from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CreateNoteRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Note body text.")

    @field_validator("content")
    @classmethod
    def strip_and_require_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content is required")
        return stripped


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: str
