from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error payload returned by exception handlers."""

    detail: str = Field(..., description="Human-readable error message.")
