from __future__ import annotations


class AppError(Exception):
    """Base exception for application-specific errors."""


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class ValidationError(AppError):
    """Raised when input fails domain validation."""
