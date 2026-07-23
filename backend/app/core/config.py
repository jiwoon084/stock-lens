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

    solar_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    dart_api_key: str = ""
    krx_api_key: str = ""

    # KIS Developers (한국투자증권 Open API) 모의투자(demo) 계좌 — 장중 근실시간 현재가 조회용
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_no: str = ""

    # Default provider for POST /api/analysis/date (app/services/llm/factory.py) — "solar" or
    # "gemini" (gemini_provider.py is interface-only for now, see its docstring). Unrelated to
    # the older /api/v1/explanations feature's user-selectable llm_provider request field.
    llm_provider: str = "solar"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
