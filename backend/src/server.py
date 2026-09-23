# server.py

"""
This module defines a FastAPI web server that exposes assignment data
as a JSON API using Uvicorn.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime

import ngrok
import uvicorn
from canvas.client import CanvasApi, filter_canvas_assignments
from config import SettingsManager
from fastapi import APIRouter, BackgroundTasks, FastAPI, Request
from gradescope.client import (
    GradescopeAutomation,
    filter_gradescope_assignments,
)
from schemas.settings import SettingsUpdate
from sse_starlette import EventSourceResponse

# The default port that the local server will run on.
PORT = 9101


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's startup and shutdown lifecycle.

    On startup, the function performs an initial assignment refresh,
    populating the cache before starting a background task that
    refreshes it periodically. On shutdown, the background task is
    cancelled and awaited before the application exits.

    Args:
        app: The FastAPI application instance.
    """
    # Startup logic
    settings = SettingsManager.get()

    await refresh_once()  # Fill cache once before continuing startup.
    task = asyncio.create_task(refresh_assignments())

    listener = None
    if settings.ngrok_enabled:
        try:
            if settings.ngrok_domain and settings.ngrok_authtoken:
                listener = ngrok.forward(
                    PORT,
                    authtoken=settings.ngrok_authtoken,
                    domain=settings.ngrok_domain,
                )

            else:
                print("ngrok is enabled but credentials are not configured.")
        except Exception as e:  # noqa: BLE001
            print(f"{e}")

    # Server is live
    yield

    # Shutdown logic
    task.cancel()

    if listener:
        ngrok.kill()

    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)
api = APIRouter(prefix="/api")

app.state.cached_assignments = []
app.state.last_refresh = None
app.state.last_refresh_error = None
app.state.sse_subscribers = set()


def fetch_assignments() -> list[dict]:
    """
    Fetches upcoming assignments from configured learning platforms.

    The function retrieves assignments from Canvas and Gradescope if
    they are configured. It filters assignments by due date and returns
    a single combined list.

    Returns:
        list[dict]: A list of dictionaries representing upcoming
            assignments.
    """
    settings = SettingsManager.get()

    due_assignments = []
    errors = []

    # Handle assignments from Canvas if enabled and configured.
    if settings.canvas_enabled:
        try:
            if settings.canvas_graphql_url and settings.canvas_token:
                canvas_api = CanvasApi(
                    settings.canvas_graphql_url, settings.canvas_token
                )
                canvas_assignments = canvas_api.get_all_assignments()
                filtered_canvas_assignments = filter_canvas_assignments(
                    canvas_assignments, settings.weeks_delta
                )

                due_assignments.extend(filtered_canvas_assignments)

            else:
                errors.append("Canvas is enabled but credentials are not configured.")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{e}")
            print(f"{e}")

    # Handle assignments from Gradescope if enabled and configured.
    if settings.gradescope_enabled:
        try:
            if settings.gradescope_email and settings.gradescope_password:
                gradescope_automation = GradescopeAutomation(
                    settings.gradescope_email, settings.gradescope_password
                )

                try:
                    gradescope_assignments = gradescope_automation.get_all_assignments()
                    filtered_gradescope_assignments = filter_gradescope_assignments(
                        gradescope_assignments, settings.weeks_delta
                    )

                    due_assignments.extend(filtered_gradescope_assignments)

                finally:
                    gradescope_automation.close_browser()
            else:
                errors.append(
                    "Gradescope is enabled but credentials are not configured."
                )
        except Exception as e:  # noqa: BLE001
            errors.append(f"{e}")
            print(f"{e}")

    app.state.last_refresh_error = "\n".join(errors) if errors else None

    return due_assignments


async def refresh_once() -> None:
    """
    Performs a single refresh of the cached assignment data.

    The function marks the server as refreshing, publishes the updated
    server status to connected SSE clients, fetches the latest
    assignments from configured sources, updates the application cache
    and last refresh time, and publishes the completed refresh status.
    """
    app.state.refreshing = True
    await publish_server_status()

    try:
        app.state.cached_assignments = await asyncio.to_thread(fetch_assignments)
        app.state.last_refresh = datetime.now(UTC)

    finally:
        app.state.refreshing = False
        await publish_server_status()


async def refresh_assignments() -> None:
    """
    Continuously refreshes the cached assignment data at a fixed
    interval.

    The function runs indefinitely while the application is active,
    repeatedly calling `refresh_once()` and waiting for the configured
    interval between refreshes.
    """
    while True:
        await refresh_once()

        settings = SettingsManager.get()
        await asyncio.sleep(settings.refresh_interval)


def get_server_status() -> dict[str, object]:
    """
    Returns the current health status of the server.

    Returns:
        dict: Information about the assignment cache and its last
            refresh.
    """
    return {
        "status": "Healthy" if app.state.last_refresh_error is None else "Degraded",
        "cached_assignments": len(app.state.cached_assignments),
        "last_refresh": app.state.last_refresh,
        "last_refresh_error": app.state.last_refresh_error,
        "refreshing": app.state.refreshing,
    }


async def publish_server_status() -> None:
    """
    Publishes the current server status to all connected SSE
    subscribers.

    The function serializes the server status and adds it to each
    subscriber's queue, replacing any older pending event.
    """
    # Create SSE event containing the current server status.
    event = {
        "event": "server_status",
        "data": json.dumps(
            get_server_status(),
            default=str,
        ),
    }

    # Send event to all connected subscribers, replacing any older
    # pending events.
    for queue in list(app.state.sse_subscribers):
        if queue.full():
            queue.get_nowait()

        queue.put_nowait(event)


@api.get("/status")
def get_status() -> dict[str, object]:
    """
    Returns the server health status as an API response.

    Returns:
        dict: The current server health status.
    """
    return get_server_status()


@api.get("/settings")
def get_settings() -> dict[str, object]:
    """
    Returns the server's current runtime settings.

    The function retrieves the active application settings and returns
    configurable values along with the enabled/configured status of
    supported integrations. Sensitive values such as passwords and
    authentication tokens are not exposed.

    Returns:
        dict: Runtime settings including refresh interval, assignment
            filtering window, and configuration information for
            Canvas, Gradescope, and ngrok.
    """
    settings = SettingsManager.get()

    return {
        "refresh_interval": settings.refresh_interval,
        "weeks_delta": settings.weeks_delta,
        "canvas": {
            "enabled": settings.canvas_enabled,
            "graphql_url": settings.canvas_graphql_url,
            "token_configured": settings.canvas_token is not None,
        },
        "gradescope": {
            "enabled": settings.gradescope_enabled,
            "email": settings.gradescope_email,
            "password_configured": settings.gradescope_password is not None,
        },
        "ngrok": {
            "enabled": settings.ngrok_enabled,
            "domain": settings.ngrok_domain,
            "authtoken_configured": settings.ngrok_authtoken is not None,
        },
    }


@api.post("/settings")
def set_settings(new_settings: SettingsUpdate) -> dict[str, str]:
    """
    Docstring
    """
    settings = SettingsManager.get()

    updated_settings = replace(settings, **new_settings.model_dump(exclude_unset=True))

    SettingsManager.save(updated_settings)

    return {"status": "ok"}


@api.get("/assignments")
def get_upcoming_assignments() -> list[dict]:
    """
    Returns the cached list of upcoming assignments.

    Returns:
        list[dict]: A list of dictionaries representing upcoming
            assignments.
    """
    return app.state.cached_assignments


@api.post("/refresh")
def manual_refresh(background_tasks: BackgroundTasks) -> dict[str, str]:
    """
    Trigger a background refresh of cached assignment data.

    Args:
        background_tasks (BackgroundTasks): FastAPI background task
            manager.

    Returns:
        dict[str, str]: Status message indicating the refresh has been
            scheduled.
    """
    background_tasks.add_task(refresh_once)

    return {"status": "refresh_started"}


@api.get("/events")
async def server_events(request: Request) -> EventSourceResponse:
    """
    Streams server status updates to connected SSE clients.

    The function creates a queue for the client, registers it as an
    active subscriber, and returns an SSE response that sends the
    current server status followed by future updates.

    Args:
        request: The incoming FastAPI request.

    Returns:
        EventSourceResponse: An SSE response that streams server status
            updates to the connected client.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    app.state.sse_subscribers.add(queue)

    async def event_generator():
        """
        Generates server status events for the connected SSE client.

        The generator immediately sends the current server status and
        then waits for new events until the client disconnects. The
        client's queue is removed from the active subscribers when the
        connection closes.
        """
        try:
            # Immediately send the current state.
            yield {
                "event": "server_status",
                "data": json.dumps(
                    get_server_status(),
                    default=str,
                ),
            }

            while True:
                if await request.is_disconnected():
                    break

                yield await queue.get()
        finally:
            app.state.sse_subscribers.discard(queue)

    return EventSourceResponse(
        event_generator(),
        ping=30,  # 30 second SSE heartbeat.
    )


app.include_router(api)


def run() -> None:
    """
    Starts the FastAPI server using Uvicorn.
    """
    uvicorn.run(
        app,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    run()
