"""MCP server exposing Stock Lens's stock-analysis capability to external MCP clients (e.g.
Claude Desktop) over stdio.

Direction: Stock Lens *is* the MCP server here (not the other way around) — an external client
asks it things like "why did Samsung Electronics move on 2026-07-21", and it answers using the
exact same Agent/Gateway pipeline the web app already uses. Every tool below is a thin wrapper
over an existing, independently-tested entrypoint (app/services/stock_analysis_service.py,
app/gateway/data_gateway.py, app/services/market_data_service.py) — no new business logic lives
here, matching how app/gateway/data_gateway.py itself is a thin pass-through (see its docstring).

Runs in its OWN virtualenv (backend/.venv-mcp, via backend/requirements-mcp.txt), NOT the main
backend/.venv that runs the FastAPI app and CI. The `mcp` SDK's dependencies (starlette,
pydantic-core, uvicorn — all unpinned/latest) directly conflict with FastAPI 0.115.0's pinned
`starlette<0.39.0` — installing `mcp` into backend/.venv was tried once and it broke the app's
own imports immediately. Since this server never runs inside the deployed web app (it's a local
stdio tool for a human's own MCP client, not a production HTTP surface), keeping it in a fully
separate venv avoids that conflict entirely rather than trying to pin around it.

Run locally:
    cd backend
    .venv-mcp/Scripts/python.exe -m pip install -r requirements-mcp.txt   # once
    .venv-mcp/Scripts/python.exe mcp_server.py

Then point an MCP client (e.g. Claude Desktop's claude_desktop_config.json) at this command.
"""

from app.gateway import data_gateway
from app.services import market_data_service, stock_analysis_service

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="stock-lens",
    instructions=(
        "한국 주식(코스피 상장 종목)의 시세 조회와, 특정 날짜에 주가가 왜 움직였는지에 대한 "
        "AI 분석(공시·뉴스 근거 포함)을 제공합니다. 종목은 6자리 티커(예: 삼성전자=005930)로 "
        "지정합니다. '추천'은 제공하지 않으며, 공개된 공시·뉴스 근거에 기반한 설명만 제공합니다."
    ),
)


def _direction_for(ticker: str, selected_date: str) -> str:
    prices = data_gateway.get_price_series_with_live_today(ticker)
    point = next((p for p in prices if p.time == selected_date), None)
    if point is None:
        return "flat"
    if point.change_percent > 0:
        return "up"
    if point.change_percent < 0:
        return "down"
    return "flat"


@mcp.tool()
def analyze_stock_movement(ticker: str, selected_date: str) -> dict:
    """지정한 종목이 지정한 날짜(YYYY-MM-DD)에 왜 움직였는지 분석합니다.

    실제 공시·뉴스 근거를 검색해 LLM으로 종합한 원인 후보, 앞으로 지켜볼 신호, 근거 원문
    자료를 반환합니다. 웹 앱의 POST /api/analysis/date와 동일한 파이프라인(Agent: LangGraph
    fetch_market_data -> retrieve_evidence -> build_llm_input -> generate_analysis)을 그대로
    호출합니다.
    """
    response = stock_analysis_service.analyze_date(ticker, selected_date)
    return response.model_dump()


@mcp.tool()
def search_disclosures_and_news(ticker: str, selected_date: str) -> list[dict]:
    """지정한 종목·날짜 전후의 공시·뉴스 원문 근거를 검색합니다 (LLM 종합 없이 원본만).

    analyze_stock_movement이 이미 골라 종합한 결과가 아니라, 그 판단의 재료가 된 원본
    문서 목록 자체가 필요할 때 사용합니다.
    """
    stock = data_gateway.get_stock(ticker)
    if stock is None:
        raise ValueError(f"Unknown ticker: {ticker}")

    direction = _direction_for(ticker, selected_date)
    documents = data_gateway.get_related_documents(ticker=ticker, selected_date=selected_date, direction=direction)
    return [d.model_dump() for d in documents]


@mcp.tool()
def get_price_series(ticker: str, limit: int = 30) -> list[dict]:
    """지정한 종목의 최근 일봉 시세를 반환합니다 (기본 최근 30거래일).

    공식 KRX 시세(data.go.kr) 기반이며, 키가 없거나 실패 시 결정론적 mock 데이터로 대체됩니다
    (웹 앱의 시세 조회와 동일한 폴백 규칙).
    """
    stock = data_gateway.get_stock(ticker)
    if stock is None:
        raise ValueError(f"Unknown ticker: {ticker}")

    prices = market_data_service.get_price_series(ticker)
    return [p.model_dump() for p in prices[-limit:]]


if __name__ == "__main__":
    mcp.run(transport="stdio")
