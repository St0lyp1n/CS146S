from __future__ import annotations

from fastapi import APIRouter

from ..database import insert_note, require_note
from ..schemas import CreateNoteRequest, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(body: CreateNoteRequest) -> NoteResponse:
    note = insert_note(body.content.strip())
    return NoteResponse(id=note.id, content=note.content, created_at=note.created_at)


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    note = require_note(note_id)
    return NoteResponse(id=note.id, content=note.content, created_at=note.created_at)
