import json
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.services import embedding_client, retrieval_service


@pytest.fixture(autouse=True)
def _reset_state():
    original_key = settings.solar_api_key
    settings.solar_api_key = ""
    retrieval_service._passage_embedding_cache.clear()
    retrieval_service._query_embedding_cache.clear()
    yield
    settings.solar_api_key = original_key
    retrieval_service._passage_embedding_cache.clear()
    retrieval_service._query_embedding_cache.clear()


def _disclosure(rcept_no: str, rcept_dt: str, report_nm: str) -> dict:
    return {"rcept_no": rcept_no, "rcept_dt": rcept_dt, "report_nm": report_nm, "flr_nm": "삼성전자"}


def _news(title: str, pub_date: str) -> dict:
    return {"title": title, "description": "필러 뉴스", "link": "https://example.com/n", "pub_date": pub_date}


# 2 filler news articles so DISCLOSURE_SLOTS(3) actually caps disclosure selection below —
# with 0 news, the "give leftover slots to the short side" logic lets all 4 disclosures
# through (see retrieval_service.get_related_documents), which would defeat these tests.
_FILLER_NEWS = [
    _news("필러 뉴스 A", "Tue, 14 Jul 2026 09:00:00 +0900"),
    _news("필러 뉴스 B", "Mon, 13 Jul 2026 09:00:00 +0900"),
]


def test_embedding_cache_persists_across_a_simulated_restart(tmp_path, monkeypatch):
    cache_file = tmp_path / "embeddings.json"
    monkeypatch.setattr(retrieval_service, "_cache_file_path", lambda: cache_file)
    settings.solar_api_key = "test-key"

    with patch.object(embedding_client, "embed_passages", return_value=[[1.0, 0.0]]) as embed_passages:
        retrieval_service._get_passage_embeddings(("a",))
    embed_passages.assert_called_once()
    assert cache_file.exists()

    # Simulate a process restart: in-memory cache gone, reload from the file just written.
    retrieval_service._passage_embedding_cache.clear()
    retrieval_service._query_embedding_cache.clear()
    retrieval_service._load_embedding_cache_from_disk()

    with patch.object(embedding_client, "embed_passages") as embed_passages_after_reload:
        result = retrieval_service._get_passage_embeddings(("a",))

    embed_passages_after_reload.assert_not_called()  # served from the reloaded disk cache
    assert result == [[1.0, 0.0]]


def test_embedding_cache_ignored_when_model_version_differs(tmp_path, monkeypatch):
    cache_file = tmp_path / "embeddings.json"
    cache_file.write_text(
        json.dumps({"version": "some-other-model", "queries": {}, "passages": {"a": [9.0]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(retrieval_service, "_cache_file_path", lambda: cache_file)

    retrieval_service._load_embedding_cache_from_disk()

    assert "a" not in retrieval_service._passage_embedding_cache


def test_embedding_cache_load_survives_a_corrupt_file(tmp_path, monkeypatch):
    cache_file = tmp_path / "embeddings.json"
    cache_file.write_text("not valid json", encoding="utf-8")
    monkeypatch.setattr(retrieval_service, "_cache_file_path", lambda: cache_file)

    retrieval_service._load_embedding_cache_from_disk()  # must not raise

    assert retrieval_service._passage_embedding_cache == {}


def test_semantic_scores_none_without_key():
    assert retrieval_service._semantic_scores("query", ("text",)) is None


def test_semantic_scores_computed_with_key():
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client, "embed_query", return_value=[1.0, 0.0]), patch.object(
        embedding_client, "embed_passages", return_value=[[1.0, 0.0]]
    ):
        scores = retrieval_service._semantic_scores("query", ("relevant text",))

    assert scores == (1.0,)


def test_semantic_scores_batches_passages_in_one_call():
    """N candidate texts must cost exactly one embed_passages call, not N — the whole point of
    batching is collapsing per-click embedding latency from dozens of round trips to one.
    """
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client, "embed_query", return_value=[1.0, 0.0]), patch.object(
        embedding_client, "embed_passages", return_value=[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]
    ) as embed_passages:
        scores = retrieval_service._semantic_scores("query", ("a", "b", "c"))

    embed_passages.assert_called_once_with(["a", "b", "c"])
    assert scores == (1.0, 0.0, 1.0)


def test_hybrid_ranking_surfaces_semantically_relevant_disclosure_over_closer_dates(monkeypatch):
    """4 candidates, only top 3 (DISCLOSURE_SLOTS) get selected. Without semantic reranking,
    the 3 closest-dated (but irrelevant) disclosures would win and the semantically relevant
    but older one would be dropped. With embeddings available, it should surface instead.
    """
    settings.solar_api_key = "test-key"

    entries = [
        _disclosure("r-a", "20260714", "필러 공시 A"),  # delta -1, irrelevant
        _disclosure("r-b", "20260713", "필러 공시 B"),  # delta -2, irrelevant
        _disclosure("r-c", "20260712", "필러 공시 C"),  # delta -3, irrelevant
        _disclosure("r-d", "20260701", "자기주식처분 결정"),  # delta -14, relevant
    ]

    monkeypatch.setattr(retrieval_service, "_load_disclosures_by_ticker", lambda: {"005930": entries})
    monkeypatch.setattr(retrieval_service, "_load_news_by_ticker", lambda: {"005930": _FILLER_NEWS})
    monkeypatch.setattr(retrieval_service, "_load_major_events_by_rcept_no", lambda: {})

    def fake_embed_passages(texts: list[str]):
        return [[1.0, 0.0] if text == "자기주식처분 결정" else [0.0, 1.0] for text in texts]

    with patch.object(embedding_client, "embed_query", return_value=[1.0, 0.0]), patch.object(
        embedding_client, "embed_passages", side_effect=fake_embed_passages
    ):
        sources = retrieval_service.get_related_documents("005930", "2026-07-15", "down")

    source_ids = {s.id for s in sources}
    assert "r-d" in source_ids  # semantically relevant, older, now surfaced
    assert "r-c" not in source_ids  # closest-date-but-irrelevant, now pushed out


def test_ranking_falls_back_to_date_order_without_key(monkeypatch):
    """Same fixture, but no SOLAR_API_KEY — must reproduce the pre-existing date-only order."""
    entries = [
        _disclosure("r-a", "20260714", "필러 공시 A"),
        _disclosure("r-b", "20260713", "필러 공시 B"),
        _disclosure("r-c", "20260712", "필러 공시 C"),
        _disclosure("r-d", "20260701", "자기주식처분 결정"),
    ]
    monkeypatch.setattr(retrieval_service, "_load_disclosures_by_ticker", lambda: {"005930": entries})
    monkeypatch.setattr(retrieval_service, "_load_news_by_ticker", lambda: {"005930": _FILLER_NEWS})
    monkeypatch.setattr(retrieval_service, "_load_major_events_by_rcept_no", lambda: {})

    sources = retrieval_service.get_related_documents("005930", "2026-07-15", "down")

    disclosure_ids = {s.id for s in sources if s.type == "disclosure"}
    assert disclosure_ids == {"r-a", "r-b", "r-c"}
    assert "r-d" not in disclosure_ids
