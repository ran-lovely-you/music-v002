import { useEffect, useRef, useState } from "react";
import { ja } from "../i18n/ja";

interface AudioPlayerProps {
  src: string;
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ src }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [loop, setLoop] = useState(false);
  const [peaks, setPeaks] = useState<number[] | null>(null);

  useEffect(() => {
    setPeaks(null);
    let cancelled = false;

    async function loadWaveform() {
      try {
        const resp = await fetch(src);
        const arrayBuffer = await resp.arrayBuffer();
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const ctx = new AudioCtx();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        const channel = audioBuffer.getChannelData(0);
        const buckets = 240;
        const bucketSize = Math.max(1, Math.floor(channel.length / buckets));
        const nextPeaks: number[] = [];
        for (let i = 0; i < buckets; i++) {
          let max = 0;
          const start = i * bucketSize;
          const end = Math.min(channel.length, start + bucketSize);
          for (let j = start; j < end; j++) {
            const v = Math.abs(channel[j]);
            if (v > max) max = v;
          }
          nextPeaks.push(max);
        }
        if (!cancelled) setPeaks(nextPeaks);
        ctx.close();
      } catch {
        if (!cancelled) setPeaks([]);
      }
    }

    loadWaveform();
    return () => {
      cancelled = true;
    };
  }, [src]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !peaks) return;
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    const g = canvas.getContext("2d");
    if (!g) return;
    g.scale(dpr, dpr);
    g.clearRect(0, 0, width, height);

    const progressRatio = duration > 0 ? currentTime / duration : 0;
    const barWidth = width / Math.max(peaks.length, 1);
    peaks.forEach((peak, i) => {
      const barHeight = Math.max(2, peak * height);
      const x = i * barWidth;
      const y = (height - barHeight) / 2;
      g.fillStyle = i / peaks.length <= progressRatio ? "#2b6f5c" : "#c9c2b3";
      g.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
    });
  }, [peaks, currentTime, duration]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = volume;
  }, [volume]);

  const handleSeek = (clientX: number) => {
    const canvas = canvasRef.current;
    const audio = audioRef.current;
    if (!canvas || !audio || !duration) return;
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    audio.currentTime = ratio * duration;
  };

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  };

  const stop = () => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
  };

  return (
    <div className="player">
      <audio
        ref={audioRef}
        src={src}
        loop={loop}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onEnded={() => setIsPlaying(false)}
      />
      <canvas
        ref={canvasRef}
        className="waveform-canvas"
        role="slider"
        aria-label={ja.preview.heading}
        aria-valuemin={0}
        aria-valuemax={Math.round(duration)}
        aria-valuenow={Math.round(currentTime)}
        onClick={(e) => handleSeek(e.clientX)}
      />
      <div>
        {formatTime(currentTime)} / {formatTime(duration)}
      </div>
      <div className="player-controls">
        <button type="button" className="big-button" onClick={togglePlay}>
          {isPlaying ? ja.preview.pause : ja.preview.play}
        </button>
        <button type="button" className="big-button secondary" onClick={stop}>
          {ja.preview.stop}
        </button>
        <label>
          <input type="checkbox" checked={loop} onChange={(e) => setLoop(e.target.checked)} /> {ja.preview.loop}
        </label>
        <label>
          {ja.preview.volume}{" "}
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={volume}
            onChange={(e) => setVolume(Number(e.target.value))}
          />
        </label>
      </div>
    </div>
  );
}
