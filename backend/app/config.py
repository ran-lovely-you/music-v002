"""アプリケーション設定。

APIキー等の秘密情報はすべて環境変数（.env）から読み込み、
ソースコードやログには一切書き込まない。
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    default_music_provider: str = "procedural"

    elevenlabs_api_key: str | None = None
    stability_api_key: str | None = None

    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_dir: str = "./data"
    output_dir: str = "./data/outputs"
    db_path: str = "./data/projects.db"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_dir_path(self) -> Path:
        p = (BACKEND_ROOT / self.data_dir).resolve() if not Path(self.data_dir).is_absolute() else Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir_path(self) -> Path:
        p = (BACKEND_ROOT / self.output_dir).resolve() if not Path(self.output_dir).is_absolute() else Path(self.output_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path_resolved(self) -> Path:
        p = (BACKEND_ROOT / self.db_path).resolve() if not Path(self.db_path).is_absolute() else Path(self.db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def has_key(self, provider: str) -> bool:
        """APIキーの有無だけを返す。値そのものは絶対に返さない/ログしない。"""
        if provider == "elevenlabs":
            return bool(self.elevenlabs_api_key)
        if provider == "stability":
            return bool(self.stability_api_key)
        return True  # procedural はキー不要


settings = Settings()
