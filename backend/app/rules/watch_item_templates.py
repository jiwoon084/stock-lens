"""Deterministic templates for detail_panel.what_to_watch candidates.

The LLM is never allowed to invent what_to_watch items (see
app/prompts/stock_analysis_system.txt) — it may only pick up to 3 items from the list this
module produces from the actual retrieved disclosures/news for the selected date.

Coverage was originally limited to one disclosure type (공급계약) plus one news-triggered
follow-up (HBM), matching a task-brief sample fixture — not real disclosure frequency. Checking
against the actual collected data (data/disclosures.json, data/major_events.json, data/news.json)
found that "공급계약" never once appears in real disclosure titles, so that rule could never fire
outside the test fixture. This revision adds three more disclosure triggers and one more news
trigger chosen by real frequency in that data instead of guessing.
"""

from app.schemas.stock_analysis import AllowedWatchItem, DisclosureContext, NewsContext

SUPPLY_CONTRACT_WATCH_ITEMS = [
    {
        "title": "계약 내용이 실제 실적에 반영되는지",
        "description": "다음 실적 발표에서 계약 관련 매출이 확인되는지 살펴보세요.",
        "signal_type": "business_result",
    },
    {
        "title": "계약 내용이 변경되거나 취소되지 않는지",
        "description": "이후 정정공시나 계약 변경 공시가 나오는지 확인하세요.",
        "signal_type": "follow_up_disclosure",
    },
]

SELF_STOCK_DISPOSAL_WATCH_ITEMS = [
    {
        "title": "자기주식 처분이 실제로 완료됐는지",
        "description": "처분 결과보고서가 나오는지, 공시된 수량·기간대로 진행되는지 확인하세요.",
        "signal_type": "follow_up_disclosure",
    },
    {
        "title": "처분 조건이 변경되지 않는지",
        "description": "처분 가격이나 수량이 정정공시로 바뀌는지 확인하세요.",
        "signal_type": "follow_up_disclosure",
    },
]

RIGHTS_OFFERING_WATCH_ITEMS = [
    {
        "title": "신주 상장(배정) 일정이 예정대로 진행되는지",
        "description": "발행가액 확정, 신주 배정일·상장일이 공시된 일정대로 진행되는지 확인하세요.",
        "signal_type": "follow_up_disclosure",
    },
]

PRELIMINARY_EARNINGS_WATCH_ITEMS = [
    {
        "title": "정식 실적 발표에서 잠정치와 달라지는 부분이 있는지",
        "description": "정기보고서(분기·반기·사업보고서)에서 확정 수치가 잠정치와 얼마나 다른지 확인하세요.",
        "signal_type": "business_result",
    },
]

HBM_SUPPLY_EXPECTATION_WATCH_ITEM = {
    "title": "HBM 관련 회사의 공식 발표가 나오는지",
    "description": "현재는 언론의 기대가 중심이므로 회사의 공식 발표 여부를 확인하세요.",
    "signal_type": "official_confirmation",
}

EARNINGS_OUTLOOK_NEWS_WATCH_ITEM = {
    "title": "실적 전망 보도가 실제 공시로 이어지는지",
    "description": "언론의 실적 전망이 회사의 공식 실적 공시로 확인되는지 살펴보세요.",
    "signal_type": "official_confirmation",
}

# (제목에 포함된 키워드, 매칭 시 추가할 템플릿들) — 실제 disclosures.json에 연속된 문자열로
# 나타나는 것만 키워드로 씀. "공급계약"은 실제 데이터에 0건이지만 기존 테스트 픽스처가
# 참조하고 있어 그대로 둠.
_DISCLOSURE_KEYWORD_TRIGGERS: list[tuple[str, list[dict]]] = [
    ("공급계약", SUPPLY_CONTRACT_WATCH_ITEMS),
    ("자기주식처분", SELF_STOCK_DISPOSAL_WATCH_ITEMS),
    ("유상증자", RIGHTS_OFFERING_WATCH_ITEMS),
]

_NEWS_KEYWORD_TRIGGERS: list[tuple[str, dict]] = [
    ("HBM", HBM_SUPPLY_EXPECTATION_WATCH_ITEM),
    ("실적", EARNINGS_OUTLOOK_NEWS_WATCH_ITEM),
]


def _is_preliminary_earnings(title: str) -> bool:
    """공시 제목이 "영업(잠정)실적(공정공시)"처럼 '잠정'과 '실적' 사이에 괄호가 끼어 있어
    하나의 연속된 문자열로 안 붙어있음 — 그래서 "(잠정)실적" 같은 고정 문자열이 아니라 두
    단어가 각각 들어있는지 따로 확인한다(괄호 위치가 바뀌어도 안 깨짐).
    """
    return "잠정" in title and "실적" in title


def generate_allowed_watch_items(
    disclosures: list[DisclosureContext],
    news: list[NewsContext],
) -> list[AllowedWatchItem]:
    items: list[AllowedWatchItem] = []
    counter = 1

    for disclosure in disclosures:
        matched_templates: list[dict] = []
        for keyword, templates in _DISCLOSURE_KEYWORD_TRIGGERS:
            if keyword in disclosure.title:
                matched_templates.extend(templates)
        if _is_preliminary_earnings(disclosure.title):
            matched_templates.extend(PRELIMINARY_EARNINGS_WATCH_ITEMS)

        for template in matched_templates:
            items.append(AllowedWatchItem(id=f"watch-{counter:03d}", source_ids=[disclosure.source_id], **template))
            counter += 1

    for keyword, template in _NEWS_KEYWORD_TRIGGERS:
        source_ids = [article.source_id for article in news if keyword in f"{article.title} {article.description}"]
        if source_ids:
            items.append(AllowedWatchItem(id=f"watch-{counter:03d}", source_ids=source_ids, **template))
            counter += 1

    return items
