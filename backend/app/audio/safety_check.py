"""高齢者向け安全設計チェック（STEP 10）。

音量 / 周波数 / 低音 / ダイナミクス / リズムを自動チェックし、
🟢 推奨 / 🟡 注意 / 🔴 要調整 の3段階で結果を返す。

閾値は procedural プロバイダーで生成した実サンプルの分析値を基準に調整している。
"""
from __future__ import annotations

from app.domain.models import AnalysisResult, SafetyCheckItem, SafetyReport

STATUS_ORDER = {"green": 0, "yellow": 1, "red": 2}
STATUS_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


def _status_for(value: float, yellow_at: float, red_at: float) -> str:
    if value >= red_at:
        return "red"
    if value >= yellow_at:
        return "yellow"
    return "green"


def run_safety_check(analysis: AnalysisResult) -> SafetyReport:
    items: list[SafetyCheckItem] = []

    vol_status = _status_for(analysis.max_short_term_dynamic_jump_db, yellow_at=6.0, red_at=12.0)
    if analysis.clipping_detected:
        vol_status = "red"
    items.append(
        SafetyCheckItem(
            key="volume",
            label="音量（急激な変化）",
            status=vol_status,
            message=(
                f"短時間の音量変化の最大値は約{analysis.max_short_term_dynamic_jump_db:.1f}dBです。"
                + ("クリッピング（音割れ）が検出されました。" if analysis.clipping_detected else "急激な変化は検出されませんでした。")
            ),
        )
    )

    high_status = _status_for(analysis.high_freq_energy_ratio, yellow_at=0.05, red_at=0.10)
    items.append(
        SafetyCheckItem(
            key="high_frequency",
            label="周波数（鋭い高音）",
            status=high_status,
            message=f"8kHz以上の高域エネルギー比率は約{analysis.high_freq_energy_ratio * 100:.1f}%です。",
        )
    )

    low_status = _status_for(analysis.low_freq_energy_ratio, yellow_at=0.07, red_at=0.14)
    items.append(
        SafetyCheckItem(
            key="low_frequency",
            label="低音（過度な低音）",
            status=low_status,
            message=f"80Hz以下の低域エネルギー比率は約{analysis.low_freq_energy_ratio * 100:.1f}%です。",
        )
    )

    dyn_status = _status_for(analysis.peak_dbfs, yellow_at=-3.0, red_at=-0.5)
    items.append(
        SafetyCheckItem(
            key="dynamics",
            label="ダイナミクス（音圧変化・クリッピング余裕）",
            status=dyn_status,
            message=f"ピークレベルは約{analysis.peak_dbfs:.1f}dBFSです。",
        )
    )

    rhythm_status = _status_for(analysis.rhythm_intensity, yellow_at=0.45, red_at=0.8)
    items.append(
        SafetyCheckItem(
            key="rhythm",
            label="リズム（激しさ）",
            status=rhythm_status,
            message=f"リズムの激しさ指標は約{analysis.rhythm_intensity:.2f}です。",
        )
    )

    overall = "green"
    for item in items:
        if STATUS_ORDER[item.status] > STATUS_ORDER[overall]:
            overall = item.status

    return SafetyReport(overall_status=overall, items=items)
