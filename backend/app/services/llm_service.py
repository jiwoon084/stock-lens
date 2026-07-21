"""Movement analysis: routes each request to SOLAR-pro2 or Gemini Flash by difficulty.

Not a fail-over chain — the two models split work by task difficulty. Requests backed by more
evidence (> _SIMPLE_SOURCE_THRESHOLD sources — several disclosures/news to reconcile into one
analysis) are harder to synthesize well, so they go to SOLAR-pro2 (stronger model); requests
backed by few/no sources are simple enough for Gemini Flash (cheaper/faster). If the routed
provider has no key or errors out, the other one is tried once as a same-request safety net
before giving up to the mock — so a missing/invalid key never breaks the feature, but that
fallback is a resilience measure, not the primary selection logic.

Both providers expose an OpenAI-compatible chat completions endpoint, so a single
`openai.OpenAI` client (pointed at a different base_url/api_key/model per provider) covers
both — no provider-specific SDK needed. Retrieval (which documents count as evidence) stays the
deterministic logic in retrieval_service.py/checklist_service.py; only the natural-language
write-up here is LLM-generated, and the prompt only lets it cite source ids it was actually
given (see app/prompts/explain_movement.txt) — this keeps the "출처 기반 신뢰성" guarantee even
once a real model is writing the prose.

If LLM_PROVIDER=mock, or both providers are missing a key/fail, this falls back to a
deterministic canned analysis so the feature never hard-fails for the user.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.core.config import settings
from app.schemas.explanation import Factor, Source

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "explain_movement.txt"
_VALID_IMPACT = {"positive", "negative", "neutral"}
_VALID_CONFIDENCE = {"low", "medium", "high"}
_SIMPLE_SOURCE_THRESHOLD = 2  # 근거 자료가 이 개수 이하면 "쉬운 요청" -> Gemini Flash, 초과하면 "어려운 요청" -> SOLAR


@dataclass(frozen=True)
class _Provider:
    name: str
    api_key: str
    base_url: str
    model: str


def _solar() -> _Provider:
    return _Provider("solar", settings.upstage_api_key, settings.solar_base_url, settings.solar_model)


def _gemini() -> _Provider:
    return _Provider(
        "gemini",
        settings.gemini_api_key,
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        settings.gemini_model,
    )


def _providers_for(num_sources: int) -> list[_Provider]:
    """Returns [routed_provider, other_provider] — the second entry is only a same-request
    fallback if the routed one is unavailable, not part of the difficulty routing itself."""
    if num_sources <= _SIMPLE_SOURCE_THRESHOLD:
        return [_gemini(), _solar()]
    return [_solar(), _gemini()]


def _documents_block(sources: list[Source]) -> str:
    if not sources:
        return "(관련 문서를 찾지 못했습니다.)"
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
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        ticker=ticker,
        selected_date=selected_date,
        price=price,
        change_percent=change_percent,
        volume_change_percent=volume_change_percent,
        retrieved_documents=_documents_block(sources),
    )


def _parse_llm_response(text: str, valid_source_ids: set[str]) -> dict | None:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        payload = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None

    headline = str(payload.get("headline", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    if not headline or not summary:
        return None

    factors_raw = payload.get("factors")
    if not isinstance(factors_raw, list):
        return None

    factors: list[Factor] = []
    for item in factors_raw:
        if not isinstance(item, dict) or item.get("impact") not in _VALID_IMPACT:
            continue
        source_ids = [sid for sid in item.get("source_ids", []) if sid in valid_source_ids]
        factors.append(
            Factor(
                title=str(item.get("title", "")).strip() or "관련 요인",
                impact=item["impact"],
                description=str(item.get("description", "")).strip(),
                source_ids=source_ids,
            )
        )
    if not factors:
        return None

    confidence = payload.get("confidence")
    if confidence not in _VALID_CONFIDENCE:
        confidence = "low"

    limitations = [str(item).strip() for item in payload.get("limitations", []) if str(item).strip()]
    if not limitations:
        limitations = ["공개 자료만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다."]

    return {
        "headline": headline,
        "summary": summary,
        "confidence": confidence,
        "factors": factors,
        "limitations": limitations,
    }


def _call_provider(provider: _Provider, prompt: str, valid_source_ids: set[str]) -> dict | None:
    if not provider.api_key:
        return None

    client = OpenAI(
        api_key=provider.api_key,
        base_url=provider.base_url,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_num_retries,
    )

    try:
        response = client.chat.completions.create(
            model=provider.model,
            messages=[
                {
                    "role": "system",
                    "content": "Respond with only a single JSON object. No markdown code fences, no commentary.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001 - any provider failure just falls through to the next one
        logger.warning("LLM provider '%s' failed, trying next fallback: %s", provider.name, exc)
        return None

    content = response.choices[0].message.content or ""
    result = _parse_llm_response(content, valid_source_ids)
    if result is None:
        logger.warning("LLM provider '%s' returned an unparseable response, trying next fallback.", provider.name)
    return result


def _mock_analysis(
    selected_date: str,
    change_percent: float,
    volume_change_percent: float,
    direction: str,
    sources: list[Source],
) -> dict:
    source_ids = [source.id for source in sources]

    if direction == "up":
        headline = "실적 기대와 수급 개선이 주요 관련 요인으로 분석됩니다."
        factors = [
            Factor(
                title="실적 기대 상승",
                impact="positive",
                description="시장 전망치를 상회할 수 있다는 기대가 관련 자료에서 언급되었습니다.",
                source_ids=source_ids[:2],
            ),
            Factor(
                title="수급 개선",
                impact="positive",
                description="거래량 증가와 함께 매수 우위 수급이 관찰되었습니다.",
                source_ids=source_ids[1:],
            ),
        ]
    elif direction == "down":
        headline = "업황 우려와 매도 수급이 주요 관련 요인으로 분석됩니다."
        factors = [
            Factor(
                title="업황 우려 확대",
                impact="negative",
                description="관련 업종에 대한 부정적 전망이 자료에서 언급되었습니다.",
                source_ids=source_ids[:2],
            ),
            Factor(
                title="매도 수급 우위",
                impact="negative",
                description="거래량 변화와 함께 매도 우위 수급이 관찰되었습니다.",
                source_ids=source_ids[1:],
            ),
        ]
    else:
        headline = "뚜렷한 방향성 없이 관망세가 이어진 것으로 분석됩니다."
        factors = [
            Factor(
                title="특별한 이슈 부재",
                impact="neutral",
                description="선택 시점 전후로 가격에 뚜렷한 영향을 준 이벤트가 확인되지 않았습니다.",
                source_ids=source_ids[:1],
            ),
        ]

    summary = (
        f"선택 시점({selected_date}) 전후의 공개 자료를 종합하면, 등락률 {change_percent:+.2f}% 및 "
        f"거래량 변화 {volume_change_percent:+.2f}%와 함께 위 요인들이 가격 변동과 관련이 있는 것으로 "
        "확인됩니다. 이는 Mock 데이터 기반 분석입니다."
    )

    confidence = "medium" if abs(change_percent) >= 1.5 else "low"

    limitations = [
        "공개 자료만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다.",
        "현재 응답은 실제 LLM 호출 없이 생성된 Mock 데이터입니다.",
    ]

    return {
        "headline": headline,
        "summary": summary,
        "confidence": confidence,
        "factors": factors,
        "limitations": limitations,
    }


def generate_movement_explanation(
    ticker: str,
    selected_date: str,
    price: float,
    change_percent: float,
    volume_change_percent: float,
    direction: str,
    sources: list[Source],
) -> dict:
    if settings.llm_provider != "mock":
        prompt = _build_prompt(ticker, selected_date, price, change_percent, volume_change_percent, sources)
        valid_source_ids = {source.id for source in sources}

        for provider in _providers_for(len(sources)):
            result = _call_provider(provider, prompt, valid_source_ids)
            if result is not None:
                return result

        logger.warning("Both LLM providers unavailable/failed for %s %s; falling back to mock.", ticker, selected_date)

    return _mock_analysis(selected_date, change_percent, volume_change_percent, direction, sources)
