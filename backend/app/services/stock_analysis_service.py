"""Orchestrates POST /api/analysis/date: real market data + retrieval, backend-built candidate
data (quick facts / watch items / available topics), one LLM call (SOLAR by default, see
app/services/llm/factory.py) constrained to those candidates, then strict re-validation before
anything reaches the frontend.

This is a separate feature from app/services/explanation_service.py (POST /api/v1/explanations,
still used by the market-events "관련 자료" list) — that endpoint, its schema, and its
user-selectable SOLAR/Gemini toggle are untouched.
"""

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.schemas.explanation import Source
from app.schemas.stock import PricePoint
from app.schemas.stock_analysis import (
    AllowedWatchItem,
    ChartCard,
    DetailPanel,
    DisclosureContext,
    LLMInputContext,
    MarketDataContext,
    MovementItem,
    NewsContext,
    PrimaryEvidence,
    QuickFact,
    QuickFactCandidate,
    RecommendedMaterial,
    SourceMetadata,
    StockAnalysisResponse,
    StockAnalysisResult,
    WatchItem,
)
from app.rules.watch_item_templates import generate_allowed_watch_items
from app.services import market_data_service, retrieval_service
from app.services.llm import factory
from app.services.llm.base import LLMProviderError

logger = logging.getLogger(__name__)

MAX_RETRIES = 1
MARKET_DATA_SOURCE_ID = "market-data"
DEFAULT_CAUTION = "공개된 정보만으로 이날 주가가 움직인 이유를 하나로 확정할 수는 없어요."
NO_DATA_SUMMARY = "이 날짜에는 설명에 활용할 공식 공시나 관련 뉴스가 충분하지 않아요."

_SUPPLY_CONTRACT_KEYWORD = "공급계약"

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "stock_analysis_system.txt"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class UnknownTickerError(ValueError):
    pass


class UnknownDateError(ValueError):
    pass


# ---- candidate-data construction (backend-computed, LLM never sees raw numbers to convert) --


def _format_percent(value: float) -> str:
    return f"{value:+.1f}%"


def _volume_ratio_20d(prices: list[PricePoint], index: int) -> float | None:
    window = prices[max(0, index - 20) : index]
    if not window:
        return None
    avg_volume = sum(p.volume for p in window) / len(window)
    if avg_volume <= 0:
        return None
    return prices[index].volume / avg_volume


def _build_market_data_context(prices: list[PricePoint], index: int) -> MarketDataContext:
    point = prices[index]
    ratio = _volume_ratio_20d(prices, index)
    return MarketDataContext(
        source_id=MARKET_DATA_SOURCE_ID,
        close=point.close,
        price_change_text=_format_percent(point.change_percent),
        change_percent=point.change_percent,
        volume=point.volume,
        volume_ratio_20d=ratio,
        volume_comparison_text=f"평소의 {ratio:.1f}배" if ratio is not None else None,
    )


def _build_quick_fact_candidates(market_data: MarketDataContext) -> list[QuickFactCandidate]:
    candidates: list[QuickFactCandidate] = []
    if market_data.volume_comparison_text:
        candidates.append(QuickFactCandidate(id="quick-001", label="거래량", value=market_data.volume_comparison_text))
    if market_data.market_comparison_text:
        candidates.append(
            QuickFactCandidate(id="quick-002", label="시장과 비교", value=market_data.market_comparison_text)
        )
    return candidates


def _disclosure_display_label(title: str) -> str:
    if _SUPPLY_CONTRACT_KEYWORD in title:
        return "회사의 공급계약 공시"
    return f"회사의 공시: {title}"


def _disclosure_available_topics(title: str) -> list[str]:
    if _SUPPLY_CONTRACT_KEYWORD in title:
        return ["최근 사업연도 매출액 대비 계약금액 비율", "공시 원문에 기재된 계약의 세부 조건"]
    return ["공시 원문에 기재된 세부 내용"]


def _news_available_topics(title: str, description: str) -> list[str]:
    text = f"{title} {description}"
    topics: list[str] = []
    if "HBM" in text:
        topics.append("언론이 언급한 HBM 공급 기대")
    if "외국인" in text:
        topics.append("언론이 언급한 외국인 매수세")
    topics.append("해당 내용이 공식 발표에 기반했는지 여부")
    return topics


def _to_disclosure_context(source: Source) -> DisclosureContext:
    return DisclosureContext(
        source_id=source.id,
        title=source.title,
        display_label=_disclosure_display_label(source.title),
        published_at=source.published_at,
        excerpt=source.excerpt,
        available_topics=_disclosure_available_topics(source.title),
    )


def _to_news_context(source: Source) -> NewsContext:
    return NewsContext(
        source_id=source.id,
        title=source.title,
        published_at=source.published_at,
        description=source.excerpt,
        available_topics=_news_available_topics(source.title, source.excerpt),
    )


def _build_sources_map(disclosures: list[Source], news: list[Source]) -> dict[str, SourceMetadata]:
    sources_map: dict[str, SourceMetadata] = {}
    for source in disclosures:
        sources_map[source.id] = SourceMetadata(
            source_id=source.id,
            source_type="official_disclosure",
            title=source.title,
            url=source.url,
            publisher=source.publisher,
            published_at=source.published_at,
        )
    for source in news:
        sources_map[source.id] = SourceMetadata(
            source_id=source.id,
            source_type="media_report",
            title=source.title,
            url=source.url,
            publisher=source.publisher,
            published_at=source.published_at,
        )
    return sources_map


# ---- LLM output validation (never trust the model's output past this) ----------------------


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _label_for_source(source_id: str, llm_input: LLMInputContext) -> str:
    for disclosure in llm_input.disclosures:
        if disclosure.source_id == source_id:
            return disclosure.display_label
    for article in llm_input.news:
        if article.source_id == source_id:
            return article.title
    return "시장 데이터"


def _sanitize_result(result: StockAnalysisResult, llm_input: LLMInputContext) -> StockAnalysisResult:
    valid_ids = (
        {llm_input.market_data.source_id}
        | {d.source_id for d in llm_input.disclosures}
        | {n.source_id for n in llm_input.news}
    )
    material_ids = {d.source_id for d in llm_input.disclosures} | {n.source_id for n in llm_input.news}
    candidate_facts = {(qf.label, qf.value) for qf in llm_input.quick_fact_candidates}
    allowed_watch_keys = {
        (w.title, w.description, w.signal_type, tuple(sorted(w.source_ids))) for w in llm_input.allowed_watch_items
    }
    topics_by_source = {d.source_id: set(d.available_topics) for d in llm_input.disclosures}
    topics_by_source.update({n.source_id: set(n.available_topics) for n in llm_input.news})

    chart_card = result.chart_card
    quick_facts = [qf for qf in chart_card.quick_facts if (qf.label, qf.value) in candidate_facts][:2]

    primary_evidence = None
    if chart_card.primary_evidence and chart_card.primary_evidence.source_id in valid_ids:
        primary_evidence = PrimaryEvidence(
            label=_label_for_source(chart_card.primary_evidence.source_id, llm_input),
            source_id=chart_card.primary_evidence.source_id,
        )

    chart_card = chart_card.model_copy(update={"quick_facts": quick_facts, "primary_evidence": primary_evidence})

    why_it_moved = [
        item.model_copy(update={"source_ids": _dedupe([sid for sid in item.source_ids if sid in valid_ids])})
        for item in result.detail_panel.why_it_moved[:2]
    ]

    what_to_watch: list[WatchItem] = []
    seen_watch_keys: set[tuple] = set()
    for item in result.detail_panel.what_to_watch:
        key = (item.title, item.description, item.signal_type, tuple(sorted(item.source_ids)))
        if key not in allowed_watch_keys or key in seen_watch_keys:
            continue
        seen_watch_keys.add(key)
        what_to_watch.append(item)
        if len(what_to_watch) == 3:
            break

    recommended_materials: list[RecommendedMaterial] = []
    seen_material_ids: set[str] = set()
    for material in result.detail_panel.recommended_materials:
        if material.source_id not in material_ids or material.source_id in seen_material_ids:
            continue
        seen_material_ids.add(material.source_id)
        allowed_topics = topics_by_source.get(material.source_id, set())
        verified_topics = [t for t in material.information_to_verify if t in allowed_topics][:3]
        recommended_materials.append(material.model_copy(update={"information_to_verify": verified_topics}))
        if len(recommended_materials) == 2:
            break

    detail_panel = result.detail_panel.model_copy(
        update={
            "why_it_moved": why_it_moved,
            "what_to_watch": what_to_watch,
            "recommended_materials": recommended_materials,
            "caution": result.detail_panel.caution or DEFAULT_CAUTION,
        }
    )

    return StockAnalysisResult(chart_card=chart_card, detail_panel=detail_panel)


# ---- deterministic fallback (no LLM call at all — mirrors llm_service._rule_based_response) -


def _fallback_result(llm_input: LLMInputContext) -> StockAnalysisResult:
    top_disclosure = llm_input.disclosures[0] if llm_input.disclosures else None
    top_news = llm_input.news[0] if llm_input.news else None

    quick_facts = [QuickFact(label=c.label, value=c.value) for c in llm_input.quick_fact_candidates[:2]]

    primary_evidence = None
    if top_disclosure is not None:
        primary_evidence = PrimaryEvidence(label=top_disclosure.display_label, source_id=top_disclosure.source_id)
    elif top_news is not None:
        primary_evidence = PrimaryEvidence(label=top_news.title, source_id=top_news.source_id)

    if top_disclosure is not None:
        one_line_summary = f"{top_disclosure.display_label}이(가) 확인됐어요."
    elif top_news is not None:
        one_line_summary = f"'{top_news.title}' 등 관련 뉴스가 확인됐어요."
    else:
        one_line_summary = NO_DATA_SUMMARY

    chart_card = ChartCard(
        selected_date=llm_input.selected_date,
        price_change_text=llm_input.market_data.price_change_text,
        one_line_summary=one_line_summary,
        quick_facts=quick_facts,
        primary_evidence=primary_evidence,
    )

    why_it_moved: list[MovementItem] = []
    if top_disclosure is not None:
        why_it_moved.append(
            MovementItem(
                title=top_disclosure.display_label,
                description=top_disclosure.excerpt,
                status="confirmed",
                evidence_type="official_disclosure",
                evidence_level="high",
                source_ids=[top_disclosure.source_id],
            )
        )
    if top_news is not None and len(why_it_moved) < 2:
        why_it_moved.append(
            MovementItem(
                title=top_news.title,
                description=top_news.description,
                status="reported",
                evidence_type="media_report",
                evidence_level="medium",
                source_ids=[top_news.source_id],
            )
        )

    what_to_watch = [
        WatchItem(title=w.title, description=w.description, signal_type=w.signal_type, source_ids=w.source_ids)
        for w in llm_input.allowed_watch_items[:3]
    ]

    recommended_materials: list[RecommendedMaterial] = []
    for source in [s for s in (top_disclosure, top_news) if s is not None][:2]:
        description = source.excerpt if isinstance(source, DisclosureContext) else source.description
        recommended_materials.append(
            RecommendedMaterial(
                source_id=source.source_id,
                description=description,
                information_to_verify=source.available_topics[:3],
            )
        )

    detail_panel = DetailPanel(
        why_it_moved=why_it_moved,
        what_to_watch=what_to_watch,
        recommended_materials=recommended_materials,
        caution=DEFAULT_CAUTION,
    )

    return StockAnalysisResult(chart_card=chart_card, detail_panel=detail_panel)


def _generate_result(llm_input: LLMInputContext, provider_name: str | None) -> StockAnalysisResult:
    provider = factory.get_provider(provider_name)
    payload = llm_input.model_dump()

    last_error: Exception | None = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            raw = provider.generate(_SYSTEM_PROMPT, payload)
            parsed = json.loads(raw)
            result = StockAnalysisResult.model_validate(parsed)
            return _sanitize_result(result, llm_input)
        except (LLMProviderError, json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning("stock analysis LLM call failed (attempt %d): %s", attempt + 1, exc)

    logger.warning("Falling back to rule-based stock analysis: %s", last_error)
    return _fallback_result(llm_input)


# ---- entrypoint -----------------------------------------------------------------------------


def analyze_date(ticker: str, selected_date: str, llm_provider: str | None = None) -> StockAnalysisResponse:
    stock = market_data_service.get_stock(ticker)
    if stock is None:
        raise UnknownTickerError(f"Unknown ticker: {ticker}")

    prices = market_data_service.get_price_series_with_live_today(ticker)
    index = next((i for i, p in enumerate(prices) if p.time == selected_date), None)
    if index is None:
        raise UnknownDateError(f"No price data for {ticker} on {selected_date}")

    point = prices[index]
    direction = "up" if point.change_percent > 0 else "down" if point.change_percent < 0 else "flat"

    retrieved = retrieval_service.get_related_documents(
        ticker=ticker, selected_date=selected_date, direction=direction
    )
    disclosures = [s for s in retrieved if s.type == "disclosure"]
    news = [s for s in retrieved if s.type != "disclosure"]

    market_data = _build_market_data_context(prices, index)
    disclosure_contexts = [_to_disclosure_context(s) for s in disclosures]
    news_contexts = [_to_news_context(s) for s in news]
    allowed_watch_items: list[AllowedWatchItem] = generate_allowed_watch_items(disclosure_contexts, news_contexts)

    llm_input = LLMInputContext(
        ticker=ticker,
        company_name=stock.name,
        selected_date=selected_date,
        market_data=market_data,
        quick_fact_candidates=_build_quick_fact_candidates(market_data),
        disclosures=disclosure_contexts,
        news=news_contexts,
        allowed_watch_items=allowed_watch_items,
    )

    if not disclosure_contexts and not news_contexts:
        result = _fallback_result(llm_input)
    else:
        result = _generate_result(llm_input, llm_provider)

    return StockAnalysisResponse(analysis=result, sources=_build_sources_map(disclosures, news))
