from app.rules.watch_item_templates import generate_allowed_watch_items
from app.schemas.stock_analysis import DisclosureContext, NewsContext


def _disclosure(source_id: str, title: str) -> DisclosureContext:
    return DisclosureContext(
        source_id=source_id,
        title=title,
        display_label=f"회사의 공시: {title}",
        published_at="2026-07-15T00:00:00+09:00",
        excerpt="e",
        available_topics=["공시 원문에 기재된 세부 내용"],
    )


def _news(source_id: str, title: str, description: str) -> NewsContext:
    return NewsContext(
        source_id=source_id,
        title=title,
        published_at="2026-07-15T00:00:00+09:00",
        description=description,
        available_topics=["해당 내용이 공식 발표에 기반했는지 여부"],
    )


def test_self_stock_disposal_trigger_matches_real_title_pattern():
    disclosure = _disclosure("d-1", "주요사항보고서(자기주식처분결정)")
    items = generate_allowed_watch_items([disclosure], [])

    titles = {item.title for item in items}
    assert "자기주식 처분이 실제로 완료됐는지" in titles
    assert "처분 조건이 변경되지 않는지" in titles
    assert all(item.source_ids == ["d-1"] for item in items)


def test_rights_offering_trigger_matches_real_title_pattern():
    disclosure = _disclosure("d-2", "주요사항보고서(유상증자결정)")
    items = generate_allowed_watch_items([disclosure], [])

    assert [item.title for item in items] == ["신주 상장(배정) 일정이 예정대로 진행되는지"]


def test_preliminary_earnings_trigger_matches_parenthesized_real_title():
    """실제 공시 제목은 "영업(잠정)실적(공정공시)"처럼 '잠정'과 '실적' 사이에 괄호가 끼어
    있어 연속된 문자열이 아님 — 단순 substring 매칭이면 여기서 조용히 실패했을 케이스."""
    disclosure = _disclosure("d-3", "연결재무제표기준영업(잠정)실적(공정공시)")
    items = generate_allowed_watch_items([disclosure], [])

    assert [item.title for item in items] == ["정식 실적 발표에서 잠정치와 달라지는 부분이 있는지"]


def test_earnings_outlook_news_trigger():
    news = _news("n-1", "실적 기대감에 강세", "2분기 실적이 시장 전망을 상회할 것으로 보인다.")
    items = generate_allowed_watch_items([], [news])

    assert [item.title for item in items] == ["실적 전망 보도가 실제 공시로 이어지는지"]
    assert items[0].source_ids == ["n-1"]


def test_unrelated_disclosure_and_news_generate_no_items():
    disclosure = _disclosure("d-4", "임원ㆍ주요주주특정증권등소유상황보고서")
    news = _news("n-2", "시장 전반 강세", "코스피 전반이 강세를 보였다.")

    assert generate_allowed_watch_items([disclosure], [news]) == []


def test_unrelated_earnings_report_title_does_not_false_positive():
    """'증권발행실적보고서'는 '실적'을 포함하지만 회사 경영 실적이 아니라 증권 발행 절차
    보고서라 — '잠정'이 없으니 잠정실적 트리거는 걸리면 안 된다."""
    disclosure = _disclosure("d-5", "증권발행실적보고서")

    assert generate_allowed_watch_items([disclosure], []) == []
