import sqlite3
from pathlib import Path


# Filepath to the settings file.
DB_PATH = Path("settings.db")


# Default settings used upon initialization.
DEFAULT_SETTINGS = {
    "canvas_enabled": "false",
    "canvas_graphql_url": "",
    "gradescope_enabled": "false",
    "refresh_interval": "3600",
    "weeks_delta": "4",
    "ngrok_enabled": "false",
    "ngrok_domain": "",
}


class Database:
    """
    Manage access to the application's SQLite settings database.

    This class provides a simple interface for initializing the database,
    storing key-value pairs, retrieving stored values, and closing the
    database connection. The connection is managed as a singleton and shared
    across all class methods.
    """

    _conn: sqlite3.Connection | None = None

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the database connection.

        Creates a connection to the SQLite database if one is not already
        open, creates the settings table if necessary, and inserts any
        missing default settings from DEFAULT_SETTINGS.

        This method is safe to call multiple times. If the database is
        already initialized, it returns immediately. Existing settings are
        not overwritten.
        """
        if cls._conn is not None:
            return

        cls._conn = sqlite3.connect(DB_PATH)
        cls._conn.row_factory = sqlite3.Row

        cls._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

        for key, value in DEFAULT_SETTINGS.items():
            cls._conn.execute(
                """
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
                """,
                (key, value),
            )

        cls._conn.commit()

    @classmethod
    def close(cls) -> None:
        """
        Close the active database connection.

        If no connection is currently open, this method does nothing. After
        closing the connection, the internal connection reference is reset.
        """
        if cls._conn is None:
            return

        cls._conn.close()
        cls._conn = None

    @classmethod
    def set(cls, key: str, value: str) -> None:
        """
        Store or update a configuration value.

        If a setting with the specified key already exists, its value is
        replaced. Otherwise, a new setting is created.

        Args:
            key: The unique identifier for the setting.
            value: The value to associate with the key.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if cls._conn is None:
            raise RuntimeError("Database has not been initialized.")

        cls._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

        cls._conn.commit()

    @classmethod
    def get(cls, key: str) -> str | None:
        """
        Retrieve a stored configuration value.

        Args:
            key: The unique identifier for the setting.

        Returns:
            The stored value associated with the key, or None if the key
            does not exist.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if cls._conn is None:
            raise RuntimeError("Database has not been initialized.")

        row = cls._conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()

        if row is None:
            return None

        return row["value"]

    @classmethod
    def delete(cls, key: str) -> None:
        """
        Delete a stored configuration value.

        If the specified key does not exist, this method has no effect.

        Args:
            key: The unique identifier for the setting to remove.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if cls._conn is None:
            raise RuntimeError("Database has not been initialized.")

        cls._conn.execute(
            "DELETE FROM settings WHERE key = ?",
            (key,),
        )

        cls._conn.commit()

    @classmethod
    def exists(cls, key: str) -> bool:
        """
        Check whether a configuration value exists.

        Args:
            key: The unique identifier for the setting.

        Returns:
            True if the specified key exists in the database, otherwise
            False.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if cls._conn is None:
            raise RuntimeError("Database has not been initialized.")

        row = cls._conn.execute(
            "SELECT EXISTS(SELECT 1 FROM settings WHERE key = ?)",
            (key,),
        ).fetchone()

        return bool(row[0])

    @classmethod
    def get_all(cls) -> dict[str, str]:
        """
        Retrieve all stored configuration values.

        Returns:
            A dictionary mapping each setting key to its corresponding value.
            If no settings are stored, an empty dictionary is returned.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if cls._conn is None:
            raise RuntimeError("Database has not been initialized.")

        rows = cls._conn.execute(
            "SELECT key, value FROM settings",
        ).fetchall()

        return {row["key"]: row["value"] for row in rows}
