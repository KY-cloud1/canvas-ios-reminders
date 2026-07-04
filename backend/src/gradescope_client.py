# gradescope_client.py

"""
This module contains a class that gets upcoming assignments from
Gradescope using browser automation.
"""

import datetime
import os

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from config import GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD


# Absolute path to this python module's file directory.
FILE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# File for Playwright browser context to be saved in.
FILE_PATH = os.path.join(FILE_DIRECTORY, "auth.json")

# Gradescope course dashboard URL.
COURSE_DASHBOARD_URL = "https://www.gradescope.com/"

# This constant represents the number of weeks in the future to
# consider for assignments with due dates.
WEEKS_DELTA = 2

# Amount of time to wait during login validation.
LOGIN_TIMEOUT_MS = 5_000


class GradescopeAutomation:
    """
    Provides methods to log in and fetch assignments from Gradescope
    using Playwright browser automation.
    """

    def __init__(self, email: str, password: str, headless: bool = True) -> None:
        """
        Initialize a GradescopeAutomation instance with user
        credentials and browser configuration.

        Args:
            email: The Gradescope login email address.
            password: The Gradescope login password.
            headless: Whether to run the browser in headless mode.
                Defaults to True.

        Raises:
            ValueError: If email or password is missing or invalid.
        """
        # Ensure login credentials are provided.
        if not email or not password:
            raise ValueError("Missing email or password for Gradescope login.")

        self._email = email
        self._password = password
        self.headless = headless

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    def login(self) -> None:
        """
        Logs into Gradescope using an active browser session,
        verifies that the course dashboard is reached, and saves the
        authenticated browser state for later reuse.

        Raises:
            RuntimeError: If the browser session cannot be initialized
                or authentication fails.
        """
        page = self._new_page()

        try:
            # Go to Gradescope website.
            page.goto(COURSE_DASHBOARD_URL)

            # Login to Gradescope using user's credentials.
            page.get_by_role("button", name="Log In").click()
            page.fill("#session_email", self._email)
            page.fill("#session_password", self._password)
            page.get_by_role("button", name="Log In").click()

            # Verify Gradescope reached the course dashboard
            # after login.
            page.locator("a[href*='/courses/']").first.wait_for(
                timeout=LOGIN_TIMEOUT_MS
            )

            # Save context state.
            self._require_context().storage_state(path=FILE_PATH)
        except PlaywrightTimeoutError as e:
            raise RuntimeError(
                "Gradescope login failed: course dashboard not reached."
            ) from e
        finally:
            page.close()

    def get_all_assignments(self) -> list[dict]:
        """
        Scrapes upcoming assignments from all enrolled Gradescope
        courses using an active browser session.

        Returns:
            list[dict]: A list of dictionaries containing the course
                title, assignment name, and assignment due date.

        Raises:
            RuntimeError: If authentication cannot be established or no
                browser session is available.
        """
        # Ensure authentication before scraping.
        self._ensure_logged_in()

        page = self._new_page()

        try:
            # Load Gradescope course dashboard.
            page.goto(COURSE_DASHBOARD_URL, wait_until="domcontentloaded")

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
                page.goto(COURSE_DASHBOARD_URL + href, wait_until="domcontentloaded")

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

            return all_assignments

        finally:
            page.close()

    def close_browser(self) -> None:
        """
        Closes the browser context, browser, and Playwright instance.
        """
        if self._context is not None:
            self._context.close()
            self._context = None

        if self._browser is not None:
            self._browser.close()
            self._browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def _start_browser(self) -> None:
        """
        Start Playwright, browser, and context internally.
        """
        if (
            self._context is not None
            and self._browser is not None
            and self._playwright is not None
        ):
            return

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)

        if os.path.exists(FILE_PATH):
            self._context = self._browser.new_context(storage_state=FILE_PATH)
        else:
            self._context = self._browser.new_context()

    def _require_context(self) -> BrowserContext:
        """
        Ensure a Playwright browser context is initialized and return
        it, starting the browser if necessary.

        Returns:
            BrowserContext: The active browser context.

        Raises:
            RuntimeError: If the browser context cannot be initialized.
        """
        # Try starting browser if there is no context.
        if self._context is None:
            self._start_browser()

        # Check again for context in case starting browser failed.
        if self._context is None:
            raise RuntimeError("Browser context could not be initialized.")

        return self._context

    def _new_page(self) -> Page:
        """
        Create and return a new page from the active browser session.

        Returns:
            Page: A new Playwright page.

        Raises:
            RuntimeError: If no browser context has been initialized.
        """
        context = self._require_context()

        return context.new_page()

    def _ensure_logged_in(self) -> None:
        """
        Ensure that the current browser session is authenticated.

        If the existing browser session is not authenticated, performs
        a login and verifies that authentication succeeded.

        Raises:
            RuntimeError: If authentication fails after login attempt.
        """
        if not self._is_logged_in():
            self.login()

    def _is_logged_in(self) -> bool:
        """
        Checks whether the current session can access the Gradescope
        dashboard.

        Returns:
            bool: True if the Gradescope course dashboard is accessible
                using the current browser session, otherwise False.
        """
        page = self._new_page()

        try:
            page.goto(COURSE_DASHBOARD_URL, wait_until="domcontentloaded")
            page.locator("a[href*='/courses/']").first.wait_for(
                timeout=LOGIN_TIMEOUT_MS
            )
            return True
        except PlaywrightTimeoutError:
            return False
        finally:
            page.close()


def filter_gradescope_assignments(
    assignments: list[dict], weeks_delta: int
) -> list[dict]:
    """
    Filters Gradescope assignments to include only those due within
    the next `weeks_delta` weeks.

    Args:
        assignments: List of assignment dictionaries from
            GradescopeAutomation.
        weeks_delta: Number of weeks into the future to include.

    Returns:
        list[dict]: A list of dictionaries containing filtered
            assignments with a course name, assignment name, and
            due date.
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
    client = GradescopeAutomation(GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD, False)

    try:
        all_assignments = client.get_all_assignments()
        filtered_assignments = filter_gradescope_assignments(
            all_assignments, WEEKS_DELTA
        )

        print(filtered_assignments)
    finally:
        client.close_browser()


if __name__ == "__main__":
    run()
