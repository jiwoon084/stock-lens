from pydantic import BaseModel


class Stock(BaseModel):
    ticker: str
    name: str
    market: str


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
