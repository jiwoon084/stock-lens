export type LlmProvider = "solar" | "gemini";

export interface MovementExplanationRequest {
  ticker: string;
  selected_date: string;
  interval: string;
  llm_provider: LlmProvider;
}

export type FactorImpact = "positive" | "negative" | "neutral";

export interface Factor {
  title: string;
  impact: FactorImpact;
  description: string;
  source_ids: string[];
}

export interface Source {
  id: string;
  type: string;
  title: string;
  publisher: string;
  published_at: string;
  url: string;
  excerpt: string;
  summary_lines: string[];
}

export type MovementDirection = "up" | "down" | "flat";
export type ConfidenceLevel = "low" | "medium" | "high";

export interface MovementExplanationResponse {
  ticker: string;
  selected_date: string;
  price: number;
  change_percent: number;
  volume_change_percent: number;
  direction: MovementDirection;
  headline: string;
  summary: string;
  confidence: ConfidenceLevel;
  factors: Factor[];
  sources: Source[];
  limitations: string[];
}
