from unittest.mock import Mock, patch

import pytest

from app.core.config import settings
from app.services.llm.base import LLMProviderError
from app.services.llm.gemini_provider import GeminiProvider


@pytest.fixture(autouse=True)
def _reset_gemini_key():
    original = settings.gemini_api_key
    settings.gemini_api_key = ""
    yield
    settings.gemini_api_key = original


def _fake_response(payload: dict):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = payload
    return response


def test_raises_without_api_key():
    provider = GeminiProvider()
    with pytest.raises(LLMProviderError):
        provider.generate("system prompt", {"ticker": "005930"})


def test_generate_returns_raw_json_text():
    settings.gemini_api_key = "test-key"
    provider = GeminiProvider()
    payload = {"candidates": [{"content": {"parts": [{"text": '{"chart_card": {}}'}]}}]}

    with patch("app.services.llm.gemini_provider.requests.post", return_value=_fake_response(payload)) as mock_post:
        result = provider.generate("system prompt", {"ticker": "005930"})

    assert result == '{"chart_card": {}}'
    request_kwargs = mock_post.call_args.kwargs
    assert request_kwargs["json"]["systemInstruction"]["parts"][0]["text"] == "system prompt"
    assert request_kwargs["json"]["generationConfig"]["responseMimeType"] == "application/json"


def test_generate_wraps_http_failure():
    settings.gemini_api_key = "test-key"
    provider = GeminiProvider()

    with patch("app.services.llm.gemini_provider.requests.post", side_effect=ConnectionError("boom")):
        with pytest.raises(LLMProviderError):
            provider.generate("system prompt", {"ticker": "005930"})


def test_generate_wraps_malformed_response_shape():
    settings.gemini_api_key = "test-key"
    provider = GeminiProvider()

    with patch(
        "app.services.llm.gemini_provider.requests.post",
        return_value=_fake_response({"candidates": []}),
    ):
        with pytest.raises(LLMProviderError):
            provider.generate("system prompt", {"ticker": "005930"})
