import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, explanations, health, stocks
from app.core.config import settings

# Without this, the root logger's default level (WARNING) silently drops every logger.info()
# call in the codebase — including the LLM call latency/outcome and routing-decision logs in
# stock_analysis_service.py, which is most of what backs the "we monitor LLM calls" claim.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Stock Lens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
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
