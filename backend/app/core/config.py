from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 루트 .env를 항상 참조 (uvicorn을 backend/에서 실행해도 상대경로 ".env"가 backend/.env를
# 가리켜 실패하지 않도록 절대경로로 고정 — Docker에는 .env가 아예 없어서 이 값은 무시되고
# environment: / docker run -e로 넘긴 실제 환경변수가 그대로 읽힘)
_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT_ENV_FILE, extra="ignore")

    port: int = 8080
    allowed_origins: str = "http://localhost:5173"

    # "mock"이면 항상 mock 분석만 사용(테스트/오프라인용). 그 외("live" 등)면 근거 자료 개수로
    # SOLAR/Gemini Flash 중 하나로 라우팅하고(app/services/llm_service.py), 그 provider가 키가
    # 없거나 실패하면 나머지 하나를 안전망으로 시도, 둘 다 안 되면 mock으로 내려감.
    llm_provider: str = "mock"
    llm_timeout: int = 30
    llm_num_retries: int = 2

    upstage_api_key: str = ""
    solar_model: str = "solar-pro2"
    solar_base_url: str = "https://api.upstage.ai/v1/solar"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    dart_api_key: str = ""
    krx_api_key: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
