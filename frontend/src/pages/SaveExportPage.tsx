import { useState } from "react";
import { downloadExport, getYoutubeMetadata, saveProject } from "../api/client";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { GenerateRequest, YoutubeMetadata } from "../types";

interface SaveExportPageProps {
  generationId: string;
  defaultTitle: string;
  request: GenerateRequest;
  onBack: () => void;
  onDone: () => void;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function SaveExportPage({ generationId, defaultTitle, request, onBack, onDone }: SaveExportPageProps) {
  const [title, setTitle] = useState(defaultTitle);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [youtube, setYoutube] = useState<YoutubeMetadata | null>(null);
  const [youtubeLoading, setYoutubeLoading] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await saveProject(generationId, title || defaultTitle);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async (format: "wav" | "mp3" | "flac") => {
    setExporting(format);
    setError(null);
    try {
      const blob = await downloadExport(generationId, format);
      triggerDownload(blob, `${title || defaultTitle}.${format}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    } finally {
      setExporting(null);
    }
  };

  const handleYoutube = async () => {
    setYoutubeLoading(true);
    setError(null);
    try {
      const data = await getYoutubeMetadata(request);
      setYoutube(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    } finally {
      setYoutubeLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="step-heading">{ja.save.heading}</h2>
      <p className="step-lead">{ja.save.lead}</p>

      {error && <div className="error-box">{error}</div>}

      <div className="field-group">
        <label htmlFor="title-input">{ja.save.titleLabel}</label>
        <input id="title-input" type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>

      <button type="button" className="big-button" onClick={handleSave} disabled={saving}>
        {saving ? ja.common.loading : ja.save.saveButton}
      </button>
      {saved && <p style={{ color: "var(--color-green)", fontWeight: 700 }}>{ja.save.saved}</p>}

      <button type="button" className="big-button secondary" onClick={() => handleExport("wav")} disabled={exporting === "wav"}>
        {exporting === "wav" ? ja.common.loading : ja.save.exportWav}
      </button>
      <button type="button" className="big-button secondary" onClick={() => handleExport("mp3")} disabled={exporting === "mp3"}>
        {exporting === "mp3" ? ja.common.loading : ja.save.exportMp3}
      </button>
      <button type="button" className="big-button secondary" onClick={() => handleExport("flac")} disabled={exporting === "flac"}>
        {exporting === "flac" ? ja.common.loading : ja.save.exportFlac}
      </button>

      <h3 style={{ marginTop: 28 }}>{ja.save.youtubeHeading}</h3>
      <button type="button" className="big-button secondary" onClick={handleYoutube} disabled={youtubeLoading}>
        {youtubeLoading ? ja.common.loading : ja.save.youtubeButton}
      </button>
      {youtube && (
        <div className="prompt-box">
          <strong>タイトル案</strong>
          <ul>
            {youtube.titles.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          <strong>説明文</strong>
          <p>{youtube.description}</p>
          <strong>タグ</strong>
          <p>{youtube.tags.join(", ")}</p>
          <strong>ハッシュタグ</strong>
          <p>{youtube.hashtags.join(" ")}</p>
          <strong>サムネイル用画像プロンプト</strong>
          <p>{youtube.thumbnail_prompt}</p>
          <strong>BGM紹介文</strong>
          <p>{youtube.intro_text}</p>
        </div>
      )}

      <StepNav onBack={onBack} onNext={onDone} nextLabel={ja.nav.startOver} />
    </div>
  );
}
