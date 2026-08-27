import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { PromptSet } from "../types";

interface PromptPreviewPageProps {
  prompts: PromptSet | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
  onGenerate: () => void;
}

export function PromptPreviewPage({ prompts, loading, error, onBack, onGenerate }: PromptPreviewPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.promptPreview.heading}</h2>
      <p className="step-lead">{ja.promptPreview.lead}</p>

      {error && <div className="error-box">{error}</div>}
      {loading && <div className="spinner" role="status" aria-label={ja.common.loading} />}

      {prompts && (
        <>
          <strong>{ja.promptPreview.short}</strong>
          <div className="prompt-box">{prompts.short}</div>
          <strong>{ja.promptPreview.detailed}</strong>
          <div className="prompt-box">{prompts.detailed}</div>
          <strong>{ja.promptPreview.professional}</strong>
          <div className="prompt-box">{prompts.professional}</div>
          <strong>{ja.promptPreview.negative}</strong>
          <div className="prompt-box">{prompts.negative}</div>
        </>
      )}

      <StepNav onBack={onBack} onNext={onGenerate} nextLabel={ja.promptPreview.generateButton} nextDisabled={!prompts} />
    </div>
  );
}
