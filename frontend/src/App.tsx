import { useEffect, useState } from "react";
import { generateBgm, generatePrompt, getOptions } from "./api/client";
import { DurationTempoPage } from "./pages/DurationTempoPage";
import { GeneratingPage } from "./pages/GeneratingPage";
import { HomePage } from "./pages/HomePage";
import { InstrumentSelectPage } from "./pages/InstrumentSelectPage";
import { MoodSelectPage } from "./pages/MoodSelectPage";
import { NatureSelectPage } from "./pages/NatureSelectPage";
import { PreviewPage } from "./pages/PreviewPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { PromptPreviewPage } from "./pages/PromptPreviewPage";
import { SaveExportPage } from "./pages/SaveExportPage";
import { SoundCheckPage } from "./pages/SoundCheckPage";
import { TypeSelectPage } from "./pages/TypeSelectPage";
import { ja } from "./i18n/ja";
import type {
  BgmType,
  GenerateRequest,
  GenerationResult,
  Instrument,
  Mood,
  NatureSound,
  OptionsResponse,
  PromptSet,
  TempoLevel,
} from "./types";

type Step =
  | "home"
  | "type"
  | "mood"
  | "instrument"
  | "nature"
  | "duration"
  | "prompt"
  | "generating"
  | "soundcheck"
  | "preview"
  | "save"
  | "projects";

const INITIAL_DURATION_SEC = 300;
const INITIAL_TEMPO: TempoLevel = "gentle";

export default function App() {
  const [options, setOptions] = useState<OptionsResponse | null>(null);
  const [optionsError, setOptionsError] = useState<string | null>(null);

  const [step, setStep] = useState<Step>("home");

  const [bgmType, setBgmType] = useState<BgmType | null>(null);
  const [moods, setMoods] = useState<Mood[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [natureSounds, setNatureSounds] = useState<NatureSound[]>([]);
  const [durationSec, setDurationSec] = useState(INITIAL_DURATION_SEC);
  const [tempoLevel, setTempoLevel] = useState<TempoLevel>(INITIAL_TEMPO);
  const [bpm, setBpm] = useState<number | null>(null);
  const [provider, setProvider] = useState("procedural");

  const [promptSet, setPromptSet] = useState<PromptSet | null>(null);
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);

  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);

  useEffect(() => {
    getOptions()
      .then(setOptions)
      .catch((e) => setOptionsError(e instanceof Error ? e.message : ja.common.error));
  }, []);

  const buildRequest = (): GenerateRequest => ({
    bgm_type: bgmType ?? "daytime",
    moods,
    instruments,
    nature_sounds: natureSounds,
    duration_sec: durationSec,
    tempo_level: tempoLevel,
    bpm,
    provider,
    for_elderly_care: true,
  });

  const resetAll = () => {
    setBgmType(null);
    setMoods([]);
    setInstruments([]);
    setNatureSounds([]);
    setDurationSec(INITIAL_DURATION_SEC);
    setTempoLevel(INITIAL_TEMPO);
    setBpm(null);
    setProvider("procedural");
    setPromptSet(null);
    setPromptError(null);
    setGenerationResult(null);
    setGenerationError(null);
    setStep("home");
  };

  const handleSelectBgmType = (value: BgmType) => {
    setBgmType(value);
    const preset = options?.bgm_types.find((t) => t.key === value);
    if (preset) {
      setMoods(preset.default_moods);
      setInstruments(preset.default_instruments);
      setNatureSounds(preset.default_nature_sounds);
      setTempoLevel(preset.default_tempo);
    }
  };

  const loadPrompt = async () => {
    setPromptLoading(true);
    setPromptError(null);
    setStep("prompt");
    try {
      const result = await generatePrompt(buildRequest());
      setPromptSet(result);
    } catch (e) {
      setPromptError(e instanceof Error ? e.message : ja.common.error);
    } finally {
      setPromptLoading(false);
    }
  };

  const runGeneration = async () => {
    setStep("generating");
    setGenerationError(null);
    try {
      const result = await generateBgm(buildRequest());
      setGenerationResult(result);
      setStep("soundcheck");
    } catch (e) {
      setGenerationError(e instanceof Error ? e.message : ja.common.error);
    }
  };

  if (optionsError) {
    return (
      <div className="app-main">
        <div className="error-box">
          サーバーに接続できませんでした。バックエンドAPIが起動しているかご確認ください。
          <br />
          {optionsError}
        </div>
        <button type="button" className="big-button" onClick={() => window.location.reload()}>
          {ja.common.retry}
        </button>
      </div>
    );
  }

  if (!options) {
    return (
      <div className="app-main">
        <div className="spinner" role="status" aria-label={ja.common.loading} />
      </div>
    );
  }

  return (
    <>
      <header className="app-header">
        <h1>{ja.appTitle}</h1>
        <p>{ja.appSubtitle}</p>
      </header>
      <main className="app-main">
        {step === "home" && (
          <HomePage onStart={() => setStep("type")} onShowProjects={() => setStep("projects")} />
        )}

        {step === "type" && (
          <TypeSelectPage
            bgmTypes={options.bgm_types}
            value={bgmType}
            onChange={handleSelectBgmType}
            onBack={() => setStep("home")}
            onNext={() => setStep("mood")}
          />
        )}

        {step === "mood" && (
          <MoodSelectPage
            moods={options.moods}
            value={moods}
            onChange={setMoods}
            onBack={() => setStep("type")}
            onNext={() => setStep("instrument")}
          />
        )}

        {step === "instrument" && (
          <InstrumentSelectPage
            instruments={options.instruments}
            value={instruments}
            onChange={setInstruments}
            onBack={() => setStep("mood")}
            onNext={() => setStep("nature")}
          />
        )}

        {step === "nature" && (
          <NatureSelectPage
            natureSounds={options.nature_sounds}
            value={natureSounds}
            onChange={setNatureSounds}
            onBack={() => setStep("instrument")}
            onNext={() => setStep("duration")}
          />
        )}

        {step === "duration" && (
          <DurationTempoPage
            durationChoicesSec={options.duration_choices_sec}
            tempoLevels={options.tempo_levels}
            providers={options.providers}
            durationSec={durationSec}
            tempoLevel={tempoLevel}
            bpm={bpm}
            provider={provider}
            onChangeDuration={setDurationSec}
            onChangeTempo={setTempoLevel}
            onChangeBpm={setBpm}
            onChangeProvider={setProvider}
            onBack={() => setStep("nature")}
            onNext={loadPrompt}
          />
        )}

        {step === "prompt" && (
          <PromptPreviewPage
            prompts={promptSet}
            loading={promptLoading}
            error={promptError}
            onBack={() => setStep("duration")}
            onGenerate={runGeneration}
          />
        )}

        {step === "generating" && (
          <GeneratingPage error={generationError} onBack={() => setStep("prompt")} onRetry={runGeneration} />
        )}

        {step === "soundcheck" && generationResult && (
          <SoundCheckPage
            safety={generationResult.safety}
            score={generationResult.score}
            onBack={() => setStep("prompt")}
            onNext={() => setStep("preview")}
          />
        )}

        {step === "preview" && generationResult && (
          <PreviewPage
            previewUrl={generationResult.preview_url}
            onBack={() => setStep("soundcheck")}
            onNext={() => setStep("save")}
          />
        )}

        {step === "save" && generationResult && (
          <SaveExportPage
            generationId={generationResult.generation_id}
            defaultTitle={`${options.bgm_types.find((t) => t.key === bgmType)?.label ?? "BGM"}_${generationResult.generation_id}`}
            request={buildRequest()}
            onBack={() => setStep("preview")}
            onDone={resetAll}
          />
        )}

        {step === "projects" && <ProjectsPage onBack={() => setStep("home")} />}
      </main>
    </>
  );
}
