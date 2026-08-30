"""家族プロフィールの保存・読み込み（家族での利用サポート）。"""
from __future__ import annotations

from app.domain.models import Profile
from app.storage.db import get_connection


def create_profile(profile: Profile) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO profiles (id, name, emoji, created_at) VALUES (?, ?, ?, ?)",
            (profile.id, profile.name, profile.emoji, profile.created_at),
        )
        conn.commit()


def list_profiles() -> list[Profile]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM profiles ORDER BY created_at ASC").fetchall()
        return [Profile(id=row["id"], name=row["name"], emoji=row["emoji"], created_at=row["created_at"]) for row in rows]


def get_profile(profile_id: str) -> Profile | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        return Profile(id=row["id"], name=row["name"], emoji=row["emoji"], created_at=row["created_at"]) if row else None


def delete_profile(profile_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return cur.rowcount > 0
