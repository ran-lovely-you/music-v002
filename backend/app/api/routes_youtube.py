"""YouTube用メタデータ生成API（STEP 12 / 14）。"""
from __future__ import annotations

from fastapi import APIRouter

from app.domain.models import GenerateRequest, YoutubeMetadata
from app.youtube.metadata import generate_youtube_metadata

router = APIRouter(prefix="/api", tags=["youtube"])


@router.post("/youtube/metadata", response_model=YoutubeMetadata)
async def youtube_metadata(req: GenerateRequest) -> YoutubeMetadata:
    return generate_youtube_metadata(req)
