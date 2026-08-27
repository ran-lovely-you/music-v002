import { ja } from "../i18n/ja";

interface GeneratingPageProps {
  error: string | null;
  onBack: () => void;
  onRetry: () => void;
}

export function GeneratingPage({ error, onBack, onRetry }: GeneratingPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.generating.heading}</h2>
      {error ? (
        <>
          <div className="error-box">{error}</div>
          <div className="nav-row">
            <button type="button" className="big-button secondary" onClick={onBack}>
              {ja.nav.back}
            </button>
            <button type="button" className="big-button" onClick={onRetry}>
              {ja.common.retry}
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="step-lead">{ja.generating.lead}</p>
          <div className="spinner" role="status" aria-label={ja.generating.heading} />
        </>
      )}
    </div>
  );
}
