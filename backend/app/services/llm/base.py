"""Common interface for stock-analysis LLM providers.

Kept separate from app/services/llm_service.py + solar_client.py/gemini_client.py, which
serve the older /api/v1/explanations movement-explanation feature and its user-selectable
SOLAR/Gemini toggle — that routing logic is intentionally untouched (see CLAUDE.md section 9).
This module backs the newer /api/analysis/date endpoint only.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProviderError(Exception):
    """Raised when a provider fails to produce usable output — caller should retry once, then
    fall back to the deterministic rule-based analysis.
    """


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, system_prompt: str, user_context: dict[str, Any]) -> str:
        """Return the raw JSON string produced by the model for the given context."""
