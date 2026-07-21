"""Real stock price series, served from a pre-built local cache.

pykrx scrapes KRX/Naver Finance rather than calling a documented, authenticated
API — fine for an offline collection script (see data/step4_prices.py), but not
something this service should call on every request (site-structure changes or
rate limiting would take the whole API down). So the API only ever reads from
the SQLite cache that script builds; a deterministic mock series is used as a
fallback for tickers/environments where that cache hasn't been built yet (e.g.
a fresh teammate clone or CI), so the app never breaks for lack of it.
"""

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from app.schemas.stock import PricePoint, Stock

SAMPLE_STOCKS: list[Stock] = [
    Stock(ticker="005930", name="삼성전자", market="KOSPI"),
    Stock(ticker="000660", name="SK하이닉스", market="KOSPI"),
    Stock(ticker="035420", name="NAVER", market="KOSPI"),
    Stock(ticker="035720", name="카카오", market="KOSPI"),
    Stock(ticker="005380", name="현대차", market="KOSPI"),
]

_LOOKBACK_DAYS = 365  # 차트에 보여줄 기간: 현재 시점 기준 최근 1년
_FETCH_BUFFER_DAYS = 10  # 창 시작일의 변화율 계산용 baseline 여유분
_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "market_data.sqlite3"

_MOCK_BASE_PRICES = {
    "005930": 78000.0,
    "000660": 195000.0,
    "035420": 210000.0,
    "035720": 45000.0,
    "005380": 240000.0,
}


def get_stocks() -> list[Stock]:
    return SAMPLE_STOCKS


def get_stock(ticker: str) -> Stock | None:
    return next((stock for stock in SAMPLE_STOCKS if stock.ticker == ticker), None)


def _business_days_ending(end: date, count: int) -> list[date]:
    days: list[date] = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


def _mock_price_series(ticker: str) -> list[PricePoint]:
    """Deterministic fallback so the app still works before step4_prices.py has been run."""
    rng = random.Random(f"stock-lens-{ticker}")
    days = _business_days_ending(date.today(), 250)

    price = _MOCK_BASE_PRICES.get(ticker, 50000.0)
    prev_close = price
    prev_volume = rng.randint(4_000_000, 8_000_000)

    points: list[PricePoint] = []
    for day in days:
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


def _read_cached_rows(ticker: str) -> list[sqlite3.Row]:
    if not _DB_PATH.exists():
        return []

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        fetch_start = (date.today() - timedelta(days=_LOOKBACK_DAYS + _FETCH_BUFFER_DAYS)).isoformat()
        cursor = conn.execute(
            "SELECT date, open, high, low, close, volume FROM prices WHERE ticker = ? AND date >= ? ORDER BY date",
            (ticker, fetch_start),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_price_series(ticker: str) -> list[PricePoint]:
    rows = _read_cached_rows(ticker)
    if not rows:
        return _mock_price_series(ticker)

    window_start = (date.today() - timedelta(days=_LOOKBACK_DAYS)).isoformat()

    points: list[PricePoint] = []
    prev_close = rows[0]["close"]
    prev_volume = rows[0]["volume"]
    for row in rows[1:]:
        change_percent = round((row["close"] - prev_close) / prev_close * 100, 2)
        volume_change_percent = round((row["volume"] - prev_volume) / prev_volume * 100, 2)

        if row["date"] >= window_start:
            points.append(
                PricePoint(
                    time=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    change_percent=change_percent,
                    volume_change_percent=volume_change_percent,
                )
            )

        prev_close = row["close"]
        prev_volume = row["volume"]

    return points
