"""Response + LLM-input-context models for the date-click stock analysis feature
(POST /api/analysis/date — see app/services/stock_analysis_service.py).

Two groups of models live here:
- LLM input context (LLMInputContext and its parts): built by the backend from real market
  data / disclosures / news, then serialized and handed to the LLM as the only facts it's
  allowed to draw from.
- LLM output (StockAnalysisResult / ChartCard / DetailPanel and their parts): what the LLM
  must return, re-validated field-by-field against the input context in
  stock_analysis_service.py before it ever reaches the frontend.
"""

from typing import Literal

from pydantic import BaseModel, Field

EvidenceType = Literal["official_disclosure", "market_data", "media_report"]
EvidenceLevel = Literal["high", "medium", "low"]
MovementStatus = Literal["confirmed", "reported", "uncertain", "not_found"]
SignalType = Literal[
    "official_confirmation",
    "business_result",
    "market_flow",
    "market_environment",
    "follow_up_disclosure",
    "unresolved_issue",
]


# ---- LLM input context -----------------------------------------------------------------


class QuickFactCandidate(BaseModel):
    id: str
    label: str
    value: str


class MarketDataContext(BaseModel):
    source_id: str
    close: float
    price_change_text: str
    change_percent: float
    volume: int
    volume_ratio_20d: float | None = None
    volume_comparison_text: str | None = None
    benchmark_name: str | None = None
    benchmark_change_text: str | None = None
    market_comparison_text: str | None = None


class DisclosureContext(BaseModel):
    source_id: str
    source_type: Literal["official_disclosure"] = "official_disclosure"
    title: str
    display_label: str
    published_at: str
    excerpt: str
    available_topics: list[str] = Field(default_factory=list)


class NewsContext(BaseModel):
    source_id: str
    source_type: Literal["media_report"] = "media_report"
    title: str
    published_at: str
    description: str
    available_topics: list[str] = Field(default_factory=list)


class AllowedWatchItem(BaseModel):
    id: str
    title: str
    description: str
    signal_type: SignalType
    source_ids: list[str] = Field(default_factory=list)


class LLMInputContext(BaseModel):
    ticker: str
    company_name: str
    selected_date: str
    market_data: MarketDataContext
    quick_fact_candidates: list[QuickFactCandidate] = Field(default_factory=list)
    disclosures: list[DisclosureContext] = Field(default_factory=list)
    news: list[NewsContext] = Field(default_factory=list)
    allowed_watch_items: list[AllowedWatchItem] = Field(default_factory=list)


# ---- LLM output / API response --------------------------------------------------------


class QuickFact(BaseModel):
    label: str
    value: str


class PrimaryEvidence(BaseModel):
    label: str
    source_id: str


class ChartCard(BaseModel):
    selected_date: str
    price_change_text: str
    one_line_summary: str
    quick_facts: list[QuickFact] = Field(default_factory=list, max_length=2)
    primary_evidence: PrimaryEvidence | None = None


class MovementItem(BaseModel):
    title: str
    description: str
    status: MovementStatus
    evidence_type: EvidenceType
    evidence_level: EvidenceLevel
    source_ids: list[str] = Field(default_factory=list)


class WatchItem(BaseModel):
    title: str
    description: str
    signal_type: SignalType
    source_ids: list[str] = Field(default_factory=list)


class RecommendedMaterial(BaseModel):
    source_id: str
    description: str
    information_to_verify: list[str] = Field(default_factory=list, max_length=3)


class DetailPanel(BaseModel):
    why_it_moved: list[MovementItem] = Field(default_factory=list, max_length=2)
    what_to_watch: list[WatchItem] = Field(default_factory=list, max_length=3)
    recommended_materials: list[RecommendedMaterial] = Field(default_factory=list, max_length=2)
    caution: str


class StockAnalysisResult(BaseModel):
    chart_card: ChartCard
    detail_panel: DetailPanel


class SourceMetadata(BaseModel):
    source_id: str
    source_type: EvidenceType
    title: str
    url: str
    publisher: str
    published_at: str


class StockAnalysisRequest(BaseModel):
    ticker: str
    selected_date: str


class StockAnalysisResponse(BaseModel):
    analysis: StockAnalysisResult
    sources: dict[str, SourceMetadata] = Field(default_factory=dict)
