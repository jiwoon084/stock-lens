import logging

# Must run before importing routes/services below — several of them (e.g.
# retrieval_service.py's on-disk embedding cache) log at import time, as a module-level
# statement runs the moment it's first imported, not deferred until a request comes in. Without
# this, the root logger's default level (WARNING) silently drops every logger.info() call in the
# codebase — including the LLM call latency/outcome and routing-decision logs in
# stock_analysis_service.py, which is most of what backs the "we monitor LLM calls" claim.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.routes import analysis, explanations, health, stocks  # noqa: E402
from app.core.config import settings  # noqa: E402

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
