"""Music Provider レジストリ / ファクトリ。

新しい音楽生成AIサービスを追加する場合は、MusicProvider を実装したクラスを作り
ここに登録するだけでよい（他のコードを変更する必要はない）。
"""
from __future__ import annotations

from app.config import settings
from app.music_providers.base import MusicProvider, ProviderError
from app.music_providers.elevenlabs_provider import ElevenLabsMusicProvider
from app.music_providers.procedural_provider import ProceduralMusicProvider
from app.music_providers.stability_provider import StabilityMusicProvider

_PROVIDERS: dict[str, MusicProvider] = {
    "procedural": ProceduralMusicProvider(),
    "elevenlabs": ElevenLabsMusicProvider(),
    "stability": StabilityMusicProvider(),
}


def get_provider(name: str | None) -> MusicProvider:
    key = name or settings.default_music_provider
    provider = _PROVIDERS.get(key)
    if provider is None:
        raise ProviderError(f"未対応の音楽生成プロバイダーです: {key}")
    if provider.requires_api_key and not settings.has_key(key):
        raise ProviderError(
            f"「{key}」プロバイダーのAPIキーが設定されていません。.env の該当キーを設定するか、"
            "procedural プロバイダー（APIキー不要ですぐに利用できます）をお試しください。"
        )
    return provider


def list_providers() -> list[dict]:
    return [
        {
            "key": key,
            "name": provider.name,
            "requires_api_key": provider.requires_api_key,
            "available": (not provider.requires_api_key) or settings.has_key(key),
        }
        for key, provider in _PROVIDERS.items()
    ]
