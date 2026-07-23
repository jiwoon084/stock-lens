"""Document retrieval backed by real DART disclosures.

Reads data/disclosures.json (produced by data/step1_corpcode.py + data/step2_disclosures.py,
run manually with a real DART_API_KEY — see docs/project-plan.md M2). If that file is entirely
missing (e.g. a teammate/CI without a DART_API_KEY, or Docker where data/ isn't copied into the
image), falls back to canned mock sources so the API stays usable; if the file loaded fine but
this specific ticker just has no matching disclosures, returns an honest empty list instead of
inventing evidence.
"""

import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import requests

from app.core.config import settings
from app.schemas.explanation import Source
from app.services import embedding_client

DOCUMENT_URL = "https://opendart.fss.or.kr/api/document.xml"
EXCERPT_LENGTH = 400
MAX_SOURCES = 5
DISCLOSURE_SLOTS = 3  # MAX_SOURCES 중 공시에 우선 배정하는 자리 수 — 나머지는 뉴스, 한쪽이 모자라면 상대가 채움

_MOCK_PUBLISHERS = ["샘플 경제신문", "샘플 증권리서치", "샘플 뉴스와이어"]


def _find_data_file(filename: str) -> Path | None:
    """Locate a file under data/ relative to this file.

    The number of parent directories between this file and the repo root differs between
    local dev (backend/app/services/..., 3 levels up) and Docker (WORKDIR /app, data/ mounted
    at /app/data, 2 levels up) — walk up a few levels instead of hardcoding one.
    """
    here = Path(__file__).resolve()
    for parent in here.parents[:6]:
        candidate = parent / "data" / filename
        if candidate.exists():
            return candidate
    return None


# Routine/administrative DART filing types that are frequent but rarely explain a price move
# (e.g. an individual executive reporting a small personal stock trade). Deprioritized, not
# discarded — every disclosure stays in data/disclosures.json and is still retrievable; this
# list only controls which ones surface first when picking the top MAX_SOURCES for a given date.
_ROUTINE_PATTERNS = [
    "임원ㆍ주요주주특정증권등소유상황보고서",
    "주식매수선택권부여에관한신고",
    "기업설명회",
    "대규모기업집단현황공시",
    "지속가능경영보고서",
    "기업지배구조보고서",
    "동일인등출자계열회사",
    "특수관계인",
]
_BRACKET_PREFIX = re.compile(r"^\[.*?\]")


def _is_routine(report_nm: str) -> bool:
    base = _BRACKET_PREFIX.sub("", report_nm)
    return any(pattern in base for pattern in _ROUTINE_PATTERNS)


@lru_cache(maxsize=1)
def _load_disclosures_by_ticker() -> dict[str, list[dict]]:
    path = _find_data_file("disclosures.json")
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))

    by_ticker: dict[str, list[dict]] = {}
    for entries in raw.values():
        for entry in entries:
            ticker = entry.get("stock_code")
            if not ticker:
                continue
            by_ticker.setdefault(ticker, []).append(entry)
    return by_ticker


@lru_cache(maxsize=1)
def _load_major_events_by_rcept_no() -> dict[str, dict]:
    """rcept_no -> structured event record from data/step3_major_events.py's output.

    Covers report types DART exposes as clean structured fields (자기주식취득/처분결정,
    유상증자결정) instead of free text — when a disclosure has one, it's a much better excerpt
    source than scraping/stripping document.xml.
    """
    path = _find_data_file("major_events.json")
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _format_structured_excerpt(event: dict) -> str | None:
    event_type = event.get("event_type")

    if event_type == "자기주식처분결정":
        return (
            f"처분목적: {event.get('dp_pp', '-')} / "
            f"처분주식수: {event.get('dppln_stk_ostk', '-')}주 / "
            f"처분가액: 1주당 {event.get('dpstk_prc_ostk', '-')}원, "
            f"총 {event.get('dppln_prc_ostk', '-')}원 / "
            f"처분기간: {event.get('dpprpd_bgd', '-')} ~ {event.get('dpprpd_edd', '-')}"
        )

    if event_type == "유상증자결정":
        purpose_fields = {
            "시설자금": event.get("fdpp_fclt"),
            "영업양수자금": event.get("fdpp_bsninh"),
            "운영자금": event.get("fdpp_op"),
            "채무상환자금": event.get("fdpp_dtrp"),
            "타법인증권취득자금": event.get("fdpp_ocsa"),
            "기타자금": event.get("fdpp_etc"),
        }
        purposes = ", ".join(f"{label} {amount}원" for label, amount in purpose_fields.items() if amount and amount != "-")
        return (
            f"증자방식: {event.get('ic_mthn', '-')} / "
            f"신주 수: {event.get('nstk_ostk_cnt', '-')}주 (1주당 액면가 {event.get('fv_ps', '-')}원) / "
            f"자금 조달 목적: {purposes or '-'}"
        )

    return None


def _extract_from_dart_xml(raw: str) -> str | None:
    """Structured extraction for DART's own dart4.xsd XML documents: skip the BODY's COVER
    child (submission-letter boilerplate — company name, CEO, address, identical for every
    filing) and keep the actual report sections after it.
    """
    root = ET.fromstring(raw)  # raises ET.ParseError if not well-formed XML
    body = root.find("BODY")
    if body is None:
        return None

    parts = [
        text.strip()
        for section in body
        if section.tag != "COVER"
        for text in section.itertext()
        if text.strip()
    ]
    text = re.sub(r"\s+", " ", " ".join(parts)).strip()
    return text or None


def _extract_from_html(raw: str) -> str | None:
    """Some filings (observed for KIND/거래소-routed report types like 생산중단, 잠정실적) come
    back as plain HTML instead of DART's XML schema — ElementTree can't parse that as XML at
    all. Fall back to a lenient regex tag-strip; there's no COVER/BODY structure to skip here,
    so this may include some page furniture, but it's still real disclosed text.
    """
    text = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


@lru_cache(maxsize=256)
def _fetch_document_excerpt(rcept_no: str) -> str | None:
    """Fetch a disclosure's real body text via DART's document.xml API. Returns None on any
    failure so callers can fall back — a missing key, a network hiccup, a malformed document,
    or an unrecognized format should never break the response.
    """
    if not settings.dart_api_key:
        return None

    try:
        response = requests.get(
            DOCUMENT_URL,
            params={"crtfc_key": settings.dart_api_key, "rcept_no": rcept_no},
            timeout=5,
        )
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            raw = zf.read(zf.namelist()[0]).decode("utf-8")
    except Exception:
        return None

    try:
        text = _extract_from_dart_xml(raw)
    except Exception:
        text = None

    if text is None:
        text = _extract_from_html(raw)

    return text[:EXCERPT_LENGTH] if text else None


def _to_source(entry: dict) -> Source:
    rcept_dt = entry["rcept_dt"]  # "YYYYMMDD"
    published_at = f"{rcept_dt[0:4]}-{rcept_dt[4:6]}-{rcept_dt[6:8]}T00:00:00+09:00"
    rcept_no = entry["rcept_no"]

    structured_event = _load_major_events_by_rcept_no().get(rcept_no)
    structured_excerpt = _format_structured_excerpt(structured_event) if structured_event else None

    excerpt = (
        structured_excerpt
        or _fetch_document_excerpt(rcept_no)
        or f"{entry['flr_nm']}이(가) 제출한 '{entry['report_nm']}' 공시입니다."
    )

    return Source(
        id=rcept_no,
        type="disclosure",
        title=entry["report_nm"],
        publisher=f"DART · {entry['flr_nm']}",
        published_at=published_at,
        url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
        excerpt=excerpt,
    )


@lru_cache(maxsize=1)
def _load_news_by_ticker() -> dict[str, list[dict]]:
    path = _find_data_file("news.json")
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _news_pub_date(article: dict) -> date | None:
    try:
        return parsedate_to_datetime(article["pub_date"]).date()
    except (KeyError, ValueError, TypeError):
        return None


def _news_to_source(article: dict, index: int) -> Source:
    pub_date = _news_pub_date(article)
    published_at = f"{pub_date.isoformat()}T00:00:00+09:00" if pub_date else ""
    domain = urlparse(article["link"]).netloc.removeprefix("www.")

    return Source(
        id=f"news-{index}",
        type="news",
        title=article["title"],
        publisher=domain or "네이버 뉴스",
        published_at=published_at,
        url=article["link"],
        excerpt=article["description"],
    )


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


def _source_date_distance(source: Source, target: date) -> int:
    if not source.published_at:
        return 10_000
    return abs((date.fromisoformat(source.published_at[:10]) - target).days)


# ---- semantic reranking (SOLAR embeddings) --------------------------------------------------
#
# Disclosures/news are still fetched and pre-filtered exactly as before (routine-deprioritized,
# date-window matched). This layer only reorders the resulting candidates by how semantically
# close their *title* (disclosures) or *title+description* (news) is to the selected date's
# price movement — using the document body would need one live document.xml fetch per
# candidate, which is too expensive to do for every candidate just to rank them.
#
# If SOLAR_API_KEY is unset or any embedding call fails, _semantic_scores returns None and
# callers fall back to the original date-only rank_key functions below, unchanged.

_DIRECTION_KO = {"up": "상승", "down": "하락", "flat": "보합"}


def _build_movement_query(ticker: str, selected_date: str, direction: str) -> str:
    return f"{ticker} 종목의 {selected_date} 주가 {_DIRECTION_KO.get(direction, '변동')} 관련 소식"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom else 0.0


@lru_cache(maxsize=256)
def _cached_passage_embedding(text: str) -> tuple[float, ...]:
    return tuple(embedding_client.embed_passage(text))


@lru_cache(maxsize=64)
def _cached_query_embedding(query: str) -> tuple[float, ...]:
    return tuple(embedding_client.embed_query(query))


def _semantic_scores(query: str, texts: tuple[str, ...]) -> tuple[float, ...] | None:
    """One cosine-similarity score per text in `texts`, or None if embeddings are unavailable."""
    if not texts:
        return ()
    try:
        query_vec = list(_cached_query_embedding(query))
    except embedding_client.EmbeddingApiError:
        return None

    scores = []
    for text in texts:
        try:
            passage_vec = list(_cached_passage_embedding(text))
        except embedding_client.EmbeddingApiError:
            scores.append(0.0)
            continue
        scores.append(max(0.0, _cosine_similarity(query_vec, passage_vec)))
    return tuple(scores)


def _date_proximity_score(delta_days: int) -> float:
    return 1.0 / (1.0 + abs(delta_days))


def get_related_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    disclosures_by_ticker = _load_disclosures_by_ticker()
    news_by_ticker = _load_news_by_ticker()

    if not disclosures_by_ticker and not news_by_ticker:
        return _mock_documents(ticker, selected_date, direction)

    disclosure_entries = disclosures_by_ticker.get(ticker, [])
    news_entries = news_by_ticker.get(ticker, [])
    if not disclosure_entries and not news_entries:
        return []

    target = date.fromisoformat(selected_date)

    def disclosure_rank_key(entry: dict) -> tuple[bool, int, int]:
        entry_date = datetime.strptime(entry["rcept_dt"], "%Y%m%d").date()
        delta = (entry_date - target).days
        return (_is_routine(entry["report_nm"]), 0 if delta <= 0 else 1, abs(delta))

    def news_rank_key(article: dict) -> tuple[int, int]:
        pub_date = _news_pub_date(article)
        if pub_date is None:
            return (1, 10_000)
        delta = (pub_date - target).days
        return (0 if delta <= 0 else 1, abs(delta))

    query = _build_movement_query(ticker, selected_date, direction)
    disclosure_semantic = _semantic_scores(query, tuple(e["report_nm"] for e in disclosure_entries))
    news_semantic = _semantic_scores(
        query, tuple(f'{a["title"]} {a["description"]}' for a in news_entries)
    )

    if disclosure_semantic is None:
        ranked_disclosures = sorted(disclosure_entries, key=disclosure_rank_key)
    else:

        def disclosure_hybrid_key(pair: tuple[int, dict]) -> tuple[bool, float]:
            index, entry = pair
            entry_date = datetime.strptime(entry["rcept_dt"], "%Y%m%d").date()
            delta = (entry_date - target).days
            hybrid = 0.5 * _date_proximity_score(delta) + 0.5 * disclosure_semantic[index]
            return (_is_routine(entry["report_nm"]), -hybrid)

        ranked_disclosures = [e for _, e in sorted(enumerate(disclosure_entries), key=disclosure_hybrid_key)]

    if news_semantic is None:
        ranked_news = sorted(news_entries, key=news_rank_key)
    else:

        def news_hybrid_key(pair: tuple[int, dict]) -> float:
            index, article = pair
            pub_date = _news_pub_date(article)
            date_score = _date_proximity_score((pub_date - target).days) if pub_date else 0.0
            return -(0.5 * date_score + 0.5 * news_semantic[index])

        ranked_news = [a for _, a in sorted(enumerate(news_entries), key=news_hybrid_key)]

    # 공시 DISCLOSURE_SLOTS개 + 뉴스 나머지를 기본 배정으로 하되, 한쪽이 모자라면 그만큼 상대에게 넘김.
    disclosure_slots = min(DISCLOSURE_SLOTS, len(ranked_disclosures))
    news_slots = min(MAX_SOURCES - disclosure_slots, len(ranked_news))
    disclosure_slots = min(MAX_SOURCES - news_slots, len(ranked_disclosures))

    sources = [_to_source(entry) for entry in ranked_disclosures[:disclosure_slots]]
    sources += [_news_to_source(article, index) for index, article in enumerate(ranked_news[:news_slots])]

    # 공시·뉴스를 합친 뒤 선택 날짜와 가까운 순으로 다시 정렬 — 가장 관련 있는 근거가 앞에 오게.
    sources.sort(key=lambda source: _source_date_distance(source, target))
    return sources
