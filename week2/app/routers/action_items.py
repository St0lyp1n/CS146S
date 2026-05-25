from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from ollama import ResponseError

from ..database import insert_action_items, insert_note, list_action_items, mark_action_item_done
from ..schemas import (
    ActionItemDetailResponse,
    ActionItemResponse,
    ExtractActionItemsRequest,
    ExtractActionItemsResponse,
    MarkActionItemDoneRequest,
    MarkActionItemDoneResponse,
)
from ..services.extract import extract_action_items, extract_action_items_llm

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post("/extract", response_model=ExtractActionItemsResponse)
def extract(body: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
    text = body.text.strip()
    note_id: Optional[int] = None
    if body.save_note:
        note = insert_note(text)
        note_id = note.id

    items = extract_action_items(text)
    saved = insert_action_items(items, note_id=note_id)
    return ExtractActionItemsResponse(
        note_id=note_id,
        items=[ActionItemResponse(id=item.id, text=item.text) for item in saved],
    )


@router.post("/extract-llm", response_model=ExtractActionItemsResponse)
def extract_llm(body: ExtractActionItemsRequest) -> ExtractActionItemsResponse:
    text = body.text.strip()
    note_id: Optional[int] = None
    if body.save_note:
        note = insert_note(text)
        note_id = note.id

    try:
        items = extract_action_items_llm(text)
    except ResponseError as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Ensure Ollama is running and the model is pulled.",
        ) from exc

    saved = insert_action_items(items, note_id=note_id)
    return ExtractActionItemsResponse(
        note_id=note_id,
        items=[ActionItemResponse(id=item.id, text=item.text) for item in saved],
    )


@router.get("", response_model=list[ActionItemDetailResponse])
def list_all(note_id: Optional[int] = Query(default=None)) -> list[ActionItemDetailResponse]:
    rows = list_action_items(note_id=note_id)
    return [
        ActionItemDetailResponse(
            id=row.id,
            note_id=row.note_id,
            text=row.text,
            done=row.done,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/{action_item_id}/done", response_model=MarkActionItemDoneResponse)
def mark_done(action_item_id: int, body: MarkActionItemDoneRequest) -> MarkActionItemDoneResponse:
    updated = mark_action_item_done(action_item_id, body.done)
    return MarkActionItemDoneResponse(id=updated.id, done=updated.done)
