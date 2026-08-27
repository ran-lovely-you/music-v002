import { AudioPlayer } from "../components/AudioPlayer";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";

interface PreviewPageProps {
  previewUrl: string;
  onBack: () => void;
  onNext: () => void;
}

export function PreviewPage({ previewUrl, onBack, onNext }: PreviewPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.preview.heading}</h2>
      <p className="step-lead">{ja.preview.lead}</p>
      <AudioPlayer src={previewUrl} />
      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
