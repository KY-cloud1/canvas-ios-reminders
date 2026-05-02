# canvas_assignment_api.py

'''
This module contains a class that gets upcoming assignments from
the UCI Canvas using the Canvas GraphQL API.
'''


import datetime
import json
import urllib.request


# Canvas API Access Token goes here in the quotes.
TOKEN = ""


# URL specifically for Canvas used by UCI students.
# This will need to be changed for different schools.
BASE_URL = "https://canvas.eee.uci.edu/api/graphql"


# Represents the number of weeks in the future to consider
# for assignments with due dates.
WEEKS_DELTA = 2


class CanvasApiAssignments:
    '''
    Contains methods that fetch assignments from the Canvas 
    GraphQL API.
    '''

    def __init__(self, token: str) -> None:
        '''
        Initializes a CanvasApiAssignments object by setting the
        user's personal Canvas token.
        
        token represents a Canvas access token.
        '''

        # TOKEN is currently hardcoded at top of module, leaving the
        # token parameter unused.
        self._token = TOKEN


    def get_all_assignments(self) -> dict | None:
        '''
        Fetches all assignments in the current Canvas courses.
        
        Returns a dictionary containing all of the assignments with
        names, ids, and due dates.

        Returns None if the Canvas API call failed or the call result
        is invalid.
        '''

        # Canvas GraphQL query.
        query = '''
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
        
        '''

        data = json.dumps({"query": query}).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
            }

        try:
            request = urllib.request.Request(BASE_URL, 
                                             data = data, 
                                             headers = headers, 
                                             method = "POST")

            with urllib.request.urlopen(request) as response:
                status = response.getcode()

                if status != 200:
                    print("FAILED.")
                    print('NOT 200')
                    return None
                
                try:
                    assignment_data = json.loads(response.read().decode("utf-8"))

                except json.JSONDecodeError:
                    print("FAILED.")
                    print('INVALID FORMAT RECEIVED')
                    return None
                
                if not assignment_data:
                    print("FAILED.")
                    print('ASSIGNMENT DATA DOES NOT EXIST.')
                    return None
                
                return assignment_data
            
        except Exception as e:
            print("FAILED")
            print(f"UNABLE TO CONNECT TO URL: {e}")
            return None
        

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

    # TOKEN is currently hardcoded at top of program.
    canvas_api = CanvasApiAssignments(TOKEN)

    assignments = canvas_api.get_all_assignments()

    if not assignments:
        return

    sorted_assignments = canvas_api.filter_assignments_due(assignments, 
                                                           WEEKS_DELTA)

    print(sorted_assignments)


if __name__ == '__main__':
    run()
