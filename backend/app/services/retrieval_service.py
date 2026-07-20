"""Document retrieval backed by real DART disclosures.

Reads data/disclosures.json (produced by data/step1_corpcode.py + data/step2_disclosures.py,
run manually with a real DART_API_KEY — see docs/project-plan.md M2). Falls back to an empty
list if that file doesn't exist yet (e.g. in Docker, where data/ isn't copied into the image),
so the API stays usable without crashing — the response will just have no sources for that case.
"""

import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import requests

from app.core.config import settings
from app.schemas.explanation import Source

DOCUMENT_URL = "https://opendart.fss.or.kr/api/document.xml"
EXCERPT_LENGTH = 400

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


MAX_SOURCES = 5

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
            by_ticker.setdefault(entry["stock_code"], []).append(entry)
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


def get_related_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    entries = _load_disclosures_by_ticker().get(ticker, [])
    if not entries:
        return []

    target = date.fromisoformat(selected_date)

    def rank_key(entry: dict) -> tuple[bool, int]:
        entry_date = datetime.strptime(entry["rcept_dt"], "%Y%m%d").date()
        distance = abs((entry_date - target).days)
        return (_is_routine(entry["report_nm"]), distance)

    ranked = sorted(entries, key=rank_key)[:MAX_SOURCES]
    return [_to_source(entry) for entry in ranked]
