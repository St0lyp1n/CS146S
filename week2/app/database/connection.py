from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ..config import get_settings


def ensure_data_directory_exists() -> None:
    get_settings().data_dir.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    ensure_data_directory_exists()
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
