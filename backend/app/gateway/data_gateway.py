"""Gateway functions the stock-analysis Agent (app/agent/nodes.py) uses to reach market-data and
evidence-retrieval services — see app/gateway/__init__.py for why this module exists. Every
function here just forwards to the real service; nodes.py should import this module instead of
app.services.market_data_service / app.services.retrieval_service directly.
"""

from app.schemas.explanation import Source
from app.schemas.stock import PricePoint, Stock
from app.services import market_data_service, retrieval_service


def get_stock(ticker: str) -> Stock | None:
    return market_data_service.get_stock(ticker)


def get_price_series_with_live_today(ticker: str) -> list[PricePoint]:
    return market_data_service.get_price_series_with_live_today(ticker)


def get_related_documents(ticker: str, selected_date: str, direction: str) -> list[Source]:
    return retrieval_service.get_related_documents(ticker=ticker, selected_date=selected_date, direction=direction)
