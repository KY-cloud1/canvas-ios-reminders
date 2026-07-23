from dataclasses import dataclass


@dataclass
class Settings:
    """
    Represents the application's runtime configuration.

    Stores both general application settings and sensitive credentials.
    Non-sensitive values are persisted in SQLite, while secrets are
    retrieved from the operating system's keyring.
    """

    canvas_enabled: bool
    canvas_graphql_url: str
    canvas_token: str | None

    gradescope_enabled: bool
    gradescope_email: str | None
    gradescope_password: str | None

    refresh_interval: int
    weeks_delta: int

    ngrok_enabled: bool
    ngrok_domain: str
    ngrok_authtoken: str | None
