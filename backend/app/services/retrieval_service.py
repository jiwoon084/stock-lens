"""Mock document retrieval.

Stands in for the future RAG pipeline. Returns a small, deterministic set of
news/report-shaped documents for a given ticker and date so the API contract
downstream (LLM service, response schema) can be built and tested now.
"""

from app.schemas.explanation import Source

_PUBLISHERS = ["샘플 경제신문", "샘플 증권리서치", "샘플 뉴스와이어"]


def get_related_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    tone = "긍정적인" if direction == "up" else "부정적인" if direction == "down" else "중립적인"

    return [
        Source(
            id="source-1",
            type="news",
            title=f"{ticker} 관련 {tone} 시장 반응 기사",
            publisher=_PUBLISHERS[0],
            published_at=f"{selected_date}T09:20:00+09:00",
            url="https://example.com/news/1",
            excerpt=f"{selected_date} 전후로 {tone} 수급 변화가 관찰되었다는 내용입니다.",
        ),
        Source(
            id="source-2",
            type="report",
            title=f"{ticker} 업종 전망 리포트",
            publisher=_PUBLISHERS[1],
            published_at=f"{selected_date}T08:00:00+09:00",
            url="https://example.com/report/1",
            excerpt="업황 및 실적 전망에 대한 애널리스트 의견을 요약한 리포트 발췌입니다.",
        ),
        Source(
            id="source-3",
            type="disclosure",
            title=f"{ticker} 공시 요약",
            publisher=_PUBLISHERS[2],
            published_at=f"{selected_date}T16:00:00+09:00",
            url="https://example.com/disclosure/1",
            excerpt="공개된 공시 자료 중 가격 변동과 관련될 수 있는 항목 발췌입니다.",
        ),
    ]
