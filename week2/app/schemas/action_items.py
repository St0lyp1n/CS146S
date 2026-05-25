from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExtractActionItemsRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Free-form notes to extract tasks from.")
    save_note: bool = Field(default=False, description="Persist the input text as a note.")

    @field_validator("text")
    @classmethod
    def strip_and_require_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text is required")
        return stripped


class ActionItemResponse(BaseModel):
    id: int
    text: str


class ExtractActionItemsResponse(BaseModel):
    note_id: Optional[int] = None
    items: list[ActionItemResponse]


class ActionItemDetailResponse(BaseModel):
    id: int
    note_id: Optional[int]
    text: str
    done: bool
    created_at: str


class MarkActionItemDoneRequest(BaseModel):
    done: bool = Field(default=True, description="Whether the action item is completed.")


class MarkActionItemDoneResponse(BaseModel):
    id: int
    done: bool
