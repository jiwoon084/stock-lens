"""Near-real-time domestic stock quotes via KIS Developers (한국투자증권 Open API), demo
(모의투자) domain — Stock Lens Phase 1 real-time approach: REST polling of the current-price
endpoint, not full WebSocket tick streaming (see CLAUDE.md real-time data plan).

Token issuance (`/oauth2/tokenP`) is rate-limited to once per minute per key (KIS returns
EGW00133 "접근토큰 발급 잠시 후 다시 시도하세요(1분당 1회)" otherwise, confirmed empirically) and
the issued token is valid ~24h, so it's cached in-process and only reissued once missing/expired
— same "don't refetch what we already have" pattern as krx_price_client.py's daily cache.

`market_data_service.get_live_price()` is the only caller; it returns None on any KisApiError
(missing keys, network failure, malformed response) so a live-price badge simply doesn't render
rather than breaking the page — there's no meaningful "mock" for a real-time quote the way there
is for a historical series.
"""

from datetime import datetime, timedelta

import requests

from app.core.config import settings
from app.schemas.stock import LivePrice

BASE_URL = "https://openapivts.koreainvestment.com:29443"  # 모의투자(demo) 도메인
TOKEN_URL = f"{BASE_URL}/oauth2/tokenP"
QUOTE_URL = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
QUOTE_TR_ID = "FHKST01010100"

# prdy_vrss_sign: 1=상한, 2=상승, 3=보합, 4=하한, 5=하락 (KIS 공식 코드값)
_UP_SIGNS = {"1", "2"}
_DOWN_SIGNS = {"4", "5"}

_cached_token: str | None = None
_token_expires_at: datetime | None = None


class KisApiError(Exception):
    """Raised on any failure to fetch a live quote — caller should fall back to no live badge."""


def _get_access_token() -> str:
    global _cached_token, _token_expires_at

    if _cached_token and _token_expires_at and datetime.now() < _token_expires_at:
        return _cached_token

    if not settings.kis_app_key or not settings.kis_app_secret:
        raise KisApiError("KIS_APP_KEY/KIS_APP_SECRET is not configured")

    try:
        response = requests.post(
            TOKEN_URL,
            headers={"Content-Type": "application/json; charset=UTF-8"},
            json={
                "grant_type": "client_credentials",
                "appkey": settings.kis_app_key,
                "appsecret": settings.kis_app_secret,
            },
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        token = body["access_token"]
        expires_in = int(body.get("expires_in", 86400))
    except Exception as exc:
        raise KisApiError(f"KIS token issuance failed: {exc}") from exc

    _cached_token = token
    # Refresh a few minutes early rather than racing the exact expiry instant.
    _token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
    return token


def fetch_live_price(ticker: str) -> LivePrice:
    token = _get_access_token()

    try:
        response = requests.get(
            QUOTE_URL,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "authorization": f"Bearer {token}",
                "appkey": settings.kis_app_key,
                "appsecret": settings.kis_app_secret,
                "tr_id": QUOTE_TR_ID,
                "custtype": "P",
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
            },
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        raise KisApiError(f"KIS quote request failed for {ticker}: {exc}") from exc

    if body.get("rt_cd") != "0":
        raise KisApiError(f"KIS quote API returned {body.get('rt_cd')}: {body.get('msg1')}")

    try:
        output = body["output"]
        sign = output["prdy_vrss_sign"]
        direction = "up" if sign in _UP_SIGNS else "down" if sign in _DOWN_SIGNS else "flat"

        return LivePrice(
            price=float(output["stck_prpr"]),
            change=float(output["prdy_vrss"]),
            change_percent=float(output["prdy_ctrt"]),
            direction=direction,
            open=float(output["stck_oprc"]),
            high=float(output["stck_hgpr"]),
            low=float(output["stck_lwpr"]),
            volume=int(output["acml_vol"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise KisApiError(f"Unexpected KIS quote response shape: {exc}") from exc
