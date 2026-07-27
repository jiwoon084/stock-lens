"""Assembles the stock-analysis LangGraph: fetch_market_data -> retrieve_evidence ->
build_llm_input -> generate_analysis. See app/agent/nodes.py for what each step does and
app/agent/state.py for the state shape.

This compiled StateGraph is the Orchestrator in this project's Agent / Gateway / Orchestrator
split — it's the thing that actually sequences the Agent's steps and threads state between
them. app/agent/orchestrator.py just gives that role one name and one call site
(run_analysis()); nothing here changes because of it.

Callers should go through app/agent/orchestrator.run_analysis(), not get_graph() directly —
that's the only reason orchestrator.py exists.
"""

from langgraph.graph import END, StateGraph

from app.agent import nodes
from app.agent.state import AnalysisGraphState

_compiled_graph = None


def build_graph():
    graph = StateGraph(AnalysisGraphState)
    graph.add_node("fetch_market_data", nodes.fetch_market_data)
    graph.add_node("retrieve_evidence", nodes.retrieve_evidence)
    graph.add_node("build_llm_input", nodes.build_llm_input)
    graph.add_node("generate_analysis", nodes.generate_analysis)

    graph.set_entry_point("fetch_market_data")
    graph.add_edge("fetch_market_data", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "build_llm_input")
    graph.add_edge("build_llm_input", "generate_analysis")
    graph.add_edge("generate_analysis", END)

    return graph.compile()


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph
