# config.py

"""
This module loads user information from the .env file within the
module's directory.
"""

import os

from dotenv import load_dotenv


# Loads variables from .env into the environment.
load_dotenv()


def get_env(name: str) -> str:
    """
    Retrieves a required environment variable.

    Args:
        name (str): The name of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set or is empty.
    """
    value = os.getenv(name)

    if not value:
        raise ValueError(
            f"No {name} was provided in the .env file.\n"
            "Please review the README for instructions on how to setup the .env"
            " file before rerunning the program.\n"
        )

    return value


# Retrieve user Canvas information located in .env file.
CANVAS_GRAPHQL_URL = get_env("CANVAS_GRAPHQL_URL")
CANVAS_TOKEN = get_env("CANVAS_TOKEN")

# Retrieve user Gradescope information located in .env file.
GRADESCOPE_EMAIL = get_env("GRADESCOPE_EMAIL")
GRADESCOPE_PASSWORD = get_env("GRADESCOPE_PASSWORD")
