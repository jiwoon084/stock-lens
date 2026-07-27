"""Gateway layer: the single boundary the stock-analysis Agent (app/agent/nodes.py) crosses to
reach anything outside this process — market data and disclosure/news retrieval today, via
data_gateway.py.

These are thin pass-throughs over the existing, independently-tested services
(app/services/market_data_service.py, app/services/retrieval_service.py) — no new fetching/
caching/fallback logic lives here, and none of it moved. The point of this module is a single
named seam between the Agent's orchestration logic and external systems: one place to add
logging, retries, or swap a data source later, and a concrete "Gateway" component for the
Agent / Gateway / Orchestrator architecture the course asked for (see CLAUDE.md).

The LLM side already had an equivalent seam before this package existed: app/services/llm/base.py
(the LLMProvider interface) + app/services/llm/factory.py (provider selection) hide SOLAR vs.
Gemini behind one call shape. That pair fills the same role for LLM calls that data_gateway.py
fills here for data calls — nothing needed to move for that one, only naming it.
"""
