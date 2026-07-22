"""Stock-analysis LLM provider interface for Gemini — reserved for future use.

app/services/gemini_client.py already has a real, working Gemini integration for the older
movement-explanation feature, but wiring a real Gemini call into this newer chart_card/
detail_panel schema is explicitly out of scope for this change (see CLAUDE.md item 16 in the
task brief this module was built for). This class only exists so factory.py has a second
provider to select and so a real implementation can be dropped in later without touching the
call sites.
"""

from typing import Any

from .base import LLMProvider, LLMProviderError


class GeminiProvider(LLMProvider):
    name = "gemini"

    def generate(self, system_prompt: str, user_context: dict[str, Any]) -> str:
        raise LLMProviderError(
            "Gemini provider for stock analysis is not implemented yet — interface reserved "
            "for future use."
        )
