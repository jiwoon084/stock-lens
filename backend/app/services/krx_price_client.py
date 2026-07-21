"""Real daily KRX price series via 금융위원회_주식시세정보 (data.go.kr).

Unlike DART disclosures (`retrieval_service.py`), which are historical facts fetched once into
a JSON snapshot, daily prices change every trading day — a snapshot would just be another frozen
mock. So this calls the API live per request, with a same-day in-process cache (see
`_cached_fetch`) so repeated requests for the same ticker on the same day don't re-hit the API.

`market_data_service.get_price_series()` is the only caller; it falls back to the mock generator
on any `KrxApiError` (or when `settings.krx_api_key` is empty), so a missing/invalid key never
breaks the app — see docs/project-plan.md M1.
"""

from datetime import date, timedelta
from functools import lru_cache

import requests

from app.core.config import settings
from app.schemas.stock import PricePoint

API_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
TRADING_DAYS = 30
# Calendar-day lookback for the query window: enough to cover TRADING_DAYS trading days plus
# one extra trading day (weekends/holidays included) so the oldest row in the output can still
# compute volume_change_percent against a real previous day.
LOOKBACK_CALENDAR_DAYS = 60


class KrxApiError(Exception):
    """Raised on any failure to fetch/parse a real price series — callers should fall back."""


def fetch_price_series(ticker: str) -> list[PricePoint]:
    if not settings.krx_api_key:
        raise KrxApiError("KRX_API_KEY is not configured")

    items = _cached_fetch(ticker, date.today().isoformat())
    points = _to_price_points(items)

    if len(points) < 2:
        raise KrxApiError(f"Not enough KRX price rows returned for {ticker}")

    # The first row only exists to give the second row a volume baseline (its own
    # volume_change_percent is meaningless) — drop it before taking the most recent window.
    return points[1:][-TRADING_DAYS:]


@lru_cache(maxsize=32)
def _cached_fetch(ticker: str, as_of: str) -> tuple[dict, ...]:
    """`as_of` (today's date, passed by the caller) is part of the cache key purely so the
    cache busts once a day — this function itself ignores the value.
    """
    end = date.fromisoformat(as_of)
    begin = end - timedelta(days=LOOKBACK_CALENDAR_DAYS)

    try:
        response = requests.get(
            API_URL,
            params={
                "serviceKey": settings.krx_api_key,
                "resultType": "json",
                "numOfRows": 100,
                "pageNo": 1,
                "likeSrtnCd": ticker,
                "beginBasDt": begin.strftime("%Y%m%d"),
                "endBasDt": end.strftime("%Y%m%d"),
            },
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        raise KrxApiError(f"KRX API request failed for {ticker}: {exc}") from exc

    result_code = body.get("response", {}).get("header", {}).get("resultCode")
    if result_code != "00":
        result_msg = body.get("response", {}).get("header", {}).get("resultMsg")
        raise KrxApiError(f"KRX API returned {result_code}: {result_msg}")

    items = body.get("response", {}).get("body", {}).get("items")
    raw_items = (items or {}).get("item") or []
    return tuple(raw_items)


def _to_price_points(items: tuple[dict, ...]) -> list[PricePoint]:
    try:
        rows = sorted(items, key=lambda item: item["basDt"])
        points: list[PricePoint] = []
        prev_volume: int | None = None

        for row in rows:
            volume = int(row["trqu"])
            volume_change_percent = (
                round((volume - prev_volume) / prev_volume * 100, 2)
                if prev_volume is not None
                else 0.0
            )
            bas_dt = row["basDt"]

            points.append(
                PricePoint(
                    time=f"{bas_dt[0:4]}-{bas_dt[4:6]}-{bas_dt[6:8]}",
                    open=float(row["mkp"]),
                    high=float(row["hipr"]),
                    low=float(row["lopr"]),
                    close=float(row["clpr"]),
                    volume=volume,
                    change_percent=float(row["fltRt"]),
                    volume_change_percent=volume_change_percent,
                )
            )
            prev_volume = volume
    except (KeyError, ValueError, TypeError) as exc:
        raise KrxApiError(f"Unexpected KRX API response shape: {exc}") from exc

    return points
