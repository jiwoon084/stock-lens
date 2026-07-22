"""Stock-analysis LLM provider backed by Upstage's SOLAR API.

Reuses the same endpoint/model constants as app/services/solar_client.py (the existing
movement-explanation SOLAR client) instead of redefining them, but issues its own request
here because the response shape (chart_card/detail_panel) is entirely different from that
older client's Factor-based schema.
"""

import json
from typing import Any

import requests

from app.core.config import settings
from app.services import solar_client

from .base import LLMProvider, LLMProviderError


class SolarProvider(LLMProvider):
    name = "solar"

    def generate(self, system_prompt: str, user_context: dict[str, Any]) -> str:
        if not settings.solar_api_key:
            raise LLMProviderError("SOLAR_API_KEY is not configured")

        try:
            response = requests.post(
                solar_client.API_URL,
                headers={"Authorization": f"Bearer {settings.solar_api_key}"},
                json={
                    "model": solar_client.MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": json.dumps(user_context, ensure_ascii=False),
                        },
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=20,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMProviderError(f"SOLAR request failed: {exc}") from exc
