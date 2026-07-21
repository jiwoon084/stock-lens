from fastapi.testclient import TestClient

from app.main import app
from app.services import market_data_service

client = TestClient(app)


def test_valid_checklist_returns_200():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker

    response = client.get(f"/api/v1/stocks/{ticker}/checklist")

    assert response.status_code == 200


def test_unknown_ticker_returns_404():
    response = client.get("/api/v1/stocks/999999/checklist")

    assert response.status_code == 404


def test_checklist_contains_required_fields():
    ticker = market_data_service.SAMPLE_STOCKS[0].ticker

    response = client.get(f"/api/v1/stocks/{ticker}/checklist")

    body = response.json()
    for field in ("ticker", "date", "total_article_count", "items"):
        assert field in body
    for field in ("id", "tag", "headline", "description", "source_count"):
        assert field in body["items"][0]
