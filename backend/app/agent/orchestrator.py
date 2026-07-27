"""Orchestrator: the single entrypoint that runs the stock-analysis Agent (app/agent/graph.py +
nodes.py) end to end and returns its final state.

Everything above this line — the FastAPI route, app/services/stock_analysis_service.py — talks
to the Agent only through run_analysis(), never by importing the compiled graph or its nodes
directly. This module doesn't add new sequencing logic of its own: graph.py's compiled
StateGraph already *is* the orchestration (it sequences fetch_market_data -> retrieve_evidence ->
build_llm_input -> generate_analysis and threads the shared state between them). This file just
gives that role one explicit name and one call site, matching the course's requirement for
Agent / Gateway / Orchestrator to be distinct, named components (see CLAUDE.md).
"""

from typing import Any

from app.agent.graph import get_graph


def run_analysis(ticker: str, selected_date: str, llm_provider: str | None = None) -> dict[str, Any]:
    graph = get_graph()
    return graph.invoke({"ticker": ticker, "selected_date": selected_date, "llm_provider": llm_provider})
