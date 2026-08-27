import { ChoiceGrid } from "../components/ChoiceGrid";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { NatureSound, OptionItem } from "../types";

interface NatureSelectPageProps {
  natureSounds: OptionItem[];
  value: NatureSound[];
  onChange: (value: NatureSound[]) => void;
  onBack: () => void;
  onNext: () => void;
}

export function NatureSelectPage({ natureSounds, value, onChange, onBack, onNext }: NatureSelectPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.natureSelect.heading}</h2>
      <p className="step-lead">{ja.natureSelect.lead}</p>
      <ChoiceGrid options={natureSounds} selected={value} onChange={(next) => onChange(next as NatureSound[])} />
      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
