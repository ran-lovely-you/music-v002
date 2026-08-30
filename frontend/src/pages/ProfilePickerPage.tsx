import { useState } from "react";
import { ja } from "../i18n/ja";
import type { Profile } from "../types";

interface ProfilePickerPageProps {
  profiles: Profile[];
  loading: boolean;
  error: string | null;
  onSelect: (profile: Profile) => void;
  onCreate: (name: string, emoji: string) => Promise<void>;
}

const EMOJI_CHOICES = ["👵", "👴", "👩", "👨", "👧", "👦", "🧑", "😊", "🌸", "🐻"];

export function ProfilePickerPage({ profiles, loading, error, onSelect, onCreate }: ProfilePickerPageProps) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [emoji, setEmoji] = useState(EMOJI_CHOICES[0]);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) {
      setFormError(ja.profile.nameRequired);
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await onCreate(name.trim(), emoji);
      setName("");
      setAdding(false);
    } catch (e) {
      setFormError(e instanceof Error ? e.message : ja.common.error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h2 className="step-heading">{ja.profile.heading}</h2>
      <p className="step-lead">{ja.profile.lead}</p>
      {error && <div className="error-box">{error}</div>}
      {loading && <div className="spinner" role="status" aria-label={ja.common.loading} />}

      {!loading && (
        <div className="profile-grid">
          {profiles.map((p) => (
            <button
              type="button"
              key={p.id}
              className="profile-card"
              onClick={() => onSelect(p)}
            >
              <span className="profile-emoji">{p.emoji}</span>
              <span>{p.name}</span>
            </button>
          ))}
        </div>
      )}

      {!adding && (
        <button type="button" className="big-button secondary" onClick={() => setAdding(true)} style={{ marginTop: 16 }}>
          {ja.profile.addButton}
        </button>
      )}

      {adding && (
        <div className="field-group" style={{ marginTop: 16 }}>
          {formError && <div className="error-box">{formError}</div>}
          <label htmlFor="profile-name-input">{ja.profile.nameLabel}</label>
          <input
            id="profile-name-input"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={20}
            placeholder={ja.profile.namePlaceholder}
          />
          <label style={{ marginTop: 12 }}>{ja.profile.emojiLabel}</label>
          <div className="emoji-picker">
            {EMOJI_CHOICES.map((e) => (
              <button
                type="button"
                key={e}
                className={`emoji-choice${emoji === e ? " selected" : ""}`}
                onClick={() => setEmoji(e)}
                aria-pressed={emoji === e}
              >
                {e}
              </button>
            ))}
          </div>
          <div className="nav-row">
            <button type="button" className="big-button secondary" onClick={() => setAdding(false)} disabled={submitting}>
              {ja.nav.back}
            </button>
            <button type="button" className="big-button" onClick={handleCreate} disabled={submitting}>
              {submitting ? ja.common.loading : ja.profile.createButton}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
