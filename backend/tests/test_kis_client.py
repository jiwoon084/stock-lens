from unittest.mock import Mock, patch

import pytest

from app.core.config import settings
from app.services import kis_client


@pytest.fixture(autouse=True)
def _reset_kis_state():
    original_key = settings.kis_app_key
    original_secret = settings.kis_app_secret
    settings.kis_app_key = ""
    settings.kis_app_secret = ""
    kis_client._cached_token = None
    kis_client._token_expires_at = None
    yield
    settings.kis_app_key = original_key
    settings.kis_app_secret = original_secret
    kis_client._cached_token = None
    kis_client._token_expires_at = None


def _fake_response(payload: dict):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = payload
    return response


_VALID_QUOTE = {
    "rt_cd": "0",
    "msg1": "정상처리 되었습니다.",
    "output": {
        "stck_prpr": "260750",
        "prdy_vrss": "1750",
        "prdy_vrss_sign": "2",
        "prdy_ctrt": "0.68",
        "stck_oprc": "276000",
        "stck_hgpr": "276000",
        "stck_lwpr": "260000",
        "acml_vol": "19400831",
    },
}


def test_raises_without_keys():
    with pytest.raises(kis_client.KisApiError):
        kis_client.fetch_live_price("005930")


def test_fetches_and_parses_live_price():
    settings.kis_app_key = "test-key"
    settings.kis_app_secret = "test-secret"

    with patch.object(
        kis_client.requests, "post", return_value=_fake_response({"access_token": "tok", "expires_in": 86400})
    ), patch.object(kis_client.requests, "get", return_value=_fake_response(_VALID_QUOTE)):
        result = kis_client.fetch_live_price("005930")

    assert result.price == 260750.0
    assert result.change == 1750.0
    assert result.direction == "up"
    assert result.volume == 19400831


def test_token_is_cached_across_calls():
    settings.kis_app_key = "test-key"
    settings.kis_app_secret = "test-secret"

    with patch.object(
        kis_client.requests, "post", return_value=_fake_response({"access_token": "tok", "expires_in": 86400})
    ) as mock_post, patch.object(kis_client.requests, "get", return_value=_fake_response(_VALID_QUOTE)):
        kis_client.fetch_live_price("005930")
        kis_client.fetch_live_price("000660")

    mock_post.assert_called_once()


def test_raises_on_non_zero_rt_cd():
    settings.kis_app_key = "test-key"
    settings.kis_app_secret = "test-secret"
    error_quote = {"rt_cd": "1", "msg1": "유효하지 않습니다", "msg_cd": "EGW00205"}

    with patch.object(
        kis_client.requests, "post", return_value=_fake_response({"access_token": "tok", "expires_in": 86400})
    ), patch.object(kis_client.requests, "get", return_value=_fake_response(error_quote)):
        with pytest.raises(kis_client.KisApiError):
            kis_client.fetch_live_price("005930")


def test_fetches_and_reorders_intraday_prices():
    settings.kis_app_key = "test-key"
    settings.kis_app_secret = "test-secret"
    intraday_payload = {
        "rt_cd": "0",
        "output2": [
            {"stck_bsop_date": "20260722", "stck_cntg_hour": "153000", "stck_prpr": "260500"},
            {"stck_bsop_date": "20260722", "stck_cntg_hour": "152900", "stck_prpr": "260750"},
        ],
    }

    with patch.object(
        kis_client.requests, "post", return_value=_fake_response({"access_token": "tok", "expires_in": 86400})
    ), patch.object(kis_client.requests, "get", return_value=_fake_response(intraday_payload)):
        result = kis_client.fetch_intraday_minute_prices("005930")

    assert [p.time for p in result] == ["2026-07-22T15:29:00+09:00", "2026-07-22T15:30:00+09:00"]
    assert [p.price for p in result] == [260750.0, 260500.0]


def test_raises_on_malformed_quote_shape():
    settings.kis_app_key = "test-key"
    settings.kis_app_secret = "test-secret"
    malformed = {"rt_cd": "0", "output": {"stck_prpr": "not-a-number"}}

    with patch.object(
        kis_client.requests, "post", return_value=_fake_response({"access_token": "tok", "expires_in": 86400})
    ), patch.object(kis_client.requests, "get", return_value=_fake_response(malformed)):
        with pytest.raises(kis_client.KisApiError):
            kis_client.fetch_live_price("005930")
