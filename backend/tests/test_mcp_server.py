"""Tests for mcp_server.py's tool functions — plain Python calls, not over the MCP protocol
(that's covered by manual verification with the real stdio client, see mcp_server.py's
docstring). Requires the `mcp` package, which lives only in backend/.venv-mcp, never in the
main backend/.venv that runs CI — importorskip keeps this file a no-op (skipped, not failed)
under the main venv instead of breaking collection for the whole suite.

Run with: backend/.venv-mcp/Scripts/python.exe -m pytest tests/test_mcp_server.py
"""

from unittest.mock import patch

import pytest

pytest.importorskip("mcp")

from app.schemas.explanation import Source  # noqa: E402
from app.schemas.stock import PricePoint, Stock  # noqa: E402
from app.schemas.stock_analysis import ChartCard, DetailPanel, StockAnalysisResponse, StockAnalysisResult  # noqa: E402

import mcp_server  # noqa: E402


def _price_point(time: str, change_percent: float = 0.0) -> PricePoint:
    return PricePoint(
        time=time, open=100.0, high=110.0, low=90.0, close=105.0, volume=1000,
        change_percent=change_percent, volume_change_percent=0.0,
    )


def test_get_price_series_returns_recent_rows_only():
    prices = [_price_point(f"2026-01-{d:02d}") for d in range(1, 11)]
    with patch.object(mcp_server.data_gateway, "get_stock", return_value=Stock(ticker="005930", name="삼성전자", market="KOSPI")), \
         patch.object(mcp_server.market_data_service, "get_price_series", return_value=prices):
        result = mcp_server.get_price_series("005930", limit=3)

    assert [p["time"] for p in result] == ["2026-01-08", "2026-01-09", "2026-01-10"]


def test_get_price_series_raises_on_unknown_ticker():
    with patch.object(mcp_server.data_gateway, "get_stock", return_value=None):
        with pytest.raises(ValueError, match="Unknown ticker"):
            mcp_server.get_price_series("999999")


def test_search_disclosures_and_news_derives_direction_from_prices():
    source = Source(
        id="dart-1", type="disclosure", title="공시", publisher="DART",
        published_at="2026-01-10T00:00:00+09:00", url="https://dart.fss.or.kr/x", excerpt="...",
    )
    with patch.object(mcp_server.data_gateway, "get_stock", return_value=Stock(ticker="005930", name="삼성전자", market="KOSPI")), \
         patch.object(mcp_server.data_gateway, "get_price_series_with_live_today", return_value=[_price_point("2026-01-10", change_percent=-2.0)]), \
         patch.object(mcp_server.data_gateway, "get_related_documents", return_value=[source]) as mock_search:
        result = mcp_server.search_disclosures_and_news("005930", "2026-01-10")

    mock_search.assert_called_once_with(ticker="005930", selected_date="2026-01-10", direction="down")
    assert result[0]["id"] == "dart-1"


def test_analyze_stock_movement_delegates_to_service():
    fake_result = StockAnalysisResult(
        chart_card=ChartCard(selected_date="2026-01-10", price_change_text="+1.0%", one_line_summary="s", quick_facts=[]),
        detail_panel=DetailPanel(why_it_moved=[], what_to_watch=[], recommended_materials=[], caution="c"),
    )
    fake_response = StockAnalysisResponse(analysis=fake_result, sources={})

    with patch.object(mcp_server.stock_analysis_service, "analyze_date", return_value=fake_response) as mock_analyze:
        result = mcp_server.analyze_stock_movement("005930", "2026-01-10")

    mock_analyze.assert_called_once_with("005930", "2026-01-10")
    assert result["analysis"]["chart_card"]["one_line_summary"] == "s"
