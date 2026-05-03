# canvas_assignment_api.py

'''
This module contains a class that gets upcoming assignments from
the UCI Canvas using the Canvas GraphQL API.
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
    Contains methods that fetch assignments from the Canvas 
    GraphQL API.
    '''
    def __init__(self, url: str, token: str) -> None:
        '''
        Initializes a CanvasApiAssignments object by setting the
        user's Canvas url and personal token.
        
        url represents a Canvas GraphQl API url.
        token represents a Canvas access token.

        Raises a ValueError if the given URL or token is None.
        '''
        # Ensure given url and token are not None.
        if not url or not token:
            raise ValueError("Missing Canvas URL and/or token.")

        self.url = url
        self._token = token


    def get_all_assignments(self) -> dict:
        '''
        Fetches all assignments in the current Canvas courses.
        
        Returns a dictionary containing all of the assignments with
        names, ids, and due dates.

        Raises a ValueError if the Canvas API call failed or the call
        result is invalid.
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
        
        Filters given assignments by only selecting the ones that have
        a due date on or after the current day and no later than the
        weeks delta from the current date.
        
        assignments represents the data received from the Canvas API.

        weeks_delta represents the number of weeks into the future from
        the current date.

        Returns a list of dicts containing only assignments that have
        due dates on or after the current day and no later than the
        weeks delta from the current day.
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
    Gets upcoming assignments from a user's UCI Canvas using their
    token and prints it into the console.
    '''
    canvas_api = CanvasApiAssignments(CANVAS_GRAPHQL_URL, CANVAS_TOKEN)

    assignments = canvas_api.get_all_assignments()

    sorted_assignments = canvas_api.filter_assignments_due(assignments, 
                                                           WEEKS_DELTA)

    print(sorted_assignments)


if __name__ == '__main__':
    run()
