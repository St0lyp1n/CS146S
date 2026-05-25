from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Note:
    id: int
    content: str
    created_at: str


@dataclass(frozen=True)
class ActionItem:
    id: int
    note_id: Optional[int]
    text: str
    done: bool
    created_at: str
