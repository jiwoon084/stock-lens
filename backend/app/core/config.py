from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path so this resolves the same whether uvicorn is started from backend/ (local dev)
# or elsewhere — Docker has no .env file at all, so this is simply ignored there (real env vars
# passed via `environment:`/`docker run -e` are read regardless of env_file).
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV_FILE, extra="ignore")

    port: int = 8080
    allowed_origins: str = "http://localhost:5173"

    llm_provider: str = "mock"
    solar_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    dart_api_key: str = ""
    krx_api_key: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
