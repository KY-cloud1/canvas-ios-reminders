# server.py

"""
This module defines a FastAPI web server that exposes assignment data
as a JSON API using Uvicorn.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import ngrok
import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI

from canvas_client import CanvasApi, filter_canvas_assignments
from config import (
    CANVAS_GRAPHQL_URL,
    CANVAS_TOKEN,
    GRADESCOPE_EMAIL,
    GRADESCOPE_PASSWORD,
    NGROK_AUTHTOKEN,
    NGROK_DOMAIN,
)
from gradescope_client import GradescopeAutomation, filter_gradescope_assignments


# The port that the local server will run on.
PORT = 8081

# The number of weeks in the future to consider for assignments with
# due dates.
WEEKS_DELTA = 2

# The amount of time in between fetching refreshes.
REFRESH_INTERVAL_SECONDS = 3600


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
    await refresh_once()  # Fill cache once before continuing startup.
    task = asyncio.create_task(refresh_assignments())

    if NGROK_DOMAIN and NGROK_AUTHTOKEN:
        listener = ngrok.forward(PORT, authtoken=NGROK_AUTHTOKEN, domain=NGROK_DOMAIN)
    else:
        listener = None

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
    due_assignments = []

    # Handle assignments from Canvas if configured.
    if CANVAS_GRAPHQL_URL and CANVAS_TOKEN:
        canvas_api = CanvasApi(CANVAS_GRAPHQL_URL, CANVAS_TOKEN)
        canvas_assignments = canvas_api.get_all_assignments()
        filtered_canvas_assignments = filter_canvas_assignments(
            canvas_assignments, WEEKS_DELTA
        )

        due_assignments.extend(filtered_canvas_assignments)

    # Handle assignments from Gradescope if configured.
    if GRADESCOPE_EMAIL and GRADESCOPE_PASSWORD:
        gradescope_automation = GradescopeAutomation(
            GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD
        )

        try:
            gradescope_assignments = gradescope_automation.get_all_assignments()
            filtered_gradescope_assignments = filter_gradescope_assignments(
                gradescope_assignments, WEEKS_DELTA
            )

            due_assignments.extend(filtered_gradescope_assignments)
        finally:
            gradescope_automation.close_browser()

    return due_assignments


async def refresh_once() -> None:
    """
    Performs a single refresh of the cached assignment data.

    The function fetches the latest assignments from configured sources
    and updates the application cache. On success, it records the
    refresh timestamp and clears any previous refresh error. On
    failure, it records the error and re-raises the exception.
    """
    try:
        app.state.cached_assignments = await asyncio.to_thread(fetch_assignments)
        app.state.last_refresh = datetime.now(UTC)
        app.state.last_refresh_error = None
    except Exception as exc:
        app.state.last_refresh_error = str(exc)
        raise


async def refresh_assignments() -> None:
    """
    Continuously refreshes the cached assignment data at a fixed
    interval.

    The function runs indefinitely while the application is active,
    repeatedly calling `refresh_once()` and waiting for the configured
    interval between refreshes. Any refresh failures are logged, and
    the loop continues after the sleep interval.
    """
    while True:
        try:
            await refresh_once()
        except Exception as exc:
            print(f"Refresh failed: {exc}")

        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


@api.get("/status")
def get_status() -> dict[str, object]:
    """
    Returns the current health status of the server.

    Returns:
        dict: Information about the assignment cache and its last
            refresh.
    """
    return {
        "status": "healthy" if app.state.last_refresh_error is None else "degraded",
        "refresh_interval": REFRESH_INTERVAL_SECONDS,
        "cached_assignments": len(app.state.cached_assignments),
        "last_refresh": app.state.last_refresh,
        "last_refresh_error": app.state.last_refresh_error,
    }


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


app.include_router(api)


if __name__ == "__main__":
    uvicorn.run(
        app,
        port=PORT,
        log_level="info",
    )
