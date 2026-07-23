from unittest.mock import patch

import pytest

from app.core.config import settings
from app.services import embedding_client, retrieval_service


@pytest.fixture(autouse=True)
def _reset_state():
    original_key = settings.solar_api_key
    settings.solar_api_key = ""
    retrieval_service._cached_passage_embedding.cache_clear()
    retrieval_service._cached_query_embedding.cache_clear()
    yield
    settings.solar_api_key = original_key
    retrieval_service._cached_passage_embedding.cache_clear()
    retrieval_service._cached_query_embedding.cache_clear()


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


def test_semantic_scores_none_without_key():
    assert retrieval_service._semantic_scores("query", ("text",)) is None


def test_semantic_scores_computed_with_key():
    settings.solar_api_key = "test-key"
    with patch.object(embedding_client, "embed_query", return_value=[1.0, 0.0]), patch.object(
        embedding_client, "embed_passage", return_value=[1.0, 0.0]
    ):
        scores = retrieval_service._semantic_scores("query", ("relevant text",))

    assert scores == (1.0,)


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

    def fake_embed_passage(text: str):
        return [1.0, 0.0] if text == "자기주식처분 결정" else [0.0, 1.0]

    with patch.object(embedding_client, "embed_query", return_value=[1.0, 0.0]), patch.object(
        embedding_client, "embed_passage", side_effect=fake_embed_passage
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
