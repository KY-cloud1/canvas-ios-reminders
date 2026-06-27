# server.py

"""
This module defines a FastAPI web server that exposes assignment data
as a JSON API using Uvicorn.
"""

import fastapi
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


# This constant represents the port that the local server will run on.
PORT = 8080


# This constant represents the number of weeks in the future to
# consider for assignments with due dates.
WEEKS_DELTA = 2


app = fastapi.FastAPI()


@app.get("/assignments")
def get_upcoming_assignments() -> list[dict]:
    """
    API endpoint that retrieves upcoming assignments from Canvas
    (required) and Gradescope (optional).

    The function fetches assignment data, filters it based on due
    dates, and returns it as JSON.

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
        gradescope_assignments = gradescope_automation.get_all_assignments()
        filtered_gradescope_assignments = filter_gradescope_assignments(
            gradescope_assignments, WEEKS_DELTA
        )

        due_assignments.extend(filtered_gradescope_assignments)

    return due_assignments


if __name__ == "__main__":
    if NGROK_DOMAIN and NGROK_AUTHTOKEN:
        listener = ngrok.forward(PORT, authtoken=NGROK_AUTHTOKEN, domain=NGROK_DOMAIN)

    uvicorn.run(
        app,
        port=PORT,
        log_level="info",
    )
