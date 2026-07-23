from unittest.mock import Mock, patch

import pytest

from app.core.config import settings
from app.services import embedding_client


@pytest.fixture(autouse=True)
def _reset_solar_key():
    original_key = settings.solar_api_key
    settings.solar_api_key = ""
    yield
    settings.solar_api_key = original_key


def _fake_success_response(vector: list[float]):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"data": [{"embedding": vector}]}
    return response


def test_raises_without_key():
    with pytest.raises(embedding_client.EmbeddingApiError):
        embedding_client.embed_query("text")


def test_embed_query_uses_query_model():
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client.requests, "post", return_value=_fake_success_response([0.1, 0.2])) as post:
        vector = embedding_client.embed_query("삼성전자 하락 이유")

    assert vector == [0.1, 0.2]
    assert post.call_args.kwargs["json"]["model"] == embedding_client.QUERY_MODEL


def test_embed_passage_uses_passage_model():
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client.requests, "post", return_value=_fake_success_response([0.3, 0.4])) as post:
        vector = embedding_client.embed_passage("공시 발췌 내용")

    assert vector == [0.3, 0.4]
    assert post.call_args.kwargs["json"]["model"] == embedding_client.PASSAGE_MODEL


def test_raises_on_network_error():
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client.requests, "post", side_effect=ConnectionError("boom")):
        with pytest.raises(embedding_client.EmbeddingApiError):
            embedding_client.embed_query("text")


def test_raises_on_malformed_response():
    settings.solar_api_key = "test-key"
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"unexpected": "shape"}

    with patch.object(embedding_client.requests, "post", return_value=response):
        with pytest.raises(embedding_client.EmbeddingApiError):
            embedding_client.embed_query("text")
