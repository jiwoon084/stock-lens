from app.core.config import settings

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .solar_provider import SolarProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "solar": SolarProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str | None = None) -> LLMProvider:
    provider_name = (name or settings.llm_provider or "solar").lower()
    provider_cls = _PROVIDERS.get(provider_name, SolarProvider)
    return provider_cls()
