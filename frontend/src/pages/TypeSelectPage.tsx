import { ChoiceGrid } from "../components/ChoiceGrid";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { BgmType, BgmTypeOption } from "../types";

interface TypeSelectPageProps {
  bgmTypes: BgmTypeOption[];
  value: BgmType | null;
  onChange: (value: BgmType) => void;
  onBack: () => void;
  onNext: () => void;
}

export function TypeSelectPage({ bgmTypes, value, onChange, onBack, onNext }: TypeSelectPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.typeSelect.heading}</h2>
      <p className="step-lead">{ja.typeSelect.lead}</p>
      <ChoiceGrid
        multi={false}
        options={bgmTypes.map((t) => ({ key: t.key, label: t.label, description: t.description }))}
        selected={value ? [value] : []}
        onChange={(next) => next[0] && onChange(next[0] as BgmType)}
      />
      <StepNav onBack={onBack} onNext={onNext} nextDisabled={!value} />
    </div>
  );
}
