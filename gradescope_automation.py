# gradescope_automation.py

"""
This module contains a class that gets upcoming assignments from
Gradescope using browser automation.
"""

import os

from config import GRADESCOPE_EMAIL, GRADESCOPE_PASSWORD
from playwright.sync_api import Playwright, sync_playwright


# Absolute path to this python module's file directory.
FILE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# File for Playwright browser context to be saved in.
FILE_PATH = os.path.join(FILE_DIRECTORY, "auth.json")


def login(playwright: Playwright):
    # Launch Chrome and create a new context.
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Go to Gradescope website.
    page.goto("https://www.gradescope.com/")

    # Login to Gradescope using user's credentials.
    page.get_by_role("button", name="Log In").click()
    page.fill("#session_email", GRADESCOPE_EMAIL)
    page.fill("#session_password", GRADESCOPE_PASSWORD)
    page.get_by_role("button", name="Log In").click()

    # Save context state.
    context.storage_state(path=FILE_PATH)

    # Close Chrome after timeout to allow time for login processing.
    page.wait_for_timeout(5000)
    browser.close()


with sync_playwright() as playwright:
    login(playwright)
