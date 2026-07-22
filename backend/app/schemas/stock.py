from typing import Literal

from pydantic import BaseModel


class Stock(BaseModel):
    ticker: str
    name: str
    market: str


class LivePrice(BaseModel):
    price: float
    change: float
    change_percent: float
    direction: Literal["up", "down", "flat"]
    open: float
    high: float
    low: float
    volume: int


class LivePriceResponse(BaseModel):
    available: bool
    as_of: str | None = None
    live: LivePrice | None = None


class PricePoint(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change_percent: float
    volume_change_percent: float


class StockPricesResponse(BaseModel):
    ticker: str
    prices: list[PricePoint]
