# server.py

'''
This module contains a FastAPI application that uses Uvicorn (ASGI)
to send JSON data.
'''


import fastapi
import uvicorn

from canvas_assignment_api import CanvasApiAssignments
from config import CANVAS_GRAPHQL_URL, CANVAS_TOKEN 


# This constant represents the port that the local server will run on.
PORT = 8080


# This constant represents the number of weeks in the future to 
# consider for assignments with due dates.
WEEKS_DELTA = 2


app = fastapi.FastAPI()


@app.get('/assignments')
def get_upcoming_assignments():
    '''
    Gets assignments from Canvas, filters into upcoming, and returns
    the assignments as a list of dictionaries.
    '''
    canvas_api = CanvasApiAssignments(CANVAS_GRAPHQL_URL, CANVAS_TOKEN)

    assignments = canvas_api.get_all_assignments()

    if not assignments:
        return

    filtered_assignments = canvas_api.filter_assignments_due(assignments,
                                                             WEEKS_DELTA)

    return filtered_assignments


if __name__ == '__main__':
    uvicorn.run("server:app", port = PORT, log_level = "info",)
