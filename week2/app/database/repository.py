from __future__ import annotations

import sqlite3
from typing import Optional

from ..exceptions import NotFoundError
from .connection import db_session, ensure_data_directory_exists, get_connection
from .models import ActionItem, Note


def _row_to_note(row: sqlite3.Row) -> Note:
    return Note(id=row["id"], content=row["content"], created_at=row["created_at"])


def _row_to_action_item(row: sqlite3.Row) -> ActionItem:
    return ActionItem(
        id=row["id"],
        note_id=row["note_id"],
        text=row["text"],
        done=bool(row["done"]),
        created_at=row["created_at"],
    )


def init_db() -> None:
    ensure_data_directory_exists()
    with db_session() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (note_id) REFERENCES notes(id)
            );
            """
        )


def insert_note(content: str) -> Note:
    with db_session() as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        note_id = int(cursor.lastrowid)
    note = get_note(note_id)
    if note is None:
        raise RuntimeError(f"Failed to load note {note_id} after insert.")
    return note


def list_notes() -> list[Note]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
        return [_row_to_note(row) for row in cursor.fetchall()]


def get_note(note_id: int) -> Optional[Note]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, content, created_at FROM notes WHERE id = ?",
            (note_id,),
        )
        row = cursor.fetchone()
        return _row_to_note(row) if row else None


def require_note(note_id: int) -> Note:
    note = get_note(note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} not found.")
    return note


def insert_action_items(items: list[str], note_id: Optional[int] = None) -> list[ActionItem]:
    if not items:
        return []

    with db_session() as connection:
        cursor = connection.cursor()
        created: list[ActionItem] = []
        for item in items:
            cursor.execute(
                "INSERT INTO action_items (note_id, text) VALUES (?, ?)",
                (note_id, item),
            )
            action_item_id = int(cursor.lastrowid)
            cursor.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items WHERE id = ?",
                (action_item_id,),
            )
            row = cursor.fetchone()
            if row is not None:
                created.append(_row_to_action_item(row))
        return created


def list_action_items(note_id: Optional[int] = None) -> list[ActionItem]:
    with get_connection() as connection:
        cursor = connection.cursor()
        if note_id is None:
            cursor.execute(
                "SELECT id, note_id, text, done, created_at FROM action_items ORDER BY id DESC"
            )
        else:
            cursor.execute(
                """
                SELECT id, note_id, text, done, created_at
                FROM action_items
                WHERE note_id = ?
                ORDER BY id DESC
                """,
                (note_id,),
            )
        return [_row_to_action_item(row) for row in cursor.fetchall()]


def mark_action_item_done(action_item_id: int, done: bool) -> ActionItem:
    with db_session() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE action_items SET done = ? WHERE id = ?",
            (1 if done else 0, action_item_id),
        )
        if cursor.rowcount == 0:
            raise NotFoundError(f"Action item {action_item_id} not found.")

        cursor.execute(
            "SELECT id, note_id, text, done, created_at FROM action_items WHERE id = ?",
            (action_item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise NotFoundError(f"Action item {action_item_id} not found.")
        return _row_to_action_item(row)
