"""LangGraph state for the stock-analysis pipeline (POST /api/analysis/date).

This repurposes the folder's original "종목 Q&A 챗봇" placeholder (see git history) for the one
flow that actually exists today: app/services/stock_analysis_service.analyze_date(). A separate
chatbot state would live alongside this one, not replace it, if that feature is ever built.
"""

from typing import Optional, TypedDict

from app.schemas.explanation import Source
from app.schemas.stock import PricePoint
from app.schemas.stock_analysis import LLMInputContext, MarketDataContext, StockAnalysisResult


class AnalysisGraphState(TypedDict, total=False):
    # inputs
    ticker: str
    selected_date: str
    llm_provider: Optional[str]

    # set by nodes.fetch_market_data
    company_name: str
    prices: list[PricePoint]
    price_index: int
    direction: str
    market_data: MarketDataContext

    # set by nodes.retrieve_evidence
    disclosures: list[Source]
    news: list[Source]

    # set by nodes.build_llm_input
    llm_input: LLMInputContext

    # set by nodes.generate_analysis
    result: StockAnalysisResult
