import sqlite3
from pathlib import Path


DB_PATH = Path("settings.db")


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

        Creates a connection to the SQLite database if one does not already
        exist. The required ``settings`` table is created automatically if it
        is not present.

        This method may be called multiple times safely. Subsequent calls have
        no effect while a connection is already open.
        """
        if cls._conn is not None:
            return

        cls._conn = sqlite3.connect(DB_PATH)
        cls._conn.row_factory = sqlite3.Row

        cls._conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

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
            The stored value associated with the key, or ``None`` if the key
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
