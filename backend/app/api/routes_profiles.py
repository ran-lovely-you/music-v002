"""家族プロフィールAPI（パスワード不要・名前と絵文字だけの簡易プロフィール）。"""
from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.models import Profile
from app.storage.profile_repo import create_profile, delete_profile, list_profiles

router = APIRouter(prefix="/api", tags=["profiles"])

DEFAULT_EMOJI = "🙂"


class CreateProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    emoji: str = DEFAULT_EMOJI


@router.get("/profiles", response_model=list[Profile])
async def get_profiles() -> list[Profile]:
    return list_profiles()


@router.post("/profiles", response_model=Profile)
async def add_profile(body: CreateProfileRequest) -> Profile:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="名前を入力してください。")
    profile = Profile(
        id=uuid.uuid4().hex[:12],
        name=name,
        emoji=body.emoji.strip() or DEFAULT_EMOJI,
        created_at=dt.datetime.utcnow().isoformat(),
    )
    create_profile(profile)
    return profile


@router.delete("/profiles/{profile_id}")
async def remove_profile(profile_id: str) -> dict:
    if not delete_profile(profile_id):
        raise HTTPException(status_code=404, detail="プロフィールが見つかりません。")
    return {"deleted": True}
