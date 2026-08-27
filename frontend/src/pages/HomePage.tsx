import { ja } from "../i18n/ja";

interface HomePageProps {
  onStart: () => void;
  onShowProjects: () => void;
}

export function HomePage({ onStart, onShowProjects }: HomePageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.home.heading}</h2>
      <p className="step-lead">{ja.home.lead}</p>
      <button type="button" className="big-button" onClick={onStart}>
        {ja.home.startButton}
      </button>
      <button type="button" className="big-button secondary" onClick={onShowProjects}>
        {ja.home.projectsButton}
      </button>
      <div className="disclaimer-box">{ja.home.disclaimer}</div>
    </div>
  );
}
