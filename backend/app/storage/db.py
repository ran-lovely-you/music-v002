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

CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# 家族プロフィール・お気に入り機能追加時の後方互換マイグレーション。
# 既存の projects.db（これらの列を持たない）でも起動時に自動で列を追加する。
_PROJECT_COLUMN_MIGRATIONS = [
    ("profile_id", "TEXT"),
    ("profile_name", "TEXT"),
    ("is_favorite", "INTEGER NOT NULL DEFAULT 0"),
]


def _migrate_projects_table(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(projects)")}
    for column, ddl_type in _PROJECT_COLUMN_MIGRATIONS:
        if column not in existing:
            conn.execute(f"ALTER TABLE projects ADD COLUMN {column} {ddl_type}")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        _migrate_projects_table(conn)
        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(settings.db_path_resolved))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
