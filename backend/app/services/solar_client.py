"""Real headline/summary/factor generation via Upstage's SOLAR API.

Uses the OpenAI-compatible chat completions endpoint (verified against a real call on
2026-07-21) with a JSON-schema-constrained response_format, so the model's output is
guaranteed to parse into our Factor/limitations shape instead of free-form text.
`llm_service.py` is the only caller and falls back to its rule-based response on any
`SolarApiError` — see docs/project-plan.md M3.
"""

import json

import requests

from app.core.config import settings
from app.schemas.explanation import Factor

API_URL = "https://api.upstage.ai/v1/chat/completions"
MODEL = "solar-pro2"

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
                "additionalProperties": False,
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "summary", "confidence", "factors", "limitations"],
    "additionalProperties": False,
}


class SolarApiError(Exception):
    """Raised on any failure to get a usable analysis from SOLAR — caller should fall back."""


def generate_movement_explanation(prompt: str) -> dict:
    if not settings.solar_api_key:
        raise SolarApiError("SOLAR_API_KEY is not configured")

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {settings.solar_api_key}"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "movement_explanation",
                        "strict": True,
                        "schema": _RESPONSE_SCHEMA,
                    },
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception as exc:
        raise SolarApiError(f"SOLAR request failed: {exc}") from exc

    try:
        return {
            "headline": parsed["headline"],
            "summary": parsed["summary"],
            "confidence": parsed["confidence"],
            "factors": [Factor(**factor) for factor in parsed["factors"]],
            "limitations": parsed["limitations"],
        }
    except (KeyError, TypeError) as exc:
        raise SolarApiError(f"Unexpected SOLAR response shape: {exc}") from exc
