"""FastAPI アプリケーションのエントリポイント。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import routes_export, routes_generate, routes_presets, routes_projects, routes_prompt, routes_youtube
from app.config import settings
from app.music_providers.base import ProviderError
from app.storage.db import init_db

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("bgm_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("BGM生成AIサーバーを起動しました（デフォルトプロバイダー: %s）", settings.default_music_provider)
    yield


app = FastAPI(
    title="認知機能サポートBGM AI",
    description="高齢者向け認知機能サポートBGM制作AIソフトウェア バックエンドAPI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    # APIキーの値そのものは例外メッセージに含めない設計になっている
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.mount("/outputs", StaticFiles(directory=str(settings.output_dir_path)), name="outputs")

app.include_router(routes_presets.router)
app.include_router(routes_prompt.router)
app.include_router(routes_generate.router)
app.include_router(routes_export.router)
app.include_router(routes_projects.router)
app.include_router(routes_youtube.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
