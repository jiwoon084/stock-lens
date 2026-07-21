"""Document retrieval for movement explanations.

Reads the locally collected `data/disclosures.json` (see data/step2_disclosures.py)
for real DART disclosures near the selected date. That file is gitignored — it's
collected with a personal Open DART API key and never committed — so teammates or
CI running without it transparently fall back to the previous mock documents. The
response shape is identical either way, so downstream code (LLM service, schema)
never needs to know which path served it.
"""

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.schemas.explanation import Source

_DISCLOSURES_PATH = Path(__file__).resolve().parents[3] / "data" / "disclosures.json"
_MAX_RESULTS = 3

_MOCK_PUBLISHERS = ["샘플 경제신문", "샘플 증권리서치", "샘플 뉴스와이어"]


@lru_cache(maxsize=1)
def _load_disclosures_by_ticker() -> dict[str, list[dict]]:
    try:
        with open(_DISCLOSURES_PATH, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    by_ticker: dict[str, list[dict]] = {}
    for entries in raw.values():
        for entry in entries:
            ticker = entry.get("stock_code")
            if not ticker:
                continue
            by_ticker.setdefault(ticker, []).append(entry)
    return by_ticker


def _entry_date(entry: dict) -> date:
    rcept_dt = entry["rcept_dt"]  # "YYYYMMDD"
    return date(int(rcept_dt[:4]), int(rcept_dt[4:6]), int(rcept_dt[6:]))


def _disclosure_to_source(entry: dict) -> Source:
    entry_date = _entry_date(entry)
    title = entry["report_nm"].strip()
    return Source(
        id=entry["rcept_no"],
        type="disclosure",
        title=title,
        publisher=entry.get("flr_nm", "DART 전자공시").strip(),
        published_at=f"{entry_date.isoformat()}T00:00:00+09:00",
        url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={entry['rcept_no']}",
        excerpt=f"{title} 공시 원문은 DART 전자공시시스템에서 확인할 수 있습니다.",
    )


def _closest_disclosures(entries: list[dict], selected_date: str) -> list[dict]:
    target = date.fromisoformat(selected_date)

    def sort_key(entry: dict) -> tuple[int, int]:
        delta = (_entry_date(entry) - target).days
        return (0 if delta <= 0 else 1, abs(delta))

    return sorted(entries, key=sort_key)[:_MAX_RESULTS]


def _mock_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    tone = "긍정적인" if direction == "up" else "부정적인" if direction == "down" else "중립적인"

    return [
        Source(
            id="source-1",
            type="news",
            title=f"{ticker} 관련 {tone} 시장 반응 기사",
            publisher=_MOCK_PUBLISHERS[0],
            published_at=f"{selected_date}T09:20:00+09:00",
            url="https://example.com/news/1",
            excerpt=f"{selected_date} 전후로 {tone} 수급 변화가 관찰되었다는 내용입니다.",
        ),
        Source(
            id="source-2",
            type="report",
            title=f"{ticker} 업종 전망 리포트",
            publisher=_MOCK_PUBLISHERS[1],
            published_at=f"{selected_date}T08:00:00+09:00",
            url="https://example.com/report/1",
            excerpt="업황 및 실적 전망에 대한 애널리스트 의견을 요약한 리포트 발췌입니다.",
        ),
        Source(
            id="source-3",
            type="disclosure",
            title=f"{ticker} 공시 요약",
            publisher=_MOCK_PUBLISHERS[2],
            published_at=f"{selected_date}T16:00:00+09:00",
            url="https://example.com/disclosure/1",
            excerpt="공개된 공시 자료 중 가격 변동과 관련될 수 있는 항목 발췌입니다.",
        ),
    ]


def get_related_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    entries = _load_disclosures_by_ticker().get(ticker, [])
    if not entries:
        return _mock_documents(ticker, selected_date, direction)

    return [_disclosure_to_source(entry) for entry in _closest_disclosures(entries, selected_date)]
