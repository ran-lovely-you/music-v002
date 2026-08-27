"""SQLite接続とスキーマ初期化（STEP 12）。"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    bgm_type TEXT NOT NULL,
    bpm INTEGER NOT NULL,
    instruments TEXT NOT NULL,
    nature_sounds TEXT NOT NULL,
    prompts TEXT NOT NULL,
    analysis TEXT NOT NULL,
    safety TEXT NOT NULL,
    score TEXT NOT NULL,
    audio_path TEXT NOT NULL
);
"""


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(settings.db_path_resolved))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
