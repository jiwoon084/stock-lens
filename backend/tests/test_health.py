from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_url_follows_enable_api_docs_setting():
    # ENABLE_API_DOCS defaults to true for local dev; production sets it false via
    # infra/gce/.env.example so the API schema isn't publicly browsable with no auth in front.
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


def test_cors_does_not_allow_credentials():
    # No cookie/session auth exists anywhere in this app, so credentialed cross-origin
    # requests have nothing to carry — allow_credentials should stay off.
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-credentials" not in response.headers
