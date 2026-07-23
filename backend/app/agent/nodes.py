"""LangGraph nodes for the stock-analysis pipeline (POST /api/analysis/date).

Each node is a thin wrapper around the existing, independently-tested helpers in
app/services/stock_analysis_service.py — this module adds explicit graph structure, not new
business logic. The helpers stay defined there (not duplicated here) so the existing unit
tests that call them directly (e.g. `stock_analysis_service._sanitize_result(...)` in
backend/tests/test_stock_analysis_service.py) keep working unchanged.

Imports `app.services.stock_analysis_service` at module load time. That module only imports
this graph back via a *local* import inside `analyze_date()` (not at its own top level) —
otherwise this would be a circular import. See app/agent/graph.py's docstring.
"""

from datetime import date

from app.agent.state import AnalysisGraphState
from app.rules.watch_item_templates import generate_allowed_watch_items
from app.schemas.stock_analysis import LLMInputContext
from app.services import market_data_service, retrieval_service
from app.services import stock_analysis_service as sas


class TickerNotFoundError(ValueError):
    pass


class DateNotFoundError(ValueError):
    pass


def fetch_market_data(state: AnalysisGraphState) -> dict:
    ticker = state["ticker"]
    selected_date = state["selected_date"]

    stock = market_data_service.get_stock(ticker)
    if stock is None:
        raise TickerNotFoundError(ticker)

    # get_price_series_with_live_today (not plain get_price_series): "오늘" is never in the
    # official daily series yet (KRX EOD lags a day) — this synthesizes today's row from the
    # live KIS quote so analysis works from the intraday tab too. See market_data_service.py.
    prices = market_data_service.get_price_series_with_live_today(ticker)
    index = next((i for i, p in enumerate(prices) if p.time == selected_date), None)
    if index is None:
        raise DateNotFoundError(selected_date)

    point = prices[index]
    direction = "up" if point.change_percent > 0 else "down" if point.change_percent < 0 else "flat"
    # "오늘"은 장이 아직 끝나지 않아 change_percent가 마감 전까지 계속 바뀔 수 있음 —
    # market_data.is_intraday로 넘겨서 프롬프트가 원인 주장 대신 중립적 사실 나열로 전환하고,
    # analyze_date()가 이 값으로 intraday_notice를 붙일지 결정한다.
    is_intraday = selected_date == date.today().isoformat()

    return {
        "company_name": stock.name,
        "prices": prices,
        "price_index": index,
        "direction": direction,
        "is_intraday": is_intraday,
        "market_data": sas._build_market_data_context(prices, index, is_intraday),
    }


def retrieve_evidence(state: AnalysisGraphState) -> dict:
    retrieved = retrieval_service.get_related_documents(
        ticker=state["ticker"], selected_date=state["selected_date"], direction=state["direction"]
    )
    return {
        "disclosures": [s for s in retrieved if s.type == "disclosure"],
        "news": [s for s in retrieved if s.type != "disclosure"],
    }


def build_llm_input(state: AnalysisGraphState) -> dict:
    disclosure_contexts = [sas._to_disclosure_context(s) for s in state["disclosures"]]
    news_contexts = [sas._to_news_context(s) for s in state["news"]]
    allowed_watch_items = generate_allowed_watch_items(disclosure_contexts, news_contexts)

    llm_input = LLMInputContext(
        ticker=state["ticker"],
        company_name=state["company_name"],
        selected_date=state["selected_date"],
        market_data=state["market_data"],
        quick_fact_candidates=sas._build_quick_fact_candidates(state["market_data"]),
        disclosures=disclosure_contexts,
        news=news_contexts,
        allowed_watch_items=allowed_watch_items,
    )
    return {"llm_input": llm_input}


def generate_analysis(state: AnalysisGraphState) -> dict:
    llm_input = state["llm_input"]
    if not llm_input.disclosures and not llm_input.news:
        result = sas._fallback_result(llm_input)
    else:
        result = sas._generate_result(llm_input, state.get("llm_provider"))
    return {"result": result}
