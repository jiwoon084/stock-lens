import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    """Keep the test suite hermetic — never spend real LLM API calls/tokens on every pytest run,
    regardless of what LLM_PROVIDER is set to in the local .env."""
    monkeypatch.setattr(settings, "llm_provider", "mock")
