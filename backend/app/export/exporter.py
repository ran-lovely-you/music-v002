"""音声ファイル出力（STEP 10 / 13）。

WAV(24bit/48kHz) / MP3(320kbps) / FLAC に対応する。
"""
from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import settings


class ExportError(Exception):
    pass


def _clip_for_write(audio: np.ndarray) -> np.ndarray:
    return np.clip(audio, -1.0, 1.0)


def export_wav(audio: np.ndarray, sr: int, generation_id: str) -> Path:
    out_path = settings.output_dir_path / f"{generation_id}.wav"
    sf.write(str(out_path), _clip_for_write(audio).T, sr, subtype="PCM_24")
    return out_path


def export_flac(audio: np.ndarray, sr: int, generation_id: str) -> Path:
    out_path = settings.output_dir_path / f"{generation_id}.flac"
    sf.write(str(out_path), _clip_for_write(audio).T, sr, subtype="PCM_24")
    return out_path


def export_mp3(audio: np.ndarray, sr: int, generation_id: str, bitrate: str = "320k") -> Path:
    if shutil.which("ffmpeg") is None:
        raise ExportError("ffmpeg が見つかりません。README のセットアップ手順に従ってインストールしてください。")

    tmp_wav = settings.output_dir_path / f"_tmp_{uuid.uuid4().hex}.wav"
    out_path = settings.output_dir_path / f"{generation_id}.mp3"
    sf.write(str(tmp_wav), _clip_for_write(audio).T, sr, subtype="PCM_24")
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(tmp_wav),
                "-codec:a", "libmp3lame", "-b:a", bitrate, "-ar", "48000",
                str(out_path),
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if result.returncode != 0:
            raise ExportError("MP3への変換に失敗しました。ffmpegの実行結果をご確認ください。")
    finally:
        tmp_wav.unlink(missing_ok=True)
    return out_path


EXPORTERS = {
    "wav": export_wav,
    "mp3": export_mp3,
    "flac": export_flac,
}


def export_audio(audio: np.ndarray, sr: int, generation_id: str, fmt: str) -> Path:
    exporter = EXPORTERS.get(fmt)
    if exporter is None:
        raise ExportError(f"未対応の出力形式です: {fmt}")
    return exporter(audio, sr, generation_id)
