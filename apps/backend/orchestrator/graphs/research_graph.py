"""LangGraph research subgraph — query gen → Tavily → filter → enrich."""

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from core.spend import record_spend
from orchestrator.graphs.state import ResearchState
from research.board_evidence import (
    EvidencePacket,
    init_evidence_packet,
    step_enrich_and_summarize,
    step_filter_relevant,
    step_generate_queries,
    step_tavily_search,
)


def _route_after_init(state: ResearchState) -> Literal["generate_queries", "done"]:
    packet = state.get("packet")
    if packet and packet.skipped_reason:
        return "done"
    return "generate_queries"


def _route_after_tavily(state: ResearchState) -> Literal["filter_relevant", "done"]:
    packet = state.get("packet")
    if packet and packet.retrieval_case == "no_sources":
        return "done"
    return "filter_relevant"


def _route_after_filter(state: ResearchState) -> Literal["enrich", "done"]:
    packet = state.get("packet")
    if packet and packet.retrieval_case == "no_relevant":
        return "done"
    return "enrich"


async def node_init(state: ResearchState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    workspace_id = state["workspace_id"]
    packet = await init_evidence_packet(session, workspace_id)
    trace = packet.to_trace() if packet else {}
    return {"packet": packet, "research_trace": trace}


async def node_generate_queries(state: ResearchState, config: RunnableConfig) -> dict:
    packet = state["packet"]
    packet = await step_generate_queries(
        packet, state["question"], state.get("workspace_context", "")
    )
    return {"packet": packet}


async def node_tavily_search(state: ResearchState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    packet, all_results = await step_tavily_search(state["packet"])
    await record_spend(session, "board_research", 0.04)
    return {"packet": packet, "all_results": all_results}


async def node_filter_relevant(state: ResearchState, config: RunnableConfig) -> dict:
    packet, relevant_raw = await step_filter_relevant(
        state["packet"], state["question"], state.get("all_results", [])
    )
    return {"packet": packet, "relevant_raw": relevant_raw}


async def node_enrich(state: ResearchState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    packet = await step_enrich_and_summarize(
        session,
        state["packet"],
        state["question"],
        state.get("relevant_raw", []),
    )
    return {"packet": packet, "research_trace": packet.to_trace()}


async def node_finalize(state: ResearchState, config: RunnableConfig) -> dict:
    packet = state.get("packet") or EvidencePacket()
    return {"packet": packet, "research_trace": packet.to_trace()}


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("init", node_init)
    graph.add_node("generate_queries", node_generate_queries)
    graph.add_node("tavily_search", node_tavily_search)
    graph.add_node("filter_relevant", node_filter_relevant)
    graph.add_node("enrich", node_enrich)
    graph.add_node("finalize", node_finalize)

    graph.add_edge(START, "init")
    graph.add_conditional_edges("init", _route_after_init, {"generate_queries": "generate_queries", "done": "finalize"})
    graph.add_edge("generate_queries", "tavily_search")
    graph.add_conditional_edges(
        "tavily_search", _route_after_tavily, {"filter_relevant": "filter_relevant", "done": "finalize"}
    )
    graph.add_conditional_edges(
        "filter_relevant", _route_after_filter, {"enrich": "enrich", "done": "finalize"}
    )
    graph.add_edge("enrich", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


research_graph = build_research_graph()
