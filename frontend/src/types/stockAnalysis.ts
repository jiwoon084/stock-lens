export type EvidenceType = "official_disclosure" | "market_data" | "media_report";
export type EvidenceLevel = "high" | "medium" | "low";
export type MovementStatus = "confirmed" | "reported" | "uncertain" | "not_found";
export type SignalType =
  | "official_confirmation"
  | "business_result"
  | "market_flow"
  | "market_environment"
  | "follow_up_disclosure"
  | "unresolved_issue";

export interface QuickFact {
  label: string;
  value: string;
}

export interface PrimaryEvidence {
  label: string;
  source_id: string;
}

export interface ChartCard {
  selected_date: string;
  price_change_text: string;
  one_line_summary: string;
  quick_facts: QuickFact[];
  primary_evidence: PrimaryEvidence | null;
}

export interface MovementItem {
  title: string;
  description: string;
  status: MovementStatus;
  evidence_type: EvidenceType;
  evidence_level: EvidenceLevel;
  source_ids: string[];
}

export interface WatchItem {
  title: string;
  description: string;
  signal_type: SignalType;
  source_ids: string[];
}

export interface RecommendedMaterial {
  source_id: string;
  description: string;
  information_to_verify: string[];
}

export interface DetailPanel {
  why_it_moved: MovementItem[];
  what_to_watch: WatchItem[];
  recommended_materials: RecommendedMaterial[];
  caution: string;
  intraday_notice: string | null;
}

export interface StockAnalysis {
  chart_card: ChartCard;
  detail_panel: DetailPanel;
}

export interface SourceMetadata {
  source_id: string;
  source_type: EvidenceType;
  title: string;
  url: string;
  publisher: string;
  published_at: string;
}

export interface StockAnalysisResponse {
  analysis: StockAnalysis;
  sources: Record<string, SourceMetadata>;
}

export interface StockAnalysisRequest {
  ticker: string;
  selected_date: string;
}
