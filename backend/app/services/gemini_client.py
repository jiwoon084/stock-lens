"""Real headline/summary/factor generation via Google's Gemini API.

Uses the generateContent REST endpoint with a JSON-schema-constrained response
(generationConfig.responseSchema), mirroring solar_client.py's approach for SOLAR.
`llm_service.py` is the only caller and falls back to its rule-based response on any
`GeminiApiError` — see docs/project-plan.md M3.

Verified against a real call on 2026-07-21. Two gotchas found empirically, both handled by
`settings.gemini_model` (app/core/config.py) rather than a hardcoded name:
- Dated model names (`gemini-2.5-flash`, `gemini-3.5-flash`, ...) get individually deprecated
  or paid-gated over time — a freshly created API key 404'd on `gemini-2.5-flash` with
  "no longer available to new users".
- `gemini-3.5-flash` specifically requires a funded Prepay plan (402/429 "prepayment credits
  are depleted"), unlike free-tier Flash models.
`gemini-flash-latest` (a Google-maintained alias that always points at their current free-tier
Flash model) avoided both problems and is the default.
"""

import json

import requests

from app.core.config import settings
from app.schemas.explanation import Factor

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "factors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "impact": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                    "description": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "impact", "description", "source_ids"],
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "summary", "confidence", "factors", "limitations"],
}


class GeminiApiError(Exception):
    """Raised on any failure to get a usable analysis from Gemini — caller should fall back."""


def generate_movement_explanation(prompt: str) -> dict:
    if not settings.gemini_api_key:
        raise GeminiApiError("GEMINI_API_KEY is not configured")

    try:
        response = requests.post(
            API_URL.format(model=settings.gemini_model),
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": _RESPONSE_SCHEMA,
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(content)
    except Exception as exc:
        raise GeminiApiError(f"Gemini request failed: {exc}") from exc

    try:
        return {
            "headline": parsed["headline"],
            "summary": parsed["summary"],
            "confidence": parsed["confidence"],
            "factors": [Factor(**factor) for factor in parsed["factors"]],
            "limitations": parsed["limitations"],
        }
    except (KeyError, TypeError) as exc:
        raise GeminiApiError(f"Unexpected Gemini response shape: {exc}") from exc
