"""音響分析エンジン（STEP 8）。

Loudness(LUFS) / Peak / RMS / クリッピング検出 / 周波数バランス /
急激な音量変化 / リズムの激しさ / 無音比率 を計測する。
"""
from __future__ import annotations

import math

import numpy as np
from scipy import signal as sps

from app.audio.processing import detect_silence, measure_lufs
from app.domain.models import AnalysisResult


def _frame_rms(mono: np.ndarray, sr: int, frame_ms: float = 50.0) -> np.ndarray:
    frame_len = max(1, int(sr * frame_ms / 1000))
    n = mono.shape[0]
    n_frames = n // frame_len
    if n_frames == 0:
        return np.array([float(np.sqrt(np.mean(mono ** 2)))]) if n > 0 else np.array([0.0])
    trimmed = mono[: n_frames * frame_len].reshape(n_frames, frame_len)
    return np.sqrt(np.mean(trimmed ** 2, axis=1))


def analyze_audio(audio: np.ndarray, sr: int) -> AnalysisResult:
    n = audio.shape[-1]
    duration_sec = n / sr if sr else 0.0
    mono = np.mean(audio, axis=0) if audio.ndim == 2 else audio

    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    peak_dbfs = 20 * math.log10(peak) if peak > 1e-9 else -120.0

    rms = float(np.sqrt(np.mean(audio ** 2))) if audio.size else 0.0
    rms_dbfs = 20 * math.log10(rms) if rms > 1e-9 else -120.0

    lufs = measure_lufs(audio, sr)

    clip_mask = np.abs(audio) >= 0.999
    clipping_sample_count = int(np.sum(clip_mask))
    clipping_detected = clipping_sample_count > 0

    nperseg = int(min(65536, max(256, n)))
    freqs, psd = sps.welch(mono, fs=sr, nperseg=nperseg)
    total_energy = float(np.sum(psd)) + 1e-12
    high_energy = float(np.sum(psd[freqs >= 8000]))
    low_energy = float(np.sum(psd[freqs <= 80]))
    high_freq_energy_ratio = high_energy / total_energy
    low_freq_energy_ratio = low_energy / total_energy

    frame_rms = _frame_rms(mono, sr, frame_ms=50.0)
    frame_db = 20 * np.log10(np.maximum(frame_rms, 1e-9))
    # フェードイン/アウトや無音区間ではdB表現上の差分が実際の聴感より過大に出るため、
    # 曲全体のピークから40dB以上低い「ほぼ無音」のフレームは急激な変化の判定から除外する。
    if frame_db.size > 1:
        audible_floor = max(float(np.max(frame_db)) - 40.0, -60.0)
        audible_mask = frame_db > audible_floor
        valid_pairs = audible_mask[1:] & audible_mask[:-1]
        diffs = np.abs(np.diff(frame_db))
        max_jump = float(diffs[valid_pairs].max()) if np.any(valid_pairs) else 0.0
    else:
        max_jump = 0.0

    flux = np.diff(frame_rms) if frame_rms.size > 1 else np.array([0.0])
    onset_flux = np.maximum(flux, 0.0)
    mean_rms = float(np.mean(frame_rms)) + 1e-9
    rhythm_intensity = float(np.mean(onset_flux) / mean_rms) if onset_flux.size else 0.0

    silence_info = detect_silence(audio, sr)

    return AnalysisResult(
        duration_sec=duration_sec,
        sample_rate=sr,
        peak_dbfs=peak_dbfs,
        rms_dbfs=rms_dbfs,
        lufs_integrated=lufs,
        clipping_detected=clipping_detected,
        clipping_sample_count=clipping_sample_count,
        high_freq_energy_ratio=high_freq_energy_ratio,
        low_freq_energy_ratio=low_freq_energy_ratio,
        max_short_term_dynamic_jump_db=max_jump,
        rhythm_intensity=rhythm_intensity,
        silence_ratio=silence_info["silence_ratio"],
    )
