"""Text embeddings via Upstage's SOLAR embedding API.

Same OpenAI-compatible HTTP style as solar_client.py (plain `requests`, no SDK). SOLAR ships
two embedding models sharing one vector space: "query" for the search query and "passage" for
the documents being searched — see https://www.upstage.ai/blog/en/solar-embedding-1-large.
retrieval_service.py uses embed_query/embed_passage to rerank disclosures/news by semantic
similarity to the selected date's price movement, not just date proximity.

Raises EmbeddingApiError on any failure (no key, network error, unexpected response shape) so
callers can fall back to the previous date-only ranking — mirrors solar_client.SolarApiError.
"""

import requests

from app.core.config import settings

API_URL = "https://api.upstage.ai/v1/solar/embeddings"
QUERY_MODEL = "solar-embedding-1-large-query"
PASSAGE_MODEL = "solar-embedding-1-large-passage"


class EmbeddingApiError(Exception):
    """Raised when an embedding request fails — caller should fall back to non-semantic ranking."""


def _embed(text: str, model: str) -> list[float]:
    if not settings.solar_api_key:
        raise EmbeddingApiError("SOLAR_API_KEY is not configured")

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {settings.solar_api_key}"},
            json={"input": text, "model": model},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as exc:
        raise EmbeddingApiError(f"Upstage embedding request failed: {exc}") from exc


def embed_query(text: str) -> list[float]:
    return _embed(text, QUERY_MODEL)


def embed_passage(text: str) -> list[float]:
    return _embed(text, PASSAGE_MODEL)
