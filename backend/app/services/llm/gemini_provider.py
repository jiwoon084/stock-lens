"""Stock-analysis LLM provider backed by Google's Gemini API.

Was interface-only until now (see git history / CLAUDE.md section 16) — this is the real
implementation, needed so complexity-based routing (stock_analysis_service._select_provider)
can actually send "easy" requests to Gemini Flash instead of always falling through to the
rule-based fallback. Mirrors solar_provider.py's shape (system prompt + JSON-dumped context in,
raw JSON string out) but issues its own request in Gemini's request/response format — reuses
app/services/gemini_client.py's API_URL/model-name gotchas (see that module's docstring) rather
than redefining them, but not its response schema: that client's Factor-based shape is for the
older movement-explanation feature, unrelated to this one's chart_card/detail_panel schema.

Unlike gemini_client.py, this does NOT constrain the response with `responseSchema` — the
chart_card/detail_panel shape has too many nested optional fields to hand-write a schema worth
maintaining twice. Relies on the same system prompt (which already spells out the JSON shape) and
the same downstream pydantic validation/sanitization in stock_analysis_service.py that already
distrusts any LLM output — consistent with SolarProvider, which takes the identical approach.
"""

import json
from typing import Any

import requests

from app.core.config import settings
from app.services import gemini_client

from .base import LLMProvider, LLMProviderError


class GeminiProvider(LLMProvider):
    name = "gemini"

    def generate(self, system_prompt: str, user_context: dict[str, Any]) -> str:
        if not settings.gemini_api_key:
            raise LLMProviderError("GEMINI_API_KEY is not configured")

        try:
            response = requests.post(
                gemini_client.API_URL.format(model=settings.gemini_model),
                headers={"x-goog-api-key": settings.gemini_api_key},
                json={
                    "contents": [
                        {"role": "user", "parts": [{"text": json.dumps(user_context, ensure_ascii=False)}]}
                    ],
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "generationConfig": {"responseMimeType": "application/json"},
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc
