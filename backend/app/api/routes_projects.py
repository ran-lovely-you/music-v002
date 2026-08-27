"""プロジェクト保存・読み込みAPI（STEP 11 / 12）。"""
from __future__ import annotations

import asyncio
import datetime as dt

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.state import GENERATION_CACHE
from app.domain.models import ProjectRecord
from app.export.exporter import ExportError, export_audio
from app.storage.project_repo import delete_project, get_project, list_projects, save_project

router = APIRouter(prefix="/api", tags=["projects"])


class SaveProjectRequest(BaseModel):
    generation_id: str
    title: str


@router.post("/projects", response_model=ProjectRecord)
async def create_project(body: SaveProjectRequest) -> ProjectRecord:
    cached = GENERATION_CACHE.get(body.generation_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="生成結果が見つかりません。再度BGMを生成してから保存してください。")

    try:
        wav_path = await asyncio.to_thread(export_audio, cached.audio, cached.sr, body.generation_id, "wav")
    except ExportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    req = cached.result.request
    title = body.title.strip() or f"BGM_{body.generation_id}"
    record = ProjectRecord(
        id=body.generation_id,
        title=title,
        created_at=dt.datetime.utcnow().isoformat(),
        bgm_type=req.bgm_type,
        bpm=req.resolved_bpm(),
        instruments=req.instruments,
        nature_sounds=req.nature_sounds,
        prompts=cached.result.prompts,
        analysis=cached.result.analysis,
        safety=cached.result.safety,
        score=cached.result.score,
        audio_path=f"/outputs/{wav_path.name}",
    )
    save_project(record)
    return record


@router.get("/projects", response_model=list[ProjectRecord])
async def get_projects() -> list[ProjectRecord]:
    return list_projects()


@router.get("/projects/{project_id}", response_model=ProjectRecord)
async def get_project_by_id(project_id: str) -> ProjectRecord:
    record = get_project(project_id)
    if record is None:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")
    return record


@router.delete("/projects/{project_id}")
async def remove_project(project_id: str) -> dict:
    if not delete_project(project_id):
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません。")
    return {"deleted": True}
