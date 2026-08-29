"""BGM生成API（STEP 5〜9 の統合: プロンプト生成 → 音楽生成 → 音響処理 → 分析 → 安全チェック → スコア）。"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

import numpy as np

from fastapi import APIRouter, HTTPException

from app.api.state import GENERATION_CACHE, CachedGeneration
from app.audio.analysis import analyze_audio
from app.audio.processing import ProcessingResult, ensure_sample_rate, process_master
from app.audio.safety_check import run_safety_check
from app.audio.scoring import compute_score
from app.domain.models import AnalysisResult, GenerateRequest, GenerationResult, QualityScore, SafetyReport
from app.export.exporter import ExportError, export_audio
from app.music_providers.base import ProviderError
from app.music_providers.registry import get_provider
from app.prompt.generator import generate_prompt_set

router = APIRouter(prefix="/api", tags=["generate"])
logger = logging.getLogger("bgm_app.generate")


@dataclass
class _PipelineOutput:
    processed: ProcessingResult
    analysis: AnalysisResult
    safety: SafetyReport
    score: QualityScore


def _run_processing_pipeline(raw_audio: np.ndarray, raw_sr: int, req: GenerateRequest) -> _PipelineOutput:
    """音響処理〜分析〜スコアリングまでのCPU律速処理。スレッドプール上で実行する想定。"""
    audio, sr = ensure_sample_rate(raw_audio, raw_sr, 48000)
    del raw_audio  # 長時間BGMでは、不要になった参照を早めに手放してピークメモリを抑える
    processed = process_master(audio, sr)
    del audio
    analysis = analyze_audio(processed.audio, processed.sr, lufs_integrated=processed.lufs_after)
    safety = run_safety_check(analysis)
    score = compute_score(analysis, safety, req)
    return _PipelineOutput(processed=processed, analysis=analysis, safety=safety, score=score)


@router.post("/bgm/generate", response_model=GenerationResult)
async def generate_bgm(req: GenerateRequest) -> GenerationResult:
    prompts = generate_prompt_set(req)
    provider = get_provider(req.provider)

    try:
        raw_audio, raw_sr = await provider.generate(req, prompts.professional, prompts.negative)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("BGM生成中にプロバイダーでエラーが発生しました (provider=%s)", provider.name)
        raise HTTPException(status_code=500, detail="BGM生成中に予期しないエラーが発生しました。しばらくしてから再度お試しください。")

    if raw_audio is None or raw_audio.size == 0:
        raise HTTPException(status_code=500, detail="音楽生成の結果が空でした。設定を変えて再度お試しください。")

    # CPU律速の音響処理・分析はスレッドに逃がし、処理中もサーバーが他のリクエストに応答できるようにする
    pipeline = await asyncio.to_thread(_run_processing_pipeline, raw_audio, raw_sr, req)
    processed = pipeline.processed

    generation_id = uuid.uuid4().hex[:12]
    try:
        # プレビュー再生は<audio>タグでの再生専用でffmpegを必要としないWAVを使う。
        # MP3変換にはffmpegの外部インストールが必要なため、それが無い環境でも
        # BGM生成自体（試聴・保存・WAV/FLAC書き出し）が失敗しないようにする。
        preview_path = await asyncio.to_thread(export_audio, processed.audio, processed.sr, generation_id, "wav")
    except ExportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    result = GenerationResult(
        generation_id=generation_id,
        request=req,
        prompts=prompts,
        preview_url=f"/outputs/{preview_path.name}",
        analysis=pipeline.analysis,
        safety=pipeline.safety,
        score=pipeline.score,
        provider_used=provider.name,
    )
    GENERATION_CACHE[generation_id] = CachedGeneration(audio=processed.audio, sr=processed.sr, result=result)
    return result


@router.get("/bgm/{generation_id}", response_model=GenerationResult)
async def get_generation(generation_id: str) -> GenerationResult:
    cached = GENERATION_CACHE.get(generation_id)
    if cached is None:
        raise HTTPException(status_code=404, detail="生成結果が見つかりません。再度BGMを生成してください。")
    return cached.result
