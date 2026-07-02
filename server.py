# server.py

"""
This module defines a FastAPI web server that exposes assignment data
as a JSON API using Uvicorn.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
import ngrok
import uvicorn

from canvas_client import CanvasApi, filter_canvas_assignments
from config import (
    CANVAS_GRAPHQL_URL,
    CANVAS_TOKEN,
    GRADESCOPE_EMAIL,
    GRADESCOPE_PASSWORD,
    NGROK_DOMAIN,
    NGROK_AUTHTOKEN,
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

    On startup, the function populates the assignment cache and starts
    a background task that refreshes it periodically. On shutdown, the
    background task is cancelled and awaited before the application
    exits.

    Args:
        app: The FastAPI application instance.
    """
    # Startup logic
    app.state.cached_assignments = await asyncio.to_thread(fetch_assignments)
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


def fetch_assignments() -> list[dict]:
    """
    Fetches upcoming assignments from supported learning platforms.

    The function retrieves assignments from Canvas and, if configured,
    Gradescope. It filters assignments by due date and returns a single
    combined list.

    Returns:
        list[dict]: A list of dictionaries representing upcoming
            assignments.
    """
    due_assignments = []

    # Handle assignments from Canvas LMS.
    canvas_api = CanvasApi(CANVAS_GRAPHQL_URL, CANVAS_TOKEN)
    canvas_assignments = canvas_api.get_all_assignments()
    filtered_canvas_assignments = filter_canvas_assignments(
        canvas_assignments, WEEKS_DELTA
    )

    due_assignments.extend(filtered_canvas_assignments)

    # Handle assignments from Gradescope if login information is
    # provided, otherwise skip Gradescope fetching.
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


async def refresh_assignments() -> None:
    """
    Refreshes the cached assignment data at regular intervals.

    The function runs continuously while the application is running,
    updating the cached assignments after each refresh interval. If a
    refresh fails, the error is logged and the task continues running.
    """
    while True:
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)

        try:
            app.state.cached_assignments = await asyncio.to_thread(fetch_assignments)
        except Exception as exc:
            print(f"Refresh failed: {exc}")


@api.get("/assignments")
def get_upcoming_assignments() -> list[dict]:
    """
    Returns the cached list of upcoming assignments.

    Returns:
        list[dict]: A list of dictionaries representing upcoming
            assignments.
    """
    return app.state.cached_assignments


app.include_router(api)


if __name__ == "__main__":
    uvicorn.run(
        app,
        port=PORT,
        log_level="info",
    )
