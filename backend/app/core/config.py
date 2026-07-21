from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 루트 .env를 항상 참조 (uvicorn을 backend/에서 실행해도 상대경로 ".env"가 backend/.env를
# 가리켜 실패하지 않도록 절대경로로 고정)
_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV_FILE, extra="ignore")

    port: int = 8080
    allowed_origins: str = "http://localhost:5173"

    # "mock"이면 항상 mock 분석만 사용(테스트/오프라인용). 그 외("live" 등)면 아래 3단 폴백을 시도하고,
    # 전부 실패하거나 키가 하나도 없으면 자동으로 mock으로 내려감.
    llm_provider: str = "mock"
    llm_timeout: int = 30
    llm_num_retries: int = 2

    upstage_api_key: str = ""
    solar_model: str = "solar-pro2"
    solar_base_url: str = "https://api.upstage.ai/v1/solar"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
