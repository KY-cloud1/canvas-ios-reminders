"""
Provides secure storage for application secrets.

This module defines the SecretStore class, which wraps the system
keyring to securely store, retrieve, and delete sensitive application
credentials.
"""

import keyring
from keyring.errors import PasswordDeleteError


class SecretStore:
    """
    Provide a simple interface for securely storing application secrets.

    This class wraps the `keyring` library to store, retrieve, and delete
    secrets associated with the application. All secrets are stored under
    the application's service name, allowing the operating system's native
    credential manager to securely manage sensitive values.
    """

    APP = "AssignmentBridge"

    @staticmethod
    def set(name: str, value: str) -> None:
        """
        Store a secret value in the system keyring.

        If a secret with the specified name already exists, its value is
        overwritten.

        Args:
            name: The unique identifier for the secret.
            value: The secret value to store.
        """
        keyring.set_password(SecretStore.APP, name, value)

    @staticmethod
    def get(name: str) -> str | None:
        """
        Retrieve a secret value from the system keyring.

        Args:
            name: The unique identifier for the secret.

        Returns:
            The stored secret value if it exists; otherwise, ``None``.
        """
        return keyring.get_password(SecretStore.APP, name)

    @staticmethod
    def delete(name: str) -> None:
        """
        Remove a secret value from the system keyring.

        If no secret exists for the specified name, the operation completes
        silently without raising an exception.

        Args:
            name: The unique identifier for the secret to remove.
        """
        try:
            keyring.delete_password(SecretStore.APP, name)
        except PasswordDeleteError:
            pass
