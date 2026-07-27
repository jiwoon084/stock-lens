from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import rate_limit


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(rate_limit.enforce_rate_limit)])
    def ping():
        return {"ok": True}

    return app


def test_allows_up_to_the_limit():
    client = TestClient(_build_app())
    for _ in range(rate_limit.MAX_REQUESTS_PER_WINDOW):
        assert client.get("/ping").status_code == 200


def test_blocks_over_the_limit_with_retry_after_header():
    client = TestClient(_build_app())
    for _ in range(rate_limit.MAX_REQUESTS_PER_WINDOW):
        client.get("/ping")

    response = client.get("/ping")

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_reset_clears_blocked_state():
    client = TestClient(_build_app())
    for _ in range(rate_limit.MAX_REQUESTS_PER_WINDOW):
        client.get("/ping")
    assert client.get("/ping").status_code == 429

    rate_limit.reset()

    assert client.get("/ping").status_code == 200
