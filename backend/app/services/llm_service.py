"""Heuristic analysis grounded in real DART disclosure titles.

Still not a real LLM/SOLAR/Gemini call (see app/prompts/explain_movement.txt for the prompt
that will eventually replace this) — there is no sentiment analysis or text understanding here.
Each factor is built directly from an actual disclosure's title (report_nm), so the content is
real; only the positive/negative/neutral labeling is a heuristic tied to price direction, not
derived from reading the filing. This keeps the response honest about what it actually knows.
"""

from app.schemas.explanation import Factor, Source

MAX_FACTORS = 3

_IMPACT_BY_DIRECTION = {"up": "positive", "down": "negative", "flat": "neutral"}


def generate_movement_explanation(
    ticker: str,
    selected_date: str,
    change_percent: float,
    volume_change_percent: float,
    direction: str,
    sources: list[Source],
) -> dict:
    if not sources:
        return {
            "headline": "관련 DART 공시 자료를 찾지 못했습니다.",
            "summary": (
                f"선택 시점({selected_date}) 전후로 조회 가능한 DART 공시가 없어, 가격 변동과 "
                "관련지을 수 있는 공개 자료를 확인하지 못했습니다."
            ),
            "confidence": "low",
            "factors": [],
            "limitations": [
                "DART 공시 검색 결과가 없어 요인을 도출할 수 없습니다.",
                "뉴스·리서치 리포트 등 다른 자료는 아직 연동되지 않았습니다.",
            ],
        }

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
        f"선택 시점({selected_date}) 전후 {len(sources)}건의 DART 공시 중 등락률 "
        f"{change_percent:+.2f}%, 거래량 변화 {volume_change_percent:+.2f}%와 시점상 가까운 "
        f"{len(top_sources)}건을 관련 요인으로 정리했습니다."
    )

    confidence = "medium" if abs(change_percent) >= 1.5 else "low"

    limitations = [
        "공시 제목과 접수일만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다.",
        "호재/유의/중립 표시는 실제 공시 내용을 분석한 것이 아니라, 등락 방향에 따른 단순 추정입니다.",
        "뉴스·리서치 리포트 등 다른 자료는 아직 연동되지 않았습니다.",
    ]

    return {
        "headline": headline,
        "summary": summary,
        "confidence": confidence,
        "factors": factors,
        "limitations": limitations,
    }
