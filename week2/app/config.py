from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    base_dir: Path
    data_dir: Path
    db_path: Path
    frontend_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        base_dir = Path(__file__).resolve().parents[1]
        data_dir = Path(os.getenv("WEEK2_DATA_DIR", str(base_dir / "data")))
        db_path = Path(os.getenv("WEEK2_DB_PATH", str(data_dir / "app.db")))
        frontend_dir = Path(os.getenv("WEEK2_FRONTEND_DIR", str(base_dir / "frontend")))
        return cls(
            base_dir=base_dir,
            data_dir=data_dir,
            db_path=db_path,
            frontend_dir=frontend_dir,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
