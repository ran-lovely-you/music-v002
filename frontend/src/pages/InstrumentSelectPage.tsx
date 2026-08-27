import { ChoiceGrid } from "../components/ChoiceGrid";
import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { Instrument, OptionItem } from "../types";

interface InstrumentSelectPageProps {
  instruments: OptionItem[];
  value: Instrument[];
  onChange: (value: Instrument[]) => void;
  onBack: () => void;
  onNext: () => void;
}

export function InstrumentSelectPage({ instruments, value, onChange, onBack, onNext }: InstrumentSelectPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.instrumentSelect.heading}</h2>
      <p className="step-lead">{ja.instrumentSelect.lead}</p>
      <ChoiceGrid options={instruments} selected={value} onChange={(next) => onChange(next as Instrument[])} />
      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
