"""AIプロンプト自動生成API（STEP 4）。"""
from __future__ import annotations

from fastapi import APIRouter

from app.domain.models import GenerateRequest, PromptSet
from app.prompt.generator import generate_prompt_set

router = APIRouter(prefix="/api", tags=["prompt"])


@router.post("/prompt/generate", response_model=PromptSet)
async def generate_prompt(req: GenerateRequest) -> PromptSet:
    return generate_prompt_set(req)
