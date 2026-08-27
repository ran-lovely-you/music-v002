export type BgmType =
  | "morning"
  | "daytime"
  | "focus"
  | "reminiscence"
  | "forest"
  | "night"
  | "mystic_forest";

export type TempoLevel = "very_slow" | "slow" | "gentle" | "normal";

export type Mood =
  | "healing"
  | "calm"
  | "bright"
  | "reassuring"
  | "mystic"
  | "natural"
  | "nostalgic"
  | "focus"
  | "sleep"
  | "hopeful";

export type Instrument =
  | "piano"
  | "harp"
  | "music_box"
  | "acoustic_guitar"
  | "flute"
  | "clarinet"
  | "marimba"
  | "soft_strings"
  | "pad"
  | "bell"
  | "chime";

export type NatureSound = "rain" | "river" | "waves" | "forest" | "birds" | "wind" | "campfire";

export interface OptionItem {
  key: string;
  label: string;
}

export interface BgmTypeOption {
  key: BgmType;
  label: string;
  description: string;
  default_moods: Mood[];
  default_instruments: Instrument[];
  default_nature_sounds: NatureSound[];
  default_tempo: TempoLevel;
}

export interface ProviderOption {
  key: string;
  name: string;
  requires_api_key: boolean;
  available: boolean;
}

export interface OptionsResponse {
  bgm_types: BgmTypeOption[];
  moods: OptionItem[];
  instruments: OptionItem[];
  nature_sounds: OptionItem[];
  tempo_levels: OptionItem[];
  duration_choices_sec: number[];
  providers: ProviderOption[];
}

export interface GenerateRequest {
  bgm_type: BgmType;
  moods: Mood[];
  instruments: Instrument[];
  nature_sounds: NatureSound[];
  duration_sec: number;
  tempo_level: TempoLevel;
  bpm?: number | null;
  provider?: string | null;
  title?: string | null;
  for_elderly_care: boolean;
}

export interface PromptSet {
  short: string;
  detailed: string;
  professional: string;
  negative: string;
}

export type SafetyStatus = "green" | "yellow" | "red";

export interface SafetyCheckItem {
  key: string;
  label: string;
  status: SafetyStatus;
  message: string;
}

export interface SafetyReport {
  overall_status: SafetyStatus;
  items: SafetyCheckItem[];
}

export interface AnalysisResult {
  duration_sec: number;
  sample_rate: number;
  peak_dbfs: number;
  rms_dbfs: number;
  lufs_integrated: number | null;
  clipping_detected: boolean;
  clipping_sample_count: number;
  high_freq_energy_ratio: number;
  low_freq_energy_ratio: number;
  max_short_term_dynamic_jump_db: number;
  rhythm_intensity: number;
  silence_ratio: number;
}

export interface ScoreBreakdown {
  relaxation: number;
  listenability: number;
  volume_stability: number;
  tonal_balance: number;
  long_duration_suitability: number;
  naturalness: number;
  elderly_fit: number;
}

export interface QualityScore {
  total: number;
  breakdown: ScoreBreakdown;
  disclaimer: string;
}

export interface GenerationResult {
  generation_id: string;
  request: GenerateRequest;
  prompts: PromptSet;
  preview_url: string;
  analysis: AnalysisResult;
  safety: SafetyReport;
  score: QualityScore;
  provider_used: string;
}

export interface ProjectRecord {
  id: string;
  title: string;
  created_at: string;
  bgm_type: BgmType;
  bpm: number;
  instruments: Instrument[];
  nature_sounds: NatureSound[];
  prompts: PromptSet;
  analysis: AnalysisResult;
  safety: SafetyReport;
  score: QualityScore;
  audio_path: string;
}

export interface YoutubeMetadata {
  titles: string[];
  description: string;
  tags: string[];
  hashtags: string[];
  thumbnail_prompt: string;
  intro_text: string;
}

export interface ApiErrorBody {
  detail: string;
}
