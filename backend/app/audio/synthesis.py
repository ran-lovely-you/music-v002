"""ローカル手続き型音楽生成エンジン（procedural provider の中核）。

外部AI音楽生成APIのキーが無くても実際に動作するBGMを作曲・合成する。
高齢者向け安全設計（急激な音量変化を避ける／強すぎる低音を避ける／
不快な高音を避ける／激しいリズムを避ける／突然の効果音を避ける）を
シンセシス段階から意識したパラメータ設計にしている。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np
from scipy import signal as sps

from app.domain.models import GenerateRequest, Instrument, NatureSound
from app.domain.presets import get_preset

SR = 48000


# ---------------------------------------------------------------------------
# 音階・周波数ユーティリティ
# ---------------------------------------------------------------------------

SCALE_INTERVALS: dict[str, list[int]] = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
}


def midi_to_freq(midi: float) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def scale_degree_midi(root_midi: int, mode: str, degree_index: int) -> int:
    intervals = SCALE_INTERVALS.get(mode, SCALE_INTERVALS["major"])
    octave_offset, idx = divmod(degree_index, len(intervals))
    return root_midi + 12 * octave_offset + intervals[idx]


# ---------------------------------------------------------------------------
# 音色（Timbre）定義 - 加算合成パラメータ
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Timbre:
    kind: str  # "pluck" (減衰音: ピアノ/ハープ等) | "sustain" (持続音: パッド/ストリングス等)
    harmonics: list[tuple[float, float]]
    attack: float = 0.01
    release: float = 0.3
    decay: float = 1.5
    detune_voices: int = 1
    tremolo_hz: float = 0.0
    tremolo_depth: float = 0.0


TIMBRES: dict[Instrument, Timbre] = {
    Instrument.PIANO: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2, 0.35), (3, 0.15), (4, 0.07), (5, 0.03)],
        attack=0.006, decay=2.4,
    ),
    Instrument.HARP: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2, 0.28), (3, 0.12), (4, 0.05)],
        attack=0.004, decay=3.0,
    ),
    Instrument.MUSIC_BOX: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2, 0.55), (3.01, 0.28), (5.4, 0.07)],
        attack=0.003, decay=1.7,
    ),
    Instrument.ACOUSTIC_GUITAR: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2, 0.42), (3, 0.2), (4, 0.09)],
        attack=0.005, decay=1.9,
    ),
    Instrument.FLUTE: Timbre(
        kind="sustain", harmonics=[(1, 1.0), (2, 0.14), (3, 0.05)],
        attack=0.35, release=0.45, tremolo_hz=4.5, tremolo_depth=0.04,
    ),
    Instrument.CLARINET: Timbre(
        kind="sustain", harmonics=[(1, 1.0), (3, 0.45), (5, 0.2), (7, 0.08)],
        attack=0.28, release=0.4,
    ),
    Instrument.MARIMBA: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (3.98, 0.22), (9.2, 0.05)],
        attack=0.002, decay=1.1,
    ),
    Instrument.SOFT_STRINGS: Timbre(
        kind="sustain", harmonics=[(1, 1.0), (2, 0.28), (3, 0.13), (4, 0.06)],
        attack=0.65, release=0.85, detune_voices=3,
    ),
    Instrument.PAD: Timbre(
        kind="sustain", harmonics=[(1, 1.0), (2, 0.18), (0.5, 0.25)],
        attack=1.3, release=1.6, detune_voices=4,
    ),
    Instrument.BELL: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2.4, 0.35), (3.8, 0.16), (5.4, 0.06)],
        attack=0.002, decay=3.6,
    ),
    Instrument.CHIME: Timbre(
        kind="pluck", harmonics=[(1, 1.0), (2.76, 0.28), (5.4, 0.09)],
        attack=0.001, decay=3.2,
    ),
}


def _envelope(n: int, sr: int, timbre: Timbre) -> np.ndarray:
    if n <= 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    if timbre.kind == "pluck":
        attack_n = max(1, min(n, int(timbre.attack * sr)))
        decay_part = np.exp(-t / max(timbre.decay, 0.05))
        env = decay_part.copy()
        env[:attack_n] = np.linspace(0.0, 1.0, attack_n) * decay_part[:attack_n]
        return env
    # sustain: raised-cosine attack/release, avoids any abrupt onset/offset
    attack_n = max(1, min(n, int(timbre.attack * sr)))
    release_n = max(1, min(n, int(timbre.release * sr)))
    if attack_n + release_n >= n:
        return np.hanning(max(n, 2))[:n] if n > 1 else np.array([1.0])
    env = np.ones(n)
    env[:attack_n] = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, attack_n))
    env[-release_n:] = (0.5 - 0.5 * np.cos(np.linspace(0, math.pi, release_n)))[::-1]
    return env


def synth_note(freq: float, duration: float, sr: int, timbre: Timbre, velocity: float, rng: random.Random) -> np.ndarray:
    n = max(1, int(duration * sr))
    t = np.arange(n) / sr
    nyquist_guard = sr * 0.42  # 不快な高周波成分を避けるため、上限を意図的に低めに設定
    detune_voices = max(1, timbre.detune_voices)
    total = np.zeros(n)
    for v in range(detune_voices):
        detune_cents = 0.0 if detune_voices == 1 else (v - (detune_voices - 1) / 2) * 4.0
        f = freq * (2.0 ** (detune_cents / 1200.0))
        voice_sig = np.zeros(n)
        for ratio, amp in timbre.harmonics:
            partial = f * ratio
            if partial <= 0 or partial >= nyquist_guard:
                continue
            # 高次倍音ほど耳に刺さりやすいため、比率が高いほど追加で減衰させる
            softness = 1.0 / (1.0 + max(0.0, ratio - 1.0) * 0.15)
            phase = rng.uniform(0, 2 * math.pi)
            voice_sig += amp * softness * np.sin(2 * math.pi * partial * t + phase)
        total += voice_sig
    total /= detune_voices

    if timbre.tremolo_hz > 0:
        total *= 1.0 - timbre.tremolo_depth + timbre.tremolo_depth * np.sin(2 * math.pi * timbre.tremolo_hz * t)

    env = _envelope(n, sr, timbre)
    return total * env * velocity


def place_stereo(buffer: np.ndarray, mono: np.ndarray, start: int, pan: float, gain: float = 1.0) -> None:
    if mono.size == 0:
        return
    total_len = buffer.shape[1]
    if start >= total_len:
        return
    n = mono.shape[0]
    if start < 0:
        mono = mono[-start:]
        n = mono.shape[0]
        start = 0
    if start + n > total_len:
        n = total_len - start
        if n <= 0:
            return
        mono = mono[:n]
    pan = max(-1.0, min(1.0, pan))
    left_gain = gain * math.sqrt(0.5 * (1 - pan))
    right_gain = gain * math.sqrt(0.5 * (1 + pan))
    buffer[0, start:start + n] += mono * left_gain
    buffer[1, start:start + n] += mono * right_gain


# ---------------------------------------------------------------------------
# 作曲: コード進行 + パッド + アルペジオ/メロディ
# ---------------------------------------------------------------------------

PROGRESSION_DEGREES = [0, 3, 4, 0]


def compose_music_layer(req: GenerateRequest, sr: int, rng: random.Random) -> np.ndarray:
    preset = get_preset(req.bgm_type)
    instruments = req.instruments or preset.default_instruments
    duration = float(req.duration_sec)
    bpm = req.resolved_bpm()
    scale_mode = preset.scale_mode
    root_midi = 60  # C4 を中心に、耳に優しい中音域を基本とする

    n_samples = int(duration * sr)
    # float32で確保する（120分の長時間BGMではfloat64だとメモリ使用量が倍増するため）
    buf = np.zeros((2, n_samples), dtype=np.float32)

    beat_sec = 60.0 / bpm
    chord_beats = 8  # 和音の変化をゆっくりにし、落ち着いた印象にする
    chord_sec = beat_sec * chord_beats

    pad_instruments = [i for i in instruments if TIMBRES[i].kind == "sustain"]
    pluck_instruments = [i for i in instruments if TIMBRES[i].kind == "pluck"]

    used_explicit_pad = bool(pad_instruments)
    active_pads = pad_instruments or [Instrument.PAD]

    t_cursor = 0.0
    chord_i = 0
    while t_cursor < duration - 1e-6:
        chord_len = min(chord_sec, duration - t_cursor)
        start_sample = int(t_cursor * sr)
        degree = PROGRESSION_DEGREES[chord_i % len(PROGRESSION_DEGREES)]
        chord_degrees = [degree, degree + 2, degree + 4]

        pad_gain_each = (0.42 if used_explicit_pad else 0.20) / math.sqrt(len(active_pads))
        for instr in active_pads:
            timbre = TIMBRES[instr]
            for d in chord_degrees:
                midi = scale_degree_midi(root_midi - 12, scale_mode, d)
                freq = midi_to_freq(midi)
                note = synth_note(freq, chord_len, sr, timbre, pad_gain_each, rng)
                pan = rng.uniform(-0.15, 0.15)
                place_stereo(buf, note, start_sample, pan)

        if pluck_instruments:
            n_beats = max(1, int(chord_len / beat_sec))
            for bi in range(n_beats):
                if rng.random() < 0.5:  # 適度に間を作り、聴き疲れしにくい密度に保つ
                    continue
                bt = bi * beat_sec
                if bt >= chord_len:
                    continue
                instr = pluck_instruments[bi % len(pluck_instruments)]
                timbre = TIMBRES[instr]
                extra = chord_degrees[0] + 7
                d = rng.choice(chord_degrees + [extra])
                octave_bump = rng.choice([0, 0, 0, 12])
                midi = scale_degree_midi(root_midi, scale_mode, d) + octave_bump
                midi = min(midi, root_midi + 19)  # 音域上限を抑え、刺さる高音を避ける
                midi = max(midi, root_midi - 5)
                freq = midi_to_freq(midi)
                note_dur = beat_sec * rng.uniform(1.3, 2.2)
                vel = rng.uniform(0.16, 0.28) / math.sqrt(len(pluck_instruments))
                note = synth_note(freq, note_dur, sr, timbre, vel, rng)
                pan = rng.uniform(-0.4, 0.4)
                place_stereo(buf, note, start_sample + int(bt * sr), pan)

        t_cursor += chord_len
        chord_i += 1

    return buf


# ---------------------------------------------------------------------------
# 自然音レイヤー
# ---------------------------------------------------------------------------

def _white_noise(n: int, rng: random.Random) -> np.ndarray:
    seed = rng.randint(0, 2**31 - 1)
    local_rng = np.random.default_rng(seed)
    # float32で生成する（長時間BGMではfloat64だと自然音レイヤーのメモリ使用量が倍増するため）
    return local_rng.standard_normal(n).astype(np.float32)


def _bandpass_noise(n: int, sr: int, low: float, high: float, rng: random.Random) -> np.ndarray:
    noise = _white_noise(n, rng)
    nyq = sr / 2.0
    low = max(10.0, min(low, nyq - 100))
    high = max(low + 50.0, min(high, nyq - 10))
    sos = sps.butter(4, [low / nyq, high / nyq], btype="bandpass", output="sos")
    return sps.sosfiltfilt(sos, noise).astype(np.float32)


def _lowpass_noise(n: int, sr: int, cutoff: float, rng: random.Random) -> np.ndarray:
    noise = _white_noise(n, rng)
    nyq = sr / 2.0
    cutoff = max(20.0, min(cutoff, nyq - 10))
    sos = sps.butter(4, cutoff / nyq, btype="lowpass", output="sos")
    return sps.sosfiltfilt(sos, noise).astype(np.float32)


def _slow_envelope(n: int, sr: int, rate_hz: float, depth: float, base: float, rng: random.Random) -> np.ndarray:
    """低解像度の乱数列を補間して、ゆっくり揺れる音量エンベロープを作る（急な音量変化を避ける）。"""
    n_ctrl = max(2, int(n / sr * rate_hz))
    seed = rng.randint(0, 2**31 - 1)
    local_rng = np.random.default_rng(seed)
    ctrl = local_rng.uniform(base - depth, base + depth, n_ctrl)
    x_ctrl = np.linspace(0, n, n_ctrl)
    x_full = np.arange(n)
    return np.clip(np.interp(x_full, x_ctrl, ctrl), 0.0, 1.5).astype(np.float32)


def _fade_edges(sig: np.ndarray, sr: int, seconds: float = 1.5) -> np.ndarray:
    n = sig.shape[-1]
    fade_n = max(1, min(n // 2, int(seconds * sr)))
    window = np.ones(n, dtype=np.float32)
    window[:fade_n] = np.linspace(0, 1, fade_n, dtype=np.float32)
    window[-fade_n:] = np.linspace(1, 0, fade_n, dtype=np.float32)
    return sig * window


def generate_rain(n: int, sr: int, rng: random.Random) -> np.ndarray:
    base = _bandpass_noise(n, sr, 1200, 9000, rng)
    env = _slow_envelope(n, sr, rate_hz=0.15, depth=0.25, base=0.65, rng=rng)
    return base * env * 0.5


def generate_river(n: int, sr: int, rng: random.Random) -> np.ndarray:
    base = _bandpass_noise(n, sr, 400, 4500, rng)
    env = _slow_envelope(n, sr, rate_hz=0.08, depth=0.15, base=0.7, rng=rng)
    return base * env * 0.55


def generate_waves(n: int, sr: int, rng: random.Random) -> np.ndarray:
    base = _bandpass_noise(n, sr, 100, 2500, rng)
    t = np.arange(n) / sr
    swell = 0.5 + 0.5 * np.sin(2 * math.pi * 0.045 * t + rng.uniform(0, math.pi))
    return base * (0.25 + 0.55 * swell) * 0.55


def generate_wind(n: int, sr: int, rng: random.Random) -> np.ndarray:
    base = _lowpass_noise(n, sr, 900, rng)
    env = _slow_envelope(n, sr, rate_hz=0.06, depth=0.3, base=0.55, rng=rng)
    return base * env * 0.5


def generate_birds(n: int, sr: int, rng: random.Random) -> np.ndarray:
    sig = np.zeros(n, dtype=np.float32)
    duration = n / sr
    t_cursor = rng.uniform(1.0, 4.0)
    while t_cursor < duration - 0.5:
        chirp_dur = rng.uniform(0.12, 0.32)
        chirp_n = int(chirp_dur * sr)
        if chirp_n > 0:
            t = np.arange(chirp_n) / sr
            f0 = rng.uniform(2200, 3800)
            f1 = f0 + rng.uniform(-400, 800)
            freq_sweep = np.linspace(f0, f1, chirp_n)
            phase = 2 * math.pi * np.cumsum(freq_sweep) / sr
            chirp = np.sin(phase)
            env = np.hanning(chirp_n)
            start = int(t_cursor * sr)
            end = min(n, start + chirp_n)
            if end > start:
                sig[start:end] += (chirp * env)[: end - start] * rng.uniform(0.12, 0.22)
        t_cursor += rng.uniform(2.5, 7.0)
    return sig


def generate_campfire(n: int, sr: int, rng: random.Random) -> np.ndarray:
    rumble = _lowpass_noise(n, sr, 220, rng) * 0.12
    sig = rumble.copy()
    duration = n / sr
    t_cursor = rng.uniform(0.3, 1.5)
    while t_cursor < duration - 0.1:
        crackle_dur = rng.uniform(0.02, 0.06)
        crackle_n = max(1, int(crackle_dur * sr))
        start = int(t_cursor * sr)
        end = min(n, start + crackle_n)
        if end > start:
            burst = _bandpass_noise(end - start, sr, 800, 6000, rng)
            env = np.linspace(1, 0, end - start) ** 2
            sig[start:end] += burst * env * rng.uniform(0.08, 0.16)
        t_cursor += rng.uniform(0.15, 0.9)
    return sig


def generate_forest(n: int, sr: int, rng: random.Random) -> np.ndarray:
    # 複数の全長バッファを同時に保持しないよう、1つのバッファへ逐次加算する
    # （長時間BGMではここが特にメモリを消費しやすいため）
    sig = generate_wind(n, sr, rng)
    sig *= 0.6
    sig += generate_birds(n, sr, rng)
    leaves = _bandpass_noise(n, sr, 2500, 8000, rng)
    leaves *= _slow_envelope(n, sr, 0.2, 0.15, 0.25, rng)
    leaves *= 0.15
    sig += leaves
    return sig


NATURE_GENERATORS = {
    NatureSound.RAIN: generate_rain,
    NatureSound.RIVER: generate_river,
    NatureSound.WAVES: generate_waves,
    NatureSound.WIND: generate_wind,
    NatureSound.BIRDS: generate_birds,
    NatureSound.CAMPFIRE: generate_campfire,
    NatureSound.FOREST: generate_forest,
}


def add_nature_layer_into(
    buf: np.ndarray, nature_sounds: list[NatureSound], sr: int, rng: random.Random, gain: float = 1.0
) -> None:
    """自然音を別バッファに作ってから合成するのではなく、既存のバッファへ直接加算する。

    120分等の長時間BGMでは、全長ぶんの一時配列を何枚も同時に保持すると
    メモリを大量に消費するため、共有バッファへの逐次加算でピークメモリを抑える。
    """
    if not nature_sounds:
        return
    n_samples = buf.shape[1]
    gain_each = gain / math.sqrt(len(nature_sounds))
    for ns in nature_sounds:
        gen = NATURE_GENERATORS.get(ns)
        if gen is None:
            continue
        mono = _fade_edges(gen(n_samples, sr, rng), sr)
        # わずかな左右差をつけて自然な広がりを持たせる（自然音は完全モノラルにしない）
        delay = int(sr * rng.uniform(0.0, 0.02))
        right = np.roll(mono, delay) if delay > 0 else mono
        buf[0] += mono * gain_each
        buf[1] += right * gain_each


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def _soft_limit(x: np.ndarray, threshold: float = 0.85) -> np.ndarray:
    """急激なクリッピングを避けるソフトリミッター（tanhベース）。"""
    return np.where(
        np.abs(x) <= threshold,
        x,
        np.sign(x) * (threshold + (1 - threshold) * np.tanh((np.abs(x) - threshold) / (1 - threshold))),
    )


def generate_raw_bgm(req: GenerateRequest, seed: int | None = None) -> tuple[np.ndarray, int]:
    """procedural provider の中核。GenerateRequest から実際のBGM波形を合成する。

    戻り値: (stereo_audio[2, N] float32, sample_rate)
    """
    rng = random.Random(seed if seed is not None else 42)
    sr = SR
    preset = get_preset(req.bgm_type)
    nature_sounds = req.nature_sounds or preset.default_nature_sounds

    # 音楽レイヤーのバッファをそのまま最終ミックスバッファとして使い回す
    # （別バッファに自然音を作って後から合成すると、長時間BGMでピークメモリが倍増するため）
    mix = compose_music_layer(req, sr, rng)
    mix *= 0.85
    add_nature_layer_into(mix, nature_sounds, sr, rng, gain=0.9)

    mix = _fade_edges(mix, sr, seconds=min(3.0, req.duration_sec / 8))
    mix = _soft_limit(mix, threshold=0.85)

    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    if peak > 1e-9:
        mix *= 0.8 / peak  # -1.9dBFS 程度の余裕を残して後段の音響処理に渡す

    return mix.astype(np.float32, copy=False), sr
