import logging
import random
from datetime import date, timedelta

from app.core.config import settings
from app.schemas.stock import IntradayPoint, LivePrice, PricePoint, Stock
from app.services import kis_client, krx_price_client

logger = logging.getLogger(__name__)

SAMPLE_STOCKS: list[Stock] = [
    Stock(ticker="005930", name="삼성전자", market="KOSPI"),
    Stock(ticker="000660", name="SK하이닉스", market="KOSPI"),
    Stock(ticker="035420", name="NAVER", market="KOSPI"),
    Stock(ticker="035720", name="카카오", market="KOSPI"),
    Stock(ticker="005380", name="현대차", market="KOSPI"),
]

_TRADING_DAYS = 250  # 차트 표시 기간(1년)에 맞춤 — krx_price_client.TRADING_DAYS와 동일하게 유지


def _business_days_ending(end: date, count: int) -> list[date]:
    days: list[date] = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


def _base_price_for(ticker: str) -> float:
    seed_prices = {
        "005930": 78000.0,
        "000660": 195000.0,
        "035420": 210000.0,
        "035720": 45000.0,
        "005380": 240000.0,
    }
    return seed_prices.get(ticker, 50000.0)


def get_stocks() -> list[Stock]:
    return SAMPLE_STOCKS


def get_stock(ticker: str) -> Stock | None:
    return next((stock for stock in SAMPLE_STOCKS if stock.ticker == ticker), None)


def get_price_series(ticker: str) -> list[PricePoint]:
    """Real KRX daily prices when KRX_API_KEY is configured, otherwise (or on any failure of
    that real call) a deterministic mock series — see docs/project-plan.md M1.
    """
    if settings.krx_api_key:
        try:
            return krx_price_client.fetch_price_series(ticker)
        except krx_price_client.KrxApiError as exc:
            logger.warning("KRX price fetch failed for %s, falling back to mock: %s", ticker, exc)

    return _generate_mock_price_series(ticker)


def get_live_price(ticker: str) -> LivePrice | None:
    """Near-real-time current price during market hours, via KIS Developers (demo account).

    Returns None (not a mock) when unavailable — a fabricated "live" price would violate the
    project's "출처 기반 신뢰성" principle worse than just hiding the live badge.
    """
    if not settings.kis_app_key or not settings.kis_app_secret:
        return None

    try:
        return kis_client.fetch_live_price(ticker)
    except kis_client.KisApiError as exc:
        logger.warning("KIS live price fetch failed for %s: %s", ticker, exc)
        return None


# ticker -> {"date": "YYYY-MM-DD", "points": {iso_time: price}} — accumulates each poll's ~30-row
# chunk into a growing full-day series (resets when the calendar date rolls over). A single KIS
# call only returns the most recent ~30 minutes (no pagination implemented), so on a cold start
# only that much history shows up; it fills in as polling continues through the session.
_intraday_cache: dict[str, dict] = {}


def get_intraday_prices(ticker: str) -> list[IntradayPoint]:
    """Today's near-real-time minute-by-minute prices for the continuous "today" chart segment.

    Returns an empty list (not a mock) when KIS isn't configured or the call fails — same
    "no fabricated real-time data" principle as get_live_price().
    """
    if not settings.kis_app_key or not settings.kis_app_secret:
        return []

    try:
        fresh_points = kis_client.fetch_intraday_minute_prices(ticker)
    except kis_client.KisApiError as exc:
        logger.warning("KIS intraday fetch failed for %s: %s", ticker, exc)
        fresh_points = []

    today = date.today().isoformat()
    cache_entry = _intraday_cache.get(ticker)
    if cache_entry is None or cache_entry["date"] != today:
        cache_entry = {"date": today, "points": {}}
        _intraday_cache[ticker] = cache_entry

    for point in fresh_points:
        cache_entry["points"][point.time] = point.price

    return [IntradayPoint(time=time, price=price) for time, price in sorted(cache_entry["points"].items())]


def _generate_mock_price_series(ticker: str) -> list[PricePoint]:
    rng = random.Random(f"stock-lens-{ticker}")
    trading_days = _business_days_ending(date.today(), _TRADING_DAYS)

    price = _base_price_for(ticker)
    prev_close = price
    prev_volume = rng.randint(4_000_000, 8_000_000)

    points: list[PricePoint] = []
    for day in trading_days:
        daily_change = rng.uniform(-0.03, 0.03)
        open_price = prev_close
        close_price = round(open_price * (1 + daily_change), -2)
        high_price = round(max(open_price, close_price) * (1 + rng.uniform(0, 0.015)), -2)
        low_price = round(min(open_price, close_price) * (1 - rng.uniform(0, 0.015)), -2)
        volume = rng.randint(3_000_000, 12_000_000)

        change_percent = round((close_price - prev_close) / prev_close * 100, 2)
        volume_change_percent = round((volume - prev_volume) / prev_volume * 100, 2)

        points.append(
            PricePoint(
                time=day.isoformat(),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                change_percent=change_percent,
                volume_change_percent=volume_change_percent,
            )
        )

        prev_close = close_price
        prev_volume = volume

    return points
