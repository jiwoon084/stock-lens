from unittest.mock import Mock, patch

import pytest

from app.core.config import settings
from app.services import krx_price_client, market_data_service


@pytest.fixture(autouse=True)
def _reset_krx_state():
    """Every test starts with no key configured and a clean per-day cache, regardless of
    what an earlier test set — `settings` and `_cached_fetch`'s cache are both process-wide.
    """
    original_key = settings.krx_api_key
    settings.krx_api_key = ""
    krx_price_client._cached_fetch.cache_clear()
    yield
    settings.krx_api_key = original_key
    krx_price_client._cached_fetch.cache_clear()


def _fake_response(*, result_code="00", items=None):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        "response": {
            "header": {"resultCode": result_code, "resultMsg": "NORMAL SERVICE."},
            "body": {"items": {"item": items or []}},
        }
    }
    return response


def _sample_item(bas_dt: str, close: float, volume: int, flt_rt: float):
    return {
        "basDt": bas_dt,
        "srtnCd": "005930",
        "itmsNm": "삼성전자",
        "mkp": close - 100,
        "hipr": close + 200,
        "lopr": close - 200,
        "clpr": close,
        "vs": 100,
        "fltRt": flt_rt,
        "trqu": volume,
        "mrktCtg": "KOSPI",
    }


def test_get_price_series_without_key_returns_mock():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker

    assert not settings.krx_api_key
    assert market_data_service.get_price_series(ticker) == market_data_service._generate_mock_price_series(
        ticker
    )


def test_to_price_points_maps_sorts_and_computes_volume_change():
    items = (
        _sample_item("20260716", close=84000.0, volume=1_000_000, flt_rt=1.0),
        _sample_item("20260715", close=83000.0, volume=800_000, flt_rt=-0.5),
    )  # deliberately out of order

    points = krx_price_client._to_price_points(items)

    assert [p.time for p in points] == ["2026-07-15", "2026-07-16"]
    assert points[0].close == 83000.0
    assert points[0].change_percent == -0.5
    assert points[0].volume_change_percent == 0.0  # no prior row to compare against
    assert points[1].volume == 1_000_000
    assert points[1].volume_change_percent == 25.0  # (1_000_000 - 800_000) / 800_000 * 100


def test_fetch_price_series_success_drops_baseline_row():
    settings.krx_api_key = "test-key"
    items = [
        _sample_item("20260714", close=82000.0, volume=700_000, flt_rt=0.2),
        _sample_item("20260715", close=83000.0, volume=800_000, flt_rt=-0.5),
        _sample_item("20260716", close=84000.0, volume=1_000_000, flt_rt=1.0),
    ]

    with patch.object(krx_price_client.requests, "get", return_value=_fake_response(items=items)):
        points = krx_price_client.fetch_price_series("005930")

    # The 07-14 row only existed to give 07-15 a volume baseline; it shouldn't appear in the output.
    assert [p.time for p in points] == ["2026-07-15", "2026-07-16"]


def test_market_data_service_falls_back_to_mock_on_api_error():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    settings.krx_api_key = "test-key"

    with patch.object(krx_price_client.requests, "get", side_effect=ConnectionError("boom")):
        result = market_data_service.get_price_series(ticker)

    assert result == market_data_service._generate_mock_price_series(ticker)


def test_market_data_service_falls_back_to_mock_on_bad_result_code():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    settings.krx_api_key = "test-key"

    with patch.object(
        krx_price_client.requests, "get", return_value=_fake_response(result_code="99", items=[])
    ):
        result = market_data_service.get_price_series(ticker)

    assert result == market_data_service._generate_mock_price_series(ticker)


def test_market_data_service_uses_real_client_when_key_and_data_present():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    settings.krx_api_key = "test-key"
    items = [
        _sample_item("20260714", close=82000.0, volume=700_000, flt_rt=0.2),
        _sample_item("20260715", close=83000.0, volume=800_000, flt_rt=-0.5),
    ]

    with patch.object(krx_price_client.requests, "get", return_value=_fake_response(items=items)):
        result = market_data_service.get_price_series(ticker)

    assert [p.time for p in result] == ["2026-07-15"]
    assert result != market_data_service._generate_mock_price_series(ticker)
