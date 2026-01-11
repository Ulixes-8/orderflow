"""Authentication helpers for fulfillment authorization."""

from __future__ import annotations


class AuthService:
    """Simple auth service that validates a shared secret code."""

    def __init__(self, required_code: str) -> None:
        self._required_code = required_code

    def check(self, auth_code: str) -> bool:
        """Return True if the provided auth code matches the required code."""

        return auth_code == self._required_code
