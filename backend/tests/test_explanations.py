from fastapi.testclient import TestClient

from app.main import app
from app.services import market_data_service

client = TestClient(app)


def test_list_stocks_returns_at_least_one():
    response = client.get("/api/v1/stocks")
    assert response.status_code == 200
    stocks = response.json()
    assert len(stocks) >= 1
    assert "ticker" in stocks[0]


def test_valid_explanation_returns_200():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    selected_date = market_data_service.get_price_series(ticker)[-1].time

    response = client.post(
        "/api/v1/explanations",
        json={"ticker": ticker, "selected_date": selected_date, "interval": "1d"},
    )

    assert response.status_code == 200


def test_unknown_ticker_returns_404():
    response = client.post(
        "/api/v1/explanations",
        json={"ticker": "999999", "selected_date": "2026-07-17", "interval": "1d"},
    )

    assert response.status_code == 404


def test_explanation_contains_required_fields():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker
    selected_date = market_data_service.get_price_series(ticker)[-1].time

    response = client.post(
        "/api/v1/explanations",
        json={"ticker": ticker, "selected_date": selected_date, "interval": "1d"},
    )

    body = response.json()
    for field in ("headline", "summary", "factors", "sources", "limitations"):
        assert field in body
