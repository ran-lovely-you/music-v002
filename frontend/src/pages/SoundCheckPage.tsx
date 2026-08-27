import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { QualityScore, SafetyReport } from "../types";

interface SoundCheckPageProps {
  safety: SafetyReport;
  score: QualityScore;
  onBack: () => void;
  onNext: () => void;
}

const SCORE_LABELS: Record<keyof QualityScore["breakdown"], string> = {
  relaxation: "リラックス度",
  listenability: "聴きやすさ",
  volume_stability: "音量安定性",
  tonal_balance: "音響バランス",
  long_duration_suitability: "長時間再生適性",
  naturalness: "自然さ",
  elderly_fit: "高齢者向け適合度",
};

export function SoundCheckPage({ safety, score, onBack, onNext }: SoundCheckPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.soundCheck.heading}</h2>
      <p className="step-lead">{ja.soundCheck.lead}</p>

      <h3>{ja.soundCheck.overall}</h3>
      <div className={`overall-banner ${safety.overall_status}`}>{ja.safetyStatusLabel[safety.overall_status]}</div>

      <ul className="safety-list">
        {safety.items.map((item) => (
          <li key={item.key} className="safety-item">
            <span>
              <strong>{item.label}</strong>
              <br />
              <span style={{ fontSize: "0.85em" }}>{item.message}</span>
            </span>
            <span className={`safety-status ${item.status}`}>{ja.safetyStatusLabel[item.status]}</span>
          </li>
        ))}
      </ul>

      <h3 style={{ marginTop: 28 }}>{ja.soundCheck.score}</h3>
      <div className="score-total">
        {score.total.toFixed(1)}
        <span style={{ fontSize: "0.4em" }}>{ja.soundCheck.scoreOutOf}</span>
      </div>
      {(Object.keys(SCORE_LABELS) as (keyof QualityScore["breakdown"])[]).map((key) => (
        <div className="score-bar-row" key={key}>
          <span className="score-bar-label">{SCORE_LABELS[key]}</span>
          <div className="score-bar-track">
            <div className="score-bar-fill" style={{ width: `${score.breakdown[key]}%` }} />
          </div>
          <span>{score.breakdown[key].toFixed(0)}</span>
        </div>
      ))}
      <div className="disclaimer-box">{score.disclaimer}</div>

      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
