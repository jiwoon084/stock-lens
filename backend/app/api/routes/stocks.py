from fastapi import APIRouter, HTTPException

from app.schemas.stock import PricePoint, Stock
from app.services import market_data_service

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@router.get("", response_model=list[Stock])
def list_stocks() -> list[Stock]:
    return market_data_service.get_stocks()


@router.get("/{ticker}/prices", response_model=list[PricePoint])
def get_prices(ticker: str) -> list[PricePoint]:
    if market_data_service.get_stock(ticker) is None:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return market_data_service.get_price_series(ticker)
