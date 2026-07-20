"""Mock LLM analysis.

Stands in for a future SOLAR/Gemini call (see app/prompts/explain_movement.txt
for the prompt this will eventually use). Returns a response shaped exactly
like the real one will be, so the frontend contract does not change later.
"""

from app.schemas.explanation import Factor, Source


def generate_movement_explanation(
    ticker: str,
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
