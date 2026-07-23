from typing import Literal

from pydantic import BaseModel, Field


class MovementExplanationRequest(BaseModel):
    ticker: str
    selected_date: str
    interval: str = "1d"
    llm_provider: Literal["solar", "gemini"] = "solar"


class Factor(BaseModel):
    title: str
    impact: Literal["positive", "negative", "neutral"]
    description: str
    source_ids: list[str]


class Source(BaseModel):
    id: str
    type: str
    title: str
    publisher: str
    published_at: str
    url: str
    excerpt: str
    # Short (<=3 line) plain-language summary of `excerpt` for card display. Always populated —
    # retrieval_service seeds a naive line-split as a deterministic default, and
    # explanation_service overwrites it with the LLM's version when a provider call succeeds
    # (same "deterministic fallback, LLM enhances when available" pattern as the rest of the app).
    summary_lines: list[str] = Field(default_factory=list)


class MovementExplanationResponse(BaseModel):
    ticker: str
    selected_date: str
    price: float
    change_percent: float
    volume_change_percent: float
    direction: Literal["up", "down", "flat"]
    headline: str
    summary: str
    confidence: Literal["low", "medium", "high"]
    factors: list[Factor]
    sources: list[Source]
    limitations: list[str]
