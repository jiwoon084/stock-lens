"""Assembles the stock-analysis LangGraph: fetch_market_data -> retrieve_evidence ->
build_llm_input -> generate_analysis. See app/agent/nodes.py for what each step does and
app/agent/state.py for the state shape.

app/services/stock_analysis_service.analyze_date() imports get_graph() via a *local* import
inside the function body, not at this module's top level — nodes.py imports
stock_analysis_service, so importing this module from stock_analysis_service's top level would
be circular. By the time analyze_date() actually runs, stock_analysis_service has already
finished loading, so the local import just returns the cached module — see nodes.py's docstring.
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
