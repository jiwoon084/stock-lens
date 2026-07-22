import pytest
from pydantic import ValidationError

from app.schemas.stock_analysis import (
    ChartCard,
    DetailPanel,
    MovementItem,
    QuickFact,
    RecommendedMaterial,
    StockAnalysisResult,
    WatchItem,
)


def _chart_card(**overrides) -> ChartCard:
    defaults = dict(
        selected_date="2026-07-15",
        price_change_text="+5.4%",
        one_line_summary="공급계약 공시와 평소보다 많은 거래가 함께 확인됐어요.",
        quick_facts=[QuickFact(label="거래량", value="평소의 2.3배")],
        primary_evidence=None,
    )
    defaults.update(overrides)
    return ChartCard(**defaults)


def test_valid_result_parses():
    result = StockAnalysisResult(
        chart_card=_chart_card(),
        detail_panel=DetailPanel(why_it_moved=[], what_to_watch=[], recommended_materials=[], caution="주의 문구"),
    )
    assert result.chart_card.one_line_summary.startswith("공급계약")


def test_primary_evidence_null_is_allowed():
    card = _chart_card(primary_evidence=None)
    assert card.primary_evidence is None


def test_invalid_status_enum_rejected():
    with pytest.raises(ValidationError):
        MovementItem(
            title="t",
            description="d",
            status="maybe",  # not a valid MovementStatus
            evidence_type="official_disclosure",
            evidence_level="high",
            source_ids=[],
        )


def test_invalid_signal_type_enum_rejected():
    with pytest.raises(ValidationError):
        WatchItem(title="t", description="d", signal_type="not_a_real_signal", source_ids=[])


def test_quick_facts_max_length_enforced():
    with pytest.raises(ValidationError):
        _chart_card(
            quick_facts=[
                QuickFact(label="a", value="1"),
                QuickFact(label="b", value="2"),
                QuickFact(label="c", value="3"),
            ]
        )


def test_why_it_moved_max_length_enforced():
    item = MovementItem(
        title="t",
        description="d",
        status="confirmed",
        evidence_type="official_disclosure",
        evidence_level="high",
        source_ids=[],
    )
    with pytest.raises(ValidationError):
        DetailPanel(why_it_moved=[item, item, item], what_to_watch=[], recommended_materials=[], caution="c")


def test_information_to_verify_max_length_enforced():
    with pytest.raises(ValidationError):
        RecommendedMaterial(source_id="dart-001", description="d", information_to_verify=["a", "b", "c", "d"])


def test_volume_ratio_text_preserved_verbatim():
    card = _chart_card(quick_facts=[QuickFact(label="거래량", value="평소의 2.3배")])
    assert card.quick_facts[0].value == "평소의 2.3배"
