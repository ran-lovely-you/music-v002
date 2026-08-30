import { useEffect, useState } from "react";
import { deleteProject, listProjects, setProjectFavorite } from "../api/client";
import { ja } from "../i18n/ja";
import type { Profile, ProjectRecord } from "../types";

interface ProjectsPageProps {
  currentProfile: Profile;
  onBack: () => void;
}

export function ProjectsPage({ currentProfile, onBack }: ProjectsPageProps) {
  const [projects, setProjects] = useState<ProjectRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mineOnly, setMineOnly] = useState(true);

  const load = async (filterMine: boolean) => {
    try {
      setProjects(await listProjects(filterMine ? currentProfile.id : null));
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  useEffect(() => {
    setProjects(null);
    load(mineOnly);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mineOnly]);

  const handleDelete = async (id: string) => {
    try {
      await deleteProject(id);
      await load(mineOnly);
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  const handleToggleFavorite = async (p: ProjectRecord) => {
    try {
      const updated = await setProjectFavorite(p.id, !p.is_favorite);
      setProjects((prev) => prev?.map((item) => (item.id === updated.id ? updated : item)) ?? prev);
    } catch (e) {
      setError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  return (
    <div className="card">
      <h2 className="step-heading">{ja.projects.heading}</h2>
      <div className="nav-row" style={{ marginTop: 0, marginBottom: 12 }}>
        <button
          type="button"
          className={`big-button${mineOnly ? "" : " secondary"}`}
          onClick={() => setMineOnly(true)}
        >
          {ja.projects.filterMine}
        </button>
        <button
          type="button"
          className={`big-button${mineOnly ? " secondary" : ""}`}
          onClick={() => setMineOnly(false)}
        >
          {ja.projects.filterAll}
        </button>
      </div>
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
              {p.profile_name && (
                <div>
                  <span className="profile-badge">
                    {ja.projects.createdBy}: {p.profile_name}
                  </span>
                </div>
              )}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button
                type="button"
                className="favorite-toggle"
                onClick={() => handleToggleFavorite(p)}
                aria-pressed={p.is_favorite}
                title={p.is_favorite ? ja.projects.favoriteOn : ja.projects.favoriteOff}
              >
                {p.is_favorite ? "★" : "☆"}
              </button>
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
