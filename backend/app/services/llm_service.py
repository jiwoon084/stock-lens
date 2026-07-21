"""Movement analysis: a real SOLAR/Gemini call when possible, a rule-based heuristic otherwise.

`generate_movement_explanation()` dispatches on `provider` ("solar" | "gemini") via
`_PROVIDERS` below — see app/services/solar_client.py / gemini_client.py for how each builds
its prompt from app/prompts/explain_movement.txt and enforces a JSON schema. The rule-based
heuristic never calls an LLM — each factor is built directly from an actual DART disclosure's
title (report_nm), so the content is real; only the positive/negative/neutral labeling is tied
to price direction, not derived from reading the filing. Kept as the fallback for both
providers so the API never breaks on a missing key or a provider-side failure.
"""

import logging
from pathlib import Path

from app.core.config import settings
from app.schemas.explanation import Factor, Source
from app.services import gemini_client, solar_client

logger = logging.getLogger(__name__)

MAX_FACTORS = 3

# provider name -> (client module, its error class, "is this provider's key configured?")
_PROVIDERS = {
    "solar": (solar_client, solar_client.SolarApiError, lambda: bool(settings.solar_api_key)),
    "gemini": (gemini_client, gemini_client.GeminiApiError, lambda: bool(settings.gemini_api_key)),
}

_IMPACT_BY_DIRECTION = {"up": "positive", "down": "negative", "flat": "neutral"}

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "explain_movement.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _documents_block(sources: list[Source]) -> str:
    return "\n".join(
        f"- [{source.id}] ({source.type}, {source.published_at[:10]}) {source.title}: {source.excerpt}"
        for source in sources
    )


def _build_prompt(
    ticker: str,
    selected_date: str,
    price: float,
    change_percent: float,
    volume_change_percent: float,
    sources: list[Source],
) -> str:
    return _PROMPT_TEMPLATE.format(
        ticker=ticker,
        selected_date=selected_date,
        price=price,
        change_percent=change_percent,
        volume_change_percent=volume_change_percent,
        retrieved_documents=_documents_block(sources),
    )


def _sanitize_factors(factors: list[Factor], sources: list[Source]) -> list[Factor]:
    """Drop any source_ids an LLM cited that don't match a document we actually retrieved —
    a hallucinated citation is worse than an unlinked factor.
    """
    known_ids = {source.id for source in sources}
    return [
        factor.model_copy(update={"source_ids": [sid for sid in factor.source_ids if sid in known_ids]})
        for factor in factors
    ]


def generate_movement_explanation(
    ticker: str,
    selected_date: str,
    price: float,
    change_percent: float,
    volume_change_percent: float,
    direction: str,
    sources: list[Source],
    provider: str = "solar",
) -> dict:
    if not sources:
        return _no_sources_response(selected_date)

    client, error_cls, has_key = _PROVIDERS.get(provider, (None, None, None))
    if client is not None and has_key():
        try:
            prompt = _build_prompt(ticker, selected_date, price, change_percent, volume_change_percent, sources)
            result = client.generate_movement_explanation(prompt)
            result["factors"] = _sanitize_factors(result["factors"], sources)
            return result
        except error_cls as exc:
            logger.warning(
                "%s call failed for %s/%s, falling back to rule-based response: %s",
                provider,
                ticker,
                selected_date,
                exc,
            )

    return _rule_based_response(selected_date, change_percent, volume_change_percent, direction, sources)


def _no_sources_response(selected_date: str) -> dict:
    return {
        "headline": "관련 공시·뉴스 자료를 찾지 못했습니다.",
        "summary": (
            f"선택 시점({selected_date}) 전후로 조회 가능한 DART 공시나 뉴스가 없어, 가격 변동과 "
            "관련지을 수 있는 공개 자료를 확인하지 못했습니다."
        ),
        "confidence": "low",
        "factors": [],
        "limitations": ["관련 공시·뉴스 검색 결과가 없어 요인을 도출할 수 없습니다."],
    }


def _rule_based_response(
    selected_date: str,
    change_percent: float,
    volume_change_percent: float,
    direction: str,
    sources: list[Source],
) -> dict:
    impact = _IMPACT_BY_DIRECTION.get(direction, "neutral")
    top_sources = sources[:MAX_FACTORS]

    factors = [
        Factor(
            title=source.title,
            impact=impact,
            description=source.excerpt,
            source_ids=[source.id],
        )
        for source in top_sources
    ]

    headline = f"'{top_sources[0].title}' 공시가 이 시점 가격 변동과 관련이 있을 수 있습니다."
    summary = (
        f"선택 시점({selected_date}) 전후 {len(sources)}건의 자료 중 등락률 "
        f"{change_percent:+.2f}%, 거래량 변화 {volume_change_percent:+.2f}%와 시점상 가까운 "
        f"{len(top_sources)}건을 관련 요인으로 정리했습니다."
    )

    confidence = "medium" if abs(change_percent) >= 1.5 else "low"

    limitations = [
        "공시/기사 제목과 접수일만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다.",
        "호재/유의/중립 표시는 실제 내용을 분석한 것이 아니라, 등락 방향에 따른 단순 추정입니다.",
    ]

    return {
        "headline": headline,
        "summary": summary,
        "confidence": confidence,
        "factors": factors,
        "limitations": limitations,
    }
