from __future__ import annotations

from typing import Any, Optional


class ApiError(Exception):
    def __init__(self, status: int, message: str, details: Optional[Any] = None):
        super().__init__(f"API error {status}: {message}")
        self.status = status
        self.message = message
        self.details = details


class ValidationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)
