"""音響処理エンジン（STEP 9）。

Normalize / Fade in・out / Gentle compression / EQ / Stereo width control /
Silence detection / Loop processing / LUFSベースの長時間再生向け自動音量調整
を実装する。すべて高齢者向け安全設計（急激な変化を避ける）を意識している。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pyloudnorm as pyln
from scipy import signal as sps


def ensure_sample_rate(audio: np.ndarray, sr: int, target_sr: int = 48000) -> tuple[np.ndarray, int]:
    """外部AIプロバイダーが異なるサンプルレートで返した場合に、48kHzへ揃える。"""
    if sr == target_sr:
        return audio, sr
    g = math.gcd(sr, target_sr)
    up = target_sr // g
    down = sr // g
    resampled = sps.resample_poly(audio, up, down, axis=-1)
    return resampled.astype(np.float32), target_sr


def normalize_peak(audio: np.ndarray, target_dbfs: float = -3.0) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak < 1e-9:
        return audio
    target_lin = 10 ** (target_dbfs / 20)
    return audio * (target_lin / peak)


def fade_in(audio: np.ndarray, sr: int, seconds: float) -> np.ndarray:
    """フェードインを適用する。呼び出し側の配列を直接書き換える(in-place)。

    process_master 内で連鎖的に呼ばれる前提のため、毎回フルサイズのコピーを
    作らないようにしている（長時間BGMでのピークメモリ削減のため）。
    """
    n = audio.shape[-1]
    fn = max(1, min(n, int(seconds * sr)))
    window = np.linspace(0.0, 1.0, fn, dtype=audio.dtype)
    audio[..., :fn] *= window
    return audio


def fade_out(audio: np.ndarray, sr: int, seconds: float) -> np.ndarray:
    """フェードアウトを適用する（in-place。理由は fade_in を参照）。"""
    n = audio.shape[-1]
    fn = max(1, min(n, int(seconds * sr)))
    window = np.linspace(1.0, 0.0, fn, dtype=audio.dtype)
    audio[..., -fn:] *= window
    return audio


def gentle_compression(
    audio: np.ndarray,
    sr: int,
    threshold_db: float = -18.0,
    ratio: float = 2.5,
    attack_ms: float = 15.0,
    release_ms: float = 300.0,
    hop_ms: float = 20.0,
) -> np.ndarray:
    """ブロック単位のエンベロープフォロワーによる、なだらかなコンプレッション。

    非常に長い音源（最大2時間）でもサンプル単位のPythonループを避けるため、
    hop_ms単位のブロックでエンベロープを追従させ、線形補間でフルサンプル数まで拡大する。
    """
    n = audio.shape[-1]
    if n == 0:
        return audio
    hop = max(1, int(sr * hop_ms / 1000))
    mono_env = np.max(np.abs(audio), axis=0)
    n_blocks = int(np.ceil(n / hop))
    block_env = np.zeros(n_blocks)
    for i in range(n_blocks):
        seg = mono_env[i * hop : (i + 1) * hop]
        block_env[i] = seg.max() if seg.size else 0.0

    block_time = hop / sr
    attack_coef = math.exp(-block_time / max(attack_ms / 1000.0, 1e-6))
    release_coef = math.exp(-block_time / max(release_ms / 1000.0, 1e-6))

    smoothed = np.empty(n_blocks)
    prev = 0.0
    for i in range(n_blocks):
        e = block_env[i]
        coef = attack_coef if e > prev else release_coef
        prev = coef * prev + (1 - coef) * e
        smoothed[i] = prev

    threshold = 10 ** (threshold_db / 20)
    gain_blocks = np.ones(n_blocks)
    over = smoothed > threshold
    safe_smoothed = np.where(smoothed > 1e-9, smoothed, 1e-9)
    gain_blocks[over] = (threshold + (smoothed[over] - threshold) / ratio) / safe_smoothed[over]

    block_centers = (np.arange(n_blocks) + 0.5) * hop
    full_idx = np.arange(n)
    gain_full = np.interp(full_idx, block_centers, gain_blocks, left=gain_blocks[0], right=gain_blocks[-1])
    audio *= gain_full  # in-place（呼び出し側のバッファを直接書き換える。理由は fade_in を参照）
    return audio


def eq_elderly_safe(
    audio: np.ndarray,
    sr: int,
    high_shelf_freq: float = 7500.0,
    high_shelf_gain_db: float = -4.0,
    low_shelf_freq: float = 65.0,
    low_shelf_gain_db: float = -3.0,
) -> np.ndarray:
    """不快な高音（鋭いシャリつき）と過度な低音の両方を穏やかに抑えるEQ。

    呼び出し側の配列を直接書き換える(in-place)。process_master の連鎖呼び出しの中で
    毎回フルサイズのコピーを作らないようにし、長時間BGMでのピークメモリを抑える。
    """
    nyq = sr / 2.0

    hp_cut = min(high_shelf_freq, nyq * 0.95) / nyq
    sos_hp = sps.butter(2, hp_cut, btype="highpass", output="sos")
    high_part = sps.sosfiltfilt(sos_hp, audio, axis=-1)
    gain_lin_high = 10 ** (high_shelf_gain_db / 20)
    high_part *= 1 - gain_lin_high
    audio -= high_part
    del high_part

    lp_cut = max(low_shelf_freq, 5.0) / nyq
    sos_lp = sps.butter(2, lp_cut, btype="lowpass", output="sos")
    low_part = sps.sosfiltfilt(sos_lp, audio, axis=-1)
    gain_lin_low = 10 ** (low_shelf_gain_db / 20)
    low_part *= 1 - gain_lin_low
    audio -= low_part
    del low_part

    return audio


def stereo_width(audio: np.ndarray, width: float = 1.05) -> np.ndarray:
    """ステレオ幅を調整する（in-place。mid/sideはモノラルの一時配列のみで完結させ、
    フルサイズのステレオ配列を新規に確保しない）。"""
    mid = (audio[0] + audio[1]) * 0.5
    side = (audio[0] - audio[1]) * (0.5 * width)
    audio[0] = mid + side
    audio[1] = mid - side
    return audio


def _longest_true_run(mask: np.ndarray) -> int:
    """boolean配列の中で連続してTrueが続く最大長を求める（完全にベクトル化）。

    120分クラスの長時間BGMではサンプル数が3億を超えるため、Pythonのforループで
    1サンプルずつ判定すると非現実的な時間がかかる。差分の符号が変わる位置だけを
    numpyで検出することでO(N)のベクトル演算のみで完結させている。
    """
    if mask.size == 0:
        return 0
    padded = np.concatenate(([False], mask, [False]))
    diff = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(diff == 1)
    ends = np.flatnonzero(diff == -1)
    if starts.size == 0:
        return 0
    return int((ends - starts).max())


def detect_silence(audio: np.ndarray, sr: int, threshold_db: float = -50.0) -> dict:
    mono = np.max(np.abs(audio), axis=0) if audio.ndim == 2 else np.abs(audio)
    threshold = 10 ** (threshold_db / 20)
    is_silent = mono < threshold
    silence_ratio = float(np.mean(is_silent)) if is_silent.size else 1.0

    longest_run = _longest_true_run(is_silent)
    longest_silence_sec = longest_run / sr if sr else 0.0

    return {
        "silence_ratio": silence_ratio,
        "longest_silence_sec": longest_silence_sec,
        "has_long_silence": longest_silence_sec > 5.0,
    }


def make_loopable(audio: np.ndarray, sr: int, crossfade_sec: float = 2.0) -> np.ndarray:
    """終端を始端へなじませ、ループ再生しても違和感が出にくいようにする。

    書き換えるのは末尾のクロスフェード区間のみのため、フルサイズのコピーは作らない
    （in-place。head側はクロスフェード長ぶんの小さなコピーのみ）。
    """
    n = audio.shape[-1]
    cf = min(int(crossfade_sec * sr), n // 4)
    if cf <= 0:
        return audio
    head = audio[..., :cf].copy()
    tail = audio[..., -cf:]
    fade_in_w = np.linspace(0.0, 1.0, cf, dtype=audio.dtype)
    fade_out_w = np.linspace(1.0, 0.0, cf, dtype=audio.dtype)
    tail *= fade_out_w
    tail += head * fade_in_w
    return audio


_LUFS_LONG_DURATION_SEC = 600.0  # これを超える長さでは測定用に間引く
_LUFS_MEASURE_SR = 12000  # 間引き後のサンプルレート


def measure_lufs(audio: np.ndarray, sr: int) -> float | None:
    """audio: [2, N] -> pyloudnorm には (N, channels) 形式で渡す。

    pyloudnorm はK-weightingフィルタ処理のために内部で信号全体ぶんの
    一時配列を確保する。120分クラスの長時間BGMをフル解像度のまま渡すと
    ピークメモリが跳ね上がるため、10分を超える音声は測定専用に12kHzへ
    間引いてから渡す（LUFSは知覚的な音量指標であり、間引きによる誤差は
    「音響設計上の参考値」としての用途では無視できるレベルに収まる）。
    実際に書き出す音声データそのものは元の解像度のまま変更しない。
    """
    try:
        duration_sec = audio.shape[-1] / sr if sr else 0.0
        measure_audio = audio
        measure_sr = sr
        if duration_sec > _LUFS_LONG_DURATION_SEC and sr > _LUFS_MEASURE_SR:
            g = math.gcd(sr, _LUFS_MEASURE_SR)
            up, down = _LUFS_MEASURE_SR // g, sr // g
            measure_audio = sps.resample_poly(audio, up, down, axis=-1).astype(np.float32)
            measure_sr = _LUFS_MEASURE_SR
        meter = pyln.Meter(measure_sr)
        loudness = meter.integrated_loudness(measure_audio.T)
        return float(loudness) if np.isfinite(loudness) else None
    except Exception:
        return None


def loudness_normalize(audio: np.ndarray, sr: int, target_lufs: float = -18.0) -> tuple[np.ndarray, float | None]:
    """長時間再生向けに、LUFSを基準として音量を自動調整する。"""
    current = measure_lufs(audio, sr)
    if current is None:
        return audio, None
    try:
        normalized = pyln.normalize.loudness(audio.T, current, target_lufs).T
    except Exception:
        return audio, current
    peak = float(np.max(np.abs(normalized))) if normalized.size else 0.0
    if peak > 0.98:
        normalized *= 0.98 / peak
    return normalized.astype(np.float32, copy=False), current


def _true_peak_limit(audio: np.ndarray, threshold: float = 0.97) -> np.ndarray:
    return np.where(
        np.abs(audio) <= threshold,
        audio,
        np.sign(audio) * (threshold + (1 - threshold) * np.tanh((np.abs(audio) - threshold) / (1 - threshold))),
    )


@dataclass
class ProcessingResult:
    audio: np.ndarray
    sr: int
    lufs_before: float | None
    lufs_after: float | None
    clipping_fixed: bool
    silence_info: dict


def process_master(
    audio: np.ndarray,
    sr: int,
    target_lufs: float = -18.0,
    fade_seconds: float = 2.5,
    make_loop_friendly: bool = True,
) -> ProcessingResult:
    """WAV/MP3書き出し前の最終マスタリングパイプライン。"""
    processed = eq_elderly_safe(audio, sr)
    processed = gentle_compression(processed, sr)
    processed = stereo_width(processed, width=1.05)
    processed = fade_in(processed, sr, fade_seconds)
    processed = fade_out(processed, sr, fade_seconds)
    if make_loop_friendly:
        processed = make_loopable(processed, sr, crossfade_sec=min(2.0, fade_seconds))

    processed, lufs_before = loudness_normalize(processed, sr, target_lufs)
    lufs_after = measure_lufs(processed, sr)

    peak = float(np.max(np.abs(processed))) if processed.size else 0.0
    clipping_fixed = False
    if peak > 0.999:
        processed = _true_peak_limit(processed)
        clipping_fixed = True

    silence_info = detect_silence(processed, sr)

    return ProcessingResult(
        audio=processed.astype(np.float32),
        sr=sr,
        lufs_before=lufs_before,
        lufs_after=lufs_after,
        clipping_fixed=clipping_fixed,
        silence_info=silence_info,
    )
