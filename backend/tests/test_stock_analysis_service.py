from fastapi.testclient import TestClient

from app.main import app
from app.rules.watch_item_templates import generate_allowed_watch_items
from app.schemas.stock_analysis import (
    AllowedWatchItem,
    ChartCard,
    DetailPanel,
    DisclosureContext,
    LLMInputContext,
    MarketDataContext,
    MovementItem,
    NewsContext,
    PrimaryEvidence,
    QuickFact,
    QuickFactCandidate,
    RecommendedMaterial,
    StockAnalysisResult,
    WatchItem,
)
from app.services import market_data_service, stock_analysis_service

client = TestClient(app)


def _samsung_llm_input() -> LLMInputContext:
    """Mirrors the 삼성전자 2026-07-15 sample fixture from the task brief (section 14)."""
    disclosure = DisclosureContext(
        source_id="dart-001",
        title="단일판매·공급계약 체결",
        display_label="회사의 공급계약 공시",
        published_at="2026-07-15T10:20:00+09:00",
        excerpt="계약금액은 최근 사업연도 매출액 대비 8.4%에 해당합니다.",
        available_topics=["최근 사업연도 매출액 대비 계약금액 비율", "공시 원문에 기재된 계약의 세부 조건"],
    )
    news_hbm = NewsContext(
        source_id="news-001",
        title="삼성전자, HBM 공급 기대감에 강세",
        published_at="2026-07-15T11:30:00+09:00",
        description="삼성전자가 HBM 공급 기대와 외국인 매수세에 상승하고 있다.",
        available_topics=["언론이 언급한 HBM 공급 기대", "언론이 언급한 외국인 매수세"],
    )
    news_foreign = NewsContext(
        source_id="news-002",
        title="외국인 반도체주 집중 매수",
        published_at="2026-07-15T14:10:00+09:00",
        description="외국인이 삼성전자와 SK하이닉스를 중심으로 순매수했다.",
        available_topics=["언론이 언급한 외국인 반도체주 매수"],
    )
    allowed_watch_items = generate_allowed_watch_items([disclosure], [news_hbm, news_foreign])

    return LLMInputContext(
        ticker="005930",
        company_name="삼성전자",
        selected_date="2026-07-15",
        market_data=MarketDataContext(
            source_id="market-data",
            close=84200,
            price_change_text="+5.4%",
            change_percent=5.4,
            volume=24_150_000,
            volume_ratio_20d=2.3,
            volume_comparison_text="평소의 2.3배",
        ),
        quick_fact_candidates=[QuickFactCandidate(id="quick-001", label="거래량", value="평소의 2.3배")],
        disclosures=[disclosure],
        news=[news_hbm, news_foreign],
        allowed_watch_items=allowed_watch_items,
    )


def test_allowed_watch_items_generated_for_supply_contract_and_hbm():
    llm_input = _samsung_llm_input()
    titles = {item.title for item in llm_input.allowed_watch_items}

    assert "계약 내용이 실제 실적에 반영되는지" in titles
    assert "계약 내용이 변경되거나 취소되지 않는지" in titles
    assert "HBM 관련 회사의 공식 발표가 나오는지" in titles


def test_no_supply_contract_no_hbm_generates_no_watch_items():
    disclosure = DisclosureContext(
        source_id="dart-999",
        title="임원ㆍ주요주주특정증권등소유상황보고서",
        display_label="회사의 공시: 임원ㆍ주요주주특정증권등소유상황보고서",
        published_at="2026-07-15T00:00:00+09:00",
        excerpt="e",
        available_topics=["공시 원문에 기재된 세부 내용"],
    )
    news = NewsContext(
        source_id="news-100",
        title="시장 전반 강세",
        published_at="2026-07-15T00:00:00+09:00",
        description="코스피 전반이 강세를 보였다.",
        available_topics=["해당 내용이 공식 발표에 기반했는지 여부"],
    )
    assert generate_allowed_watch_items([disclosure], [news]) == []


def test_sanitize_drops_hallucinated_source_id_in_why_it_moved():
    llm_input = _samsung_llm_input()
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[],
            primary_evidence=None,
        ),
        detail_panel=DetailPanel(
            why_it_moved=[
                MovementItem(
                    title="t",
                    description="d",
                    status="confirmed",
                    evidence_type="official_disclosure",
                    evidence_level="high",
                    source_ids=["dart-001", "invented-id"],
                )
            ],
            what_to_watch=[],
            recommended_materials=[],
            caution="",
        ),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert sanitized.detail_panel.why_it_moved[0].source_ids == ["dart-001"]


def test_sanitize_drops_quick_fact_not_in_candidates():
    llm_input = _samsung_llm_input()
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[
                QuickFact(label="거래량", value="평소의 2.3배"),  # matches a candidate
                QuickFact(label="시가총액", value="500조원"),  # not a candidate -> invented
            ],
            primary_evidence=None,
        ),
        detail_panel=DetailPanel(why_it_moved=[], what_to_watch=[], recommended_materials=[], caution=""),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert len(sanitized.chart_card.quick_facts) == 1
    assert sanitized.chart_card.quick_facts[0].value == "평소의 2.3배"


def test_sanitize_drops_watch_item_not_matching_allowed_list():
    llm_input = _samsung_llm_input()
    fabricated = WatchItem(
        title="목표 주가가 도달하는지",  # not in allowed_watch_items and not template-derived
        description="d",
        signal_type="market_flow",
        source_ids=[],
    )
    real = WatchItem(
        title=llm_input.allowed_watch_items[0].title,
        description=llm_input.allowed_watch_items[0].description,
        signal_type=llm_input.allowed_watch_items[0].signal_type,
        source_ids=llm_input.allowed_watch_items[0].source_ids,
    )
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[],
            primary_evidence=None,
        ),
        detail_panel=DetailPanel(
            why_it_moved=[], what_to_watch=[fabricated, real], recommended_materials=[], caution=""
        ),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert len(sanitized.detail_panel.what_to_watch) == 1
    assert sanitized.detail_panel.what_to_watch[0].title == real.title


def test_sanitize_filters_information_to_verify_to_available_topics():
    llm_input = _samsung_llm_input()
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[],
            primary_evidence=None,
        ),
        detail_panel=DetailPanel(
            why_it_moved=[],
            what_to_watch=[],
            recommended_materials=[
                RecommendedMaterial(
                    source_id="dart-001",
                    description="d",
                    information_to_verify=[
                        "최근 사업연도 매출액 대비 계약금액 비율",  # valid topic
                        "존재하지 않는 주제",  # invented topic -> should be dropped
                    ],
                )
            ],
            caution="",
        ),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert sanitized.detail_panel.recommended_materials[0].information_to_verify == [
        "최근 사업연도 매출액 대비 계약금액 비율"
    ]


def test_sanitize_defaults_missing_caution():
    llm_input = _samsung_llm_input()
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[],
            primary_evidence=None,
        ),
        detail_panel=DetailPanel(why_it_moved=[], what_to_watch=[], recommended_materials=[], caution=""),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert sanitized.detail_panel.caution == stock_analysis_service.DEFAULT_CAUTION


def test_primary_evidence_relabeled_from_registry_not_trusted_from_llm():
    llm_input = _samsung_llm_input()
    result = StockAnalysisResult(
        chart_card=ChartCard(
            selected_date="2026-07-15",
            price_change_text="+5.4%",
            one_line_summary="s",
            quick_facts=[],
            primary_evidence=PrimaryEvidence(label="완전히 지어낸 라벨", source_id="dart-001"),
        ),
        detail_panel=DetailPanel(why_it_moved=[], what_to_watch=[], recommended_materials=[], caution=""),
    )

    sanitized = stock_analysis_service._sanitize_result(result, llm_input)

    assert sanitized.chart_card.primary_evidence.label == "회사의 공급계약 공시"


def test_fallback_result_uses_only_backend_data_no_llm_call():
    llm_input = _samsung_llm_input()
    result = stock_analysis_service._fallback_result(llm_input)

    assert result.chart_card.primary_evidence.source_id == "dart-001"
    assert result.detail_panel.why_it_moved[0].status == "confirmed"
    assert result.detail_panel.why_it_moved[0].evidence_type == "official_disclosure"
    assert len(result.detail_panel.what_to_watch) <= 3
    assert result.detail_panel.caution == stock_analysis_service.DEFAULT_CAUTION


def test_fallback_result_with_no_sources_returns_honest_empty_state():
    llm_input = LLMInputContext(
        ticker="005930",
        company_name="삼성전자",
        selected_date="2026-07-15",
        market_data=MarketDataContext(
            source_id="market-data",
            close=84200,
            price_change_text="+0.0%",
            change_percent=0.0,
            volume=1000,
        ),
        quick_fact_candidates=[],
        disclosures=[],
        news=[],
        allowed_watch_items=[],
    )

    result = stock_analysis_service._fallback_result(llm_input)

    assert result.chart_card.one_line_summary == stock_analysis_service.NO_DATA_SUMMARY
    assert result.detail_panel.why_it_moved == []
    assert result.chart_card.primary_evidence is None


def test_volume_ratio_text_is_multiplier_not_percent_increase():
    prices = market_data_service.get_price_series(market_data_service.SAMPLE_STOCKS[0].ticker)
    index = len(prices) - 1
    market_data = stock_analysis_service._build_market_data_context(prices, index)

    if market_data.volume_ratio_20d is not None:
        expected = f"평소의 {market_data.volume_ratio_20d:.1f}배"
        assert market_data.volume_comparison_text == expected
        assert "%" not in market_data.volume_comparison_text


def test_analyze_date_endpoint_returns_valid_shape():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    selected_date = market_data_service.get_price_series(ticker)[-1].time

    response = client.post("/api/analysis/date", json={"ticker": ticker, "selected_date": selected_date})

    assert response.status_code == 200
    body = response.json()
    assert "analysis" in body and "sources" in body
    assert "chart_card" in body["analysis"] and "detail_panel" in body["analysis"]


def test_analyze_date_unknown_ticker_returns_404():
    response = client.post("/api/analysis/date", json={"ticker": "999999", "selected_date": "2026-07-17"})
    assert response.status_code == 404
