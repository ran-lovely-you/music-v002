import { useEffect, useState } from "react";
import { deleteProject, listProjects } from "../api/client";
import { ja } from "../i18n/ja";
import type { ProjectRecord } from "../types";

interface ProjectsPageProps {
  onBack: () => void;
}

export function ProjectsPage({ onBack }: ProjectsPageProps) {
  const [projects, setProjects] = useState<ProjectRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setProjects(await listProjects());
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteProject(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  return (
    <div className="card">
      <h2 className="step-heading">{ja.projects.heading}</h2>
      {error && <div className="error-box">{error}</div>}
      {!projects && <div className="spinner" role="status" aria-label={ja.common.loading} />}
      {projects && projects.length === 0 && <p className="step-lead">{ja.projects.empty}</p>}

      <div className="project-list">
        {projects?.map((p) => (
          <div className="project-card" key={p.id}>
            <div>
              <strong>{p.title}</strong>
              <br />
              <span style={{ fontSize: "0.85em", color: "var(--color-muted)" }}>
                {new Date(p.created_at).toLocaleString("ja-JP")} ／ スコア {p.score.total.toFixed(0)}
              </span>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <a className="big-button secondary" href={p.audio_path} download>
                DL
              </a>
              <button type="button" className="big-button secondary" onClick={() => handleDelete(p.id)}>
                {ja.projects.delete}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="nav-row">
        <button type="button" className="big-button secondary" onClick={onBack}>
          {ja.projects.backHome}
        </button>
      </div>
    </div>
  );
}
