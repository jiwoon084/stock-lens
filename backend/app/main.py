import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, explanations, health, stocks
from app.core.config import settings

# Without this, the root logger's default level (WARNING) silently drops every logger.info()
# call in the codebase — including the LLM call latency/outcome and routing-decision logs in
# stock_analysis_service.py, which is most of what backs the "we monitor LLM calls" claim.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Stock Lens API",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    # No cookie/session auth anywhere in this app, so there's nothing for credentialed
    # cross-origin requests to carry — off by default rather than left on unnecessarily.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(explanations.router)
app.include_router(analysis.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port)
