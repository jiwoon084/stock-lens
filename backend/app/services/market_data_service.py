import random
from datetime import date, timedelta

from app.schemas.stock import PricePoint, Stock

SAMPLE_STOCKS: list[Stock] = [
    Stock(ticker="005930", name="삼성전자", market="KOSPI"),
    Stock(ticker="000660", name="SK하이닉스", market="KOSPI"),
    Stock(ticker="035420", name="NAVER", market="KOSPI"),
    Stock(ticker="035720", name="카카오", market="KOSPI"),
    Stock(ticker="005380", name="현대차", market="KOSPI"),
]

_LATEST_TRADING_DAY = date(2026, 7, 17)
_TRADING_DAYS = 30


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
    rng = random.Random(f"stock-lens-{ticker}")
    trading_days = _business_days_ending(_LATEST_TRADING_DAY, _TRADING_DAYS)

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
