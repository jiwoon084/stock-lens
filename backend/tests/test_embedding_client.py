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


def _fake_batch_response(vectors: list[list[float]]):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        "data": [{"embedding": vector, "index": index} for index, vector in enumerate(vectors)]
    }
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


def test_embed_passages_empty_list_skips_request():
    with patch.object(embedding_client.requests, "post") as post:
        vectors = embedding_client.embed_passages([])

    assert vectors == []
    post.assert_not_called()


def test_embed_passages_sends_one_batched_request():
    settings.solar_api_key = "test-key"
    with patch.object(
        embedding_client.requests, "post", return_value=_fake_batch_response([[0.1, 0.2], [0.3, 0.4]])
    ) as post:
        vectors = embedding_client.embed_passages(["첫 번째 문서", "두 번째 문서"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert post.call_args.kwargs["json"] == {
        "input": ["첫 번째 문서", "두 번째 문서"],
        "model": embedding_client.PASSAGE_MODEL,
    }
    post.assert_called_once()


def test_embed_passages_reorders_by_response_index():
    """Defensive: sort by the response's own `index` instead of trusting response order matches
    request order, in case a provider ever returns entries out of sequence.
    """
    settings.solar_api_key = "test-key"
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        "data": [
            {"embedding": [0.3, 0.4], "index": 1},
            {"embedding": [0.1, 0.2], "index": 0},
        ]
    }

    with patch.object(embedding_client.requests, "post", return_value=response):
        vectors = embedding_client.embed_passages(["첫 번째 문서", "두 번째 문서"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_passages_raises_without_key():
    with pytest.raises(embedding_client.EmbeddingApiError):
        embedding_client.embed_passages(["text"])
