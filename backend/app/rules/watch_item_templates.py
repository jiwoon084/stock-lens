"""Deterministic templates for detail_panel.what_to_watch candidates.

The LLM is never allowed to invent what_to_watch items (see
app/prompts/stock_analysis_system.txt) — it may only pick up to 3 items from the list this
module produces from the actual retrieved disclosures/news for the selected date. Initial MVP
covers one disclosure type (공급계약, i.e. a supply contract filing) plus one news-triggered
follow-up (HBM supply expectations), matching the sample fixture in
app/services/stock_analysis_service.py.
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

HBM_SUPPLY_EXPECTATION_WATCH_ITEM = {
    "title": "HBM 관련 회사의 공식 발표가 나오는지",
    "description": "현재는 언론의 기대가 중심이므로 회사의 공식 발표 여부를 확인하세요.",
    "signal_type": "official_confirmation",
}

_SUPPLY_CONTRACT_KEYWORD = "공급계약"
_HBM_KEYWORD = "HBM"


def _is_supply_contract(title: str) -> bool:
    return _SUPPLY_CONTRACT_KEYWORD in title


def _mentions_hbm(news: NewsContext) -> bool:
    return _HBM_KEYWORD in f"{news.title} {news.description}"


def generate_allowed_watch_items(
    disclosures: list[DisclosureContext],
    news: list[NewsContext],
) -> list[AllowedWatchItem]:
    items: list[AllowedWatchItem] = []
    counter = 1

    for disclosure in disclosures:
        if not _is_supply_contract(disclosure.title):
            continue
        for template in SUPPLY_CONTRACT_WATCH_ITEMS:
            items.append(
                AllowedWatchItem(
                    id=f"watch-{counter:03d}",
                    source_ids=[disclosure.source_id],
                    **template,
                )
            )
            counter += 1

    hbm_source_ids = [article.source_id for article in news if _mentions_hbm(article)]
    if hbm_source_ids:
        items.append(
            AllowedWatchItem(
                id=f"watch-{counter:03d}",
                source_ids=hbm_source_ids,
                **HBM_SUPPLY_EXPECTATION_WATCH_ITEM,
            )
        )

    return items
