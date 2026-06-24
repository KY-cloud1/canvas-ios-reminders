# gradescope_client.py

"""
This module contains a class that gets upcoming assignments from
Gradescope using browser automation.
"""

import datetime
import os

from config import GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD
from playwright.sync_api import Playwright, sync_playwright


# Absolute path to this python module's file directory.
FILE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# File for Playwright browser context to be saved in.
FILE_PATH = os.path.join(FILE_DIRECTORY, "auth.json")

# Gradescope Course Dashboard URL.
COURSE_DASHBOARD_URL = "https://www.gradescope.com/"

# This constant represents the number of weeks in the future to
# consider for assignments with due dates.
WEEKS_DELTA = 2


class GradescopeAutomation:
    """
    Provides methods to login and fetch assignments from Gradescope
    using browser automation.
    """

    def __init__(self, email: str, password: str, headless: bool = True) -> None:
        """
        Initializes a GradescopeAutomation instance with user credentials
        and browser configuration for Playwright automation.

        Args:
            email: The Gradescope login email address.
            password: The Gradescope login password.
            headless: Whether to run the browser in headless mode. Defaults
                to True.

        Raises:
            ValueError: If email or password is missing or invalid.
        """
        # Ensure login credentials are are provided.
        if not email or not password:
            raise ValueError("Missing email or password.")

        self._email = email
        self._password = password
        self.headless = headless

    def login(self, playwright: Playwright) -> None:
        """
        Logs into Gradescope using stored user credentials and saves
        the authenticated browser state for later reuse.

        Args:
            playwright: A Playwright instance used to control the browser.

        Raises:
            TimeoutError: If the login page fails to load or respond.
            PlaywrightError: If browser automation actions fail.
        """
        # Launch Chrome and create a new context.
        browser = playwright.chromium.launch(headless=self.headless)
        context = browser.new_context()
        page = context.new_page()

        # Go to Gradescope website.
        page.goto("https://www.gradescope.com/")

        # Login to Gradescope using user's credentials.
        page.get_by_role("button", name="Log In").click()
        page.fill("#session_email", self._email)
        page.fill("#session_password", self._password)
        page.get_by_role("button", name="Log In").click()

        # Save context state.
        context.storage_state(path=FILE_PATH)

        # Close Chrome after timeout to allow time for login processing.
        page.wait_for_load_state("networkidle")
        browser.close()

    def get_all_assignments(self, playwright: Playwright) -> list[dict]:
        """
        Scrapes upcoming Gradescope assignments from all enrolled courses
        using a saved authenticated browser session.

        Args:
            playwright: A Playwright instance used to control the browser.

        Returns:
            A list of dictionaries, each containing:
                - course: The abbreviated course title
                - assignment: The assignment name
                - dueAt: The assignment due date as a string

        Raises:
            FileNotFoundError: If the saved authentication state file is missing.
            PlaywrightError: If page navigation or element selection fails.
            ValueError: If expected assignment data cannot be parsed.
        """
        # Launch Chrome using existing context from login.
        browser = playwright.chromium.launch(headless=self.headless)
        context = browser.new_context(storage_state=FILE_PATH)
        page = context.new_page()

        # Load Gradescope course dashboard.
        page.goto(COURSE_DASHBOARD_URL)
        page.wait_for_load_state("networkidle")

        # Get all courses found on dashboard.
        courses = page.locator("a[href*='/courses/']")
        course_data = []
        for i in range(courses.count()):
            course = courses.nth(i)

            full_course_name = course.inner_text().strip()

            # Use shortened course name if possible.
            course_name_split = full_course_name.split()
            if len(course_name_split) >= 2:
                course_title = " ".join(course_name_split[:2])
            else:
                course_title = full_course_name

            # Get the relative URL for the course page.
            href = course.get_attribute("href")

            # Store the course title and its corresponding link for
            # later navigation.
            if href:
                course_data.append((course_title, href))

        # Go through each course and fetch its assignments with
        # due dates.
        all_assignments = []
        for course_name, href in course_data:
            page.goto(COURSE_DASHBOARD_URL + href)
            page.wait_for_load_state("networkidle")

            # Locate all table rows in the assignments table body.
            rows = page.locator("#assignments-student-table tbody tr")

            # Iterate through each assignment row in the table.
            for i in range(rows.count()):
                row = rows.nth(i)

                # Assignment title.
                title = row.locator("th").inner_text().strip()

                # Due dates.
                due_dates = row.locator("time.submissionTimeChart--dueDate")

                # Skip rows with no due date.
                if due_dates.count() == 0:
                    continue

                # First due date is the actual due date.
                due_date_str = due_dates.first.get_attribute("datetime")

                # Skip row if due date parsing fails.
                if not due_date_str:
                    continue

                # Convert due_date_str to datetime object.
                due_date_dt = datetime.datetime.strptime(
                    due_date_str, "%Y-%m-%d %H:%M:%S %z"
                )

                # Convert datetime object to ISO 8601 for storage.
                due_date_iso = due_date_dt.isoformat()

                all_assignments.append(
                    {
                        "course": course_name,
                        "assignment": title,
                        "dueAt": due_date_iso,
                    }
                )

        browser.close()

        return all_assignments


def filter_gradescope_assignments(
    assignments: list[dict], weeks_delta: int
) -> list[dict]:
    """
    Filters Gradescope assignments to include only those due within
    the next `weeks_delta` weeks.

    Args:
        assignments: List of assignment dictionaries from GradescopeAutomation.
        weeks_delta: Number of weeks into the future to include.

    Returns:
        A list of dictionaries containing filtered assignments with
        a course name, assignment name, and due date.
    """
    # Load the current date and future weeks.
    curr_date = datetime.datetime.now(datetime.timezone.utc)
    weeks_future = curr_date + datetime.timedelta(weeks=weeks_delta)

    due_assignments = []

    for item in assignments:
        due_date_str = item.get("dueAt")

        # Skip if missing due date.
        if not due_date_str:
            continue

        # Convert due_date_str to datetime object for comparison.
        due_date_dt = datetime.datetime.fromisoformat(due_date_str)

        # Only include assignment if its due date is not before the
        # current date and its due date is within the amount of
        # weeks forward specified by weeks_delta.
        if curr_date <= due_date_dt <= weeks_future:
            due_assignments.append(item)

    return due_assignments


def run():
    """
    Entry point for testing the Gradescope automation locally.

    Retrieves upcoming assignments, filters them, and prints due
    assignments to the console.
    """
    with sync_playwright() as playwright:
        client = GradescopeAutomation(GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD, False)
        client.login(playwright)
        all_assignments = client.get_all_assignments(playwright)
        filtered_assignments = filter_gradescope_assignments(
            all_assignments, WEEKS_DELTA
        )
        
        print(filtered_assignments)


if __name__ == "__main__":
    run()
