import { StepNav } from "../components/StepNav";
import { ja } from "../i18n/ja";
import type { OptionItem, ProviderOption, TempoLevel } from "../types";

interface DurationTempoPageProps {
  durationChoicesSec: number[];
  tempoLevels: OptionItem[];
  providers: ProviderOption[];
  durationSec: number;
  tempoLevel: TempoLevel;
  bpm: number | null;
  provider: string;
  onChangeDuration: (value: number) => void;
  onChangeTempo: (value: TempoLevel) => void;
  onChangeBpm: (value: number | null) => void;
  onChangeProvider: (value: string) => void;
  onBack: () => void;
  onNext: () => void;
}

function formatMinutes(sec: number): string {
  return `${sec / 60}分`;
}

export function DurationTempoPage({
  durationChoicesSec,
  tempoLevels,
  providers,
  durationSec,
  tempoLevel,
  bpm,
  provider,
  onChangeDuration,
  onChangeTempo,
  onChangeBpm,
  onChangeProvider,
  onBack,
  onNext,
}: DurationTempoPageProps) {
  return (
    <div className="card">
      <h2 className="step-heading">{ja.durationSelect.heading}</h2>
      <p className="step-lead">{ja.durationSelect.lead}</p>

      <div className="field-group">
        <label htmlFor="duration-select">{ja.durationSelect.duration}</label>
        <select
          id="duration-select"
          value={durationSec}
          onChange={(e) => onChangeDuration(Number(e.target.value))}
        >
          {durationChoicesSec.map((sec) => (
            <option key={sec} value={sec}>
              {formatMinutes(sec)}
            </option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label htmlFor="tempo-select">{ja.durationSelect.tempo}</label>
        <select id="tempo-select" value={tempoLevel} onChange={(e) => onChangeTempo(e.target.value as TempoLevel)}>
          {tempoLevels.map((t) => (
            <option key={t.key} value={t.key}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      <details>
        <summary style={{ cursor: "pointer", fontWeight: 700, marginBottom: 12 }}>
          {ja.durationSelect.advanced}
        </summary>
        <div className="field-group">
          <label htmlFor="bpm-input">{ja.durationSelect.bpm}</label>
          <input
            id="bpm-input"
            type="number"
            min={30}
            max={100}
            value={bpm ?? ""}
            placeholder="例: 65"
            onChange={(e) => onChangeBpm(e.target.value === "" ? null : Number(e.target.value))}
          />
        </div>
        <div className="field-group">
          <label htmlFor="provider-select">{ja.durationSelect.provider}</label>
          <select id="provider-select" value={provider} onChange={(e) => onChangeProvider(e.target.value)}>
            {providers.map((p) => (
              <option key={p.key} value={p.key} disabled={!p.available}>
                {p.key}
                {p.requires_api_key ? (p.available ? "（APIキー設定済み）" : "（APIキー未設定）") : "（APIキー不要）"}
              </option>
            ))}
          </select>
          <p className="step-lead" style={{ marginTop: 8, fontSize: "0.85em" }}>
            {ja.durationSelect.providerHelp}
          </p>
        </div>
      </details>

      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
