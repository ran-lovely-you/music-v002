"""音楽品質スコア（STEP 9 / 11）。

ルールベースで100点満点のスコアを算出する。
医学的な効果を示すものではなく、音響・コンテンツ設計上の参考値であることを
QualityScore.disclaimer に明記する。
"""
from __future__ import annotations

from app.domain.models import AnalysisResult, GenerateRequest, QualityScore, SafetyReport, ScoreBreakdown


def _clamp(x: float) -> float:
    return float(max(0.0, min(100.0, x)))


def compute_score(analysis: AnalysisResult, safety: SafetyReport, request: GenerateRequest) -> QualityScore:
    volume_stability = _clamp(100 - analysis.max_short_term_dynamic_jump_db * 6)
    if analysis.clipping_detected:
        volume_stability = _clamp(volume_stability - 35)

    tonal_balance = _clamp(100 - analysis.high_freq_energy_ratio * 260 - analysis.low_freq_energy_ratio * 180)

    rhythm_penalty = analysis.rhythm_intensity * 45
    listenability = _clamp((tonal_balance + volume_stability) / 2 - rhythm_penalty * 0.3)

    lufs = analysis.lufs_integrated
    if lufs is None:
        long_duration_suitability = 70.0
    else:
        distance = max(0.0, abs(lufs - (-18.0)) - 3.0)
        long_duration_suitability = _clamp(100 - distance * 8)
    if analysis.silence_ratio > 0.4:
        long_duration_suitability = _clamp(long_duration_suitability - (analysis.silence_ratio - 0.4) * 100)

    naturalness = _clamp(100 - abs(analysis.rhythm_intensity - 0.25) * 90 - analysis.high_freq_energy_ratio * 120)

    bpm = request.resolved_bpm()
    bpm_penalty = 0.0 if bpm <= 92 else (bpm - 92) * 3
    elderly_fit = _clamp((volume_stability + tonal_balance + long_duration_suitability) / 3 - bpm_penalty)

    if safety.overall_status == "red":
        elderly_fit = _clamp(elderly_fit - 25)
        listenability = _clamp(listenability - 15)
    elif safety.overall_status == "yellow":
        elderly_fit = _clamp(elderly_fit - 10)

    relaxation = _clamp((listenability + long_duration_suitability + naturalness) / 3)

    breakdown = ScoreBreakdown(
        relaxation=round(relaxation, 1),
        listenability=round(listenability, 1),
        volume_stability=round(volume_stability, 1),
        tonal_balance=round(tonal_balance, 1),
        long_duration_suitability=round(long_duration_suitability, 1),
        naturalness=round(naturalness, 1),
        elderly_fit=round(elderly_fit, 1),
    )
    total = _clamp(
        (
            relaxation
            + listenability
            + volume_stability
            + tonal_balance
            + long_duration_suitability
            + naturalness
            + elderly_fit
        )
        / 7
    )

    return QualityScore(total=round(total, 1), breakdown=breakdown)
