"""Today's article checklist.

Reads the locally collected `data/news.json` (see data/step5_news.py) for real
Naver News results per ticker, groups near-duplicate headlines into issues, and
tags each with a lightweight keyword heuristic (real LLM classification is a
later milestone). That file is gitignored — collected with a personal Naver API
key — so teammates/CI running without it transparently fall back to the
previous canned mock checklist. The response shape is identical either way.
"""

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.schemas.checklist import ChecklistItem, ChecklistResponse, ChecklistTag

_NEWS_PATH = Path(__file__).resolve().parents[3] / "data" / "news.json"
_MAX_ITEMS = 4
_DESCRIPTION_LIMIT = 60

_EARNINGS_KEYWORDS = ["실적", "잠정", "영업이익", "매출", "흑자", "적자"]
_CAUTION_KEYWORDS = ["하락", "우려", "소송", "제재", "리스크", "급락", "감소", "부진"]
_POSITIVE_KEYWORDS = ["공급", "계약", "수주", "합의", "확대", "협력", "최대", "호실적", "상승"]

_SAMSUNG_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        id="chk-1",
        tag="positive",
        headline="HBM 공급계약 체결 보도",
        description="대형 고객사와 차세대 메모리 공급 합의.",
        source_count=3,
    ),
    ChecklistItem(
        id="chk-2",
        tag="earnings",
        headline="3분기 잠정실적 발표 예정",
        description="컨센서스 대비 개선 전망. 발표일 확인 필요.",
        source_count=5,
    ),
    ChecklistItem(
        id="chk-3",
        tag="caution",
        headline="환율·업황 변동성 언급",
        description="일부 리포트가 하반기 리스크 요인 지적.",
        source_count=4,
    ),
    ChecklistItem(
        id="chk-4",
        tag="neutral",
        headline="신규 라인 증설 계획 보도",
        description="사실 전달 성격. 중복 기사 다수 묶음.",
        source_count=2,
    ),
]

_DEFAULT_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        id="chk-1",
        tag="positive",
        headline="주요 거래처向 공급 확대 보도",
        description="관련 업계 매체에서 긍정적으로 평가.",
        source_count=3,
    ),
    ChecklistItem(
        id="chk-2",
        tag="earnings",
        headline="분기 실적 발표 예정",
        description="시장 컨센서스와 비교 필요.",
        source_count=4,
    ),
    ChecklistItem(
        id="chk-3",
        tag="caution",
        headline="업황 관련 유의 요인 언급",
        description="일부 자료가 리스크 요인으로 지적.",
        source_count=2,
    ),
]

_MOCK_ITEMS_BY_TICKER: dict[str, list[ChecklistItem]] = {
    "005930": _SAMSUNG_ITEMS,
}


def _classify_tag(text: str) -> ChecklistTag:
    if any(keyword in text for keyword in _EARNINGS_KEYWORDS):
        return "earnings"
    if any(keyword in text for keyword in _CAUTION_KEYWORDS):
        return "caution"
    if any(keyword in text for keyword in _POSITIVE_KEYWORDS):
        return "positive"
    return "neutral"


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


@lru_cache(maxsize=1)
def _load_news_by_ticker() -> dict[str, list[dict]]:
    try:
        with open(_NEWS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _cluster_by_title(articles: list[dict]) -> list[list[dict]]:
    """Groups near-duplicate headlines (same normalized leading text) into one issue.

    This is a cheap stand-in for real semantic clustering — good enough to collapse
    wire-service duplicates without needing an LLM/embedding call.
    """
    clusters: dict[str, list[dict]] = {}
    order: list[str] = []
    for article in articles:
        key = re.sub(r"\s+", "", article["title"])[:20]
        if key not in clusters:
            clusters[key] = []
            order.append(key)
        clusters[key].append(article)
    return [clusters[key] for key in order]


def _real_checklist(ticker: str) -> ChecklistResponse | None:
    articles = _load_news_by_ticker().get(ticker)
    if not articles:
        return None

    clusters = _cluster_by_title(articles)[:_MAX_ITEMS]
    items = [
        ChecklistItem(
            id=f"chk-{i}",
            tag=_classify_tag(f"{cluster[0]['title']} {cluster[0]['description']}"),
            headline=cluster[0]["title"],
            description=_truncate(cluster[0]["description"], _DESCRIPTION_LIMIT),
            source_count=len(cluster),
            url=cluster[0]["link"],
        )
        for i, cluster in enumerate(clusters, start=1)
    ]

    return ChecklistResponse(
        ticker=ticker,
        date=date.today().isoformat(),
        total_article_count=len(articles),
        items=items,
    )


def _mock_checklist(ticker: str) -> ChecklistResponse:
    items = _MOCK_ITEMS_BY_TICKER.get(ticker, _DEFAULT_ITEMS)
    return ChecklistResponse(
        ticker=ticker,
        date=date.today().isoformat(),
        total_article_count=sum(item.source_count for item in items),
        items=items,
    )


def get_today_checklist(ticker: str) -> ChecklistResponse:
    return _real_checklist(ticker) or _mock_checklist(ticker)
