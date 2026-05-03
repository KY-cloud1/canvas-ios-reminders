# canvas_assignment_api.py

'''
This module contains a class that gets upcoming assignments from
the Canvas LMS using the Canvas GraphQL API.
'''


import datetime
import json
import urllib.error
import urllib.request

from config import CANVAS_GRAPHQL_URL, CANVAS_TOKEN 


# Represents the number of weeks in the future to consider
# for assignments with due dates.
WEEKS_DELTA = 2


class CanvasApiAssignments:
    '''
    Provides methods to interact with the Canvas GraphQL API and
    retrieve assignment data for enrolled courses.
    '''
    def __init__(self, url: str, token: str) -> None:
        '''
        Initializes a CanvasApiAssignments instance with the Canvas
        GraphQL API endpoint and user authentication token.

        Args:
            url: The Canvas GraphQL API endpoint URL.
            token: A valid Canvas access token for authentication.

        Raises:
            ValueError: If either the URL or token is missing or invalid.
        '''
        # Ensure given url and token are not None.
        if not url or not token:
            raise ValueError("Missing Canvas URL and/or token.")

        self.url = url
        self._token = token


    def get_all_assignments(self) -> dict:
        '''
        Fetches all assignments from all enrolled Canvas courses using
        the GraphQL API.

        Returns:
            A dictionary containing the raw API response with courses and
            their associated assignments.

        Raises:
            ValueError: If the response is empty or contains invalid JSON.
            ConnectionError: If the API request fails or cannot connect.
        '''
        # Canvas GraphQL query for course code and assignments with
        # due dates.
        query = """
        query AllUpcomingAssignments {
            allCourses {
                courseCode
                assignmentsConnection(first: 100) {
                    nodes {
                        name
                        dueAt
                    }
                }
            }
        }
        """

        data = json.dumps({"query": query}).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
            }

        try:
            req = urllib.request.Request(self.url, 
                                         data = data, 
                                         headers = headers, 
                                         method = "POST")

            with urllib.request.urlopen(req) as response:        
                try:
                    assignment_data = json.loads(response.read().decode("utf-8"))
                
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON received from Canvas API")
                
                if not assignment_data:
                    raise ValueError("Canvas API returned empty assignment data")
                
                return assignment_data
            
        except urllib.error.HTTPError as e:
            raise ConnectionError(f"Canvas API HTTP error: {e}")
            
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to Canvas API: {e}")


    def filter_assignments_due(self, assignments: dict, 
                               weeks_delta: int) -> list[dict]:
        '''
        Filters Canvas assignments to include only those due within a
        specified time range.

        Args:
            assignments: Raw assignment data returned from the Canvas API.
            weeks_delta: Number of weeks into the future to include.

        Returns:
            A list of dictionaries containing filtered assignments with
            course name, assignment name, and due date.
        '''
        due_assignments = []

        curr_date = datetime.datetime.now(datetime.timezone.utc)

        weeks_future = curr_date + datetime.timedelta(weeks = weeks_delta)

        for course in assignments['data']['allCourses']:
            course_code_split = course['courseCode'].split()
            
            for assignment in course['assignmentsConnection']['nodes']:
                assignment_due_date = assignment.get("dueAt")

                if not assignment_due_date:
                    continue

                # Convert assignment due date from ISO 8601 string into
                # datetime.datetime object in UTC for comparison.
                due_date_dt = datetime.datetime.fromisoformat(
                    assignment_due_date.replace("Z", "+00:00"))

                if due_date_dt >= curr_date and due_date_dt <= weeks_future:
                    # Use only the first two strings in the courseCode
                    # as the course's title if the courseCode is at
                    # least two strings long. Otherwise just use the
                    # entire courseCode.
                    # 
                    # This should make the course title only the
                    # abbreviated course department and the course
                    # number (ex: MATH 1). 
                    if len(course_code_split) >= 2:
                        course_title = " ".join(course_code_split[:2])
                    else:
                        course_title = course['courseCode']

                    due_assignments.append({
                        "course": course_title,
                        "assignment": assignment['name'],
                        "dueAt": assignment_due_date
                        })

        return due_assignments


def run():
    '''
    Entry point for testing the Canvas API integration locally.
    Retrieves upcoming assignments and prints them to the console.
    '''
    canvas_api = CanvasApiAssignments(CANVAS_GRAPHQL_URL, CANVAS_TOKEN)

    assignments = canvas_api.get_all_assignments()

    sorted_assignments = canvas_api.filter_assignments_due(assignments, 
                                                           WEEKS_DELTA)

    print(sorted_assignments)


if __name__ == '__main__':
    run()
