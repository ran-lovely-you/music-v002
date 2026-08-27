import { ChoiceGrid } from "../components/ChoiceGrid";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { Mood, OptionItem } from "../types";

interface MoodSelectPageProps {
  moods: OptionItem[];
  value: Mood[];
  onChange: (value: Mood[]) => void;
  onBack: () => void;
  onNext: () => void;
}

export function MoodSelectPage({ moods, value, onChange, onBack, onNext }: MoodSelectPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.moodSelect.heading}</h2>
      <p className="step-lead">{ja.moodSelect.lead}</p>
      <ChoiceGrid options={moods} selected={value} onChange={(next) => onChange(next as Mood[])} />
      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
