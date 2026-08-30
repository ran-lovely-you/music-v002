"""プロジェクト保存・読み込み（STEP 11 / 12）。

作成したBGMをタイトル・作成日時・BGMタイプ・BPM・楽器・自然音・AIプロンプト・
Negative Prompt・音響分析結果・評価スコアとともにSQLiteへ保存する。
"""
from __future__ import annotations

import json

from app.domain.models import (
    AnalysisResult,
    BgmType,
    Instrument,
    NatureSound,
    ProjectRecord,
    PromptSet,
    QualityScore,
    SafetyReport,
)
from app.storage.db import get_connection


def save_project(record: ProjectRecord) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO projects
                (id, title, created_at, bgm_type, bpm, instruments, nature_sounds,
                 prompts, analysis, safety, score, audio_path, profile_id, profile_name, is_favorite)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title, bgm_type=excluded.bgm_type, bpm=excluded.bpm,
                instruments=excluded.instruments, nature_sounds=excluded.nature_sounds,
                prompts=excluded.prompts, analysis=excluded.analysis, safety=excluded.safety,
                score=excluded.score, audio_path=excluded.audio_path,
                profile_id=excluded.profile_id, profile_name=excluded.profile_name,
                is_favorite=excluded.is_favorite
            """,
            (
                record.id,
                record.title,
                record.created_at,
                record.bgm_type.value,
                record.bpm,
                json.dumps([i.value for i in record.instruments], ensure_ascii=False),
                json.dumps([n.value for n in record.nature_sounds], ensure_ascii=False),
                record.prompts.model_dump_json(),
                record.analysis.model_dump_json(),
                record.safety.model_dump_json(),
                record.score.model_dump_json(),
                record.audio_path,
                record.profile_id,
                record.profile_name,
                int(record.is_favorite),
            ),
        )
        conn.commit()


def _row_to_record(row) -> ProjectRecord:
    return ProjectRecord(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        bgm_type=BgmType(row["bgm_type"]),
        bpm=row["bpm"],
        instruments=[Instrument(i) for i in json.loads(row["instruments"])],
        nature_sounds=[NatureSound(n) for n in json.loads(row["nature_sounds"])],
        prompts=PromptSet.model_validate_json(row["prompts"]),
        analysis=AnalysisResult.model_validate_json(row["analysis"]),
        safety=SafetyReport.model_validate_json(row["safety"]),
        score=QualityScore.model_validate_json(row["score"]),
        audio_path=row["audio_path"],
        profile_id=row["profile_id"],
        profile_name=row["profile_name"],
        is_favorite=bool(row["is_favorite"]),
    )


def get_project(project_id: str) -> ProjectRecord | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _row_to_record(row) if row else None


def list_projects(profile_id: str | None = None) -> list[ProjectRecord]:
    with get_connection() as conn:
        if profile_id:
            rows = conn.execute(
                "SELECT * FROM projects WHERE profile_id = ? ORDER BY created_at DESC", (profile_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [_row_to_record(row) for row in rows]


def delete_project(project_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cur.rowcount > 0


def set_favorite(project_id: str, favorite: bool) -> ProjectRecord | None:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE projects SET is_favorite = ? WHERE id = ?", (int(favorite), project_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _row_to_record(row)
