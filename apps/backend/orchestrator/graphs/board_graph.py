"""LangGraph board workflow — context → research → agents → synthesis → persist."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AGENT_NAMES, run_agent
from agents.board_modes import BoardMode
from agents.researcher import run_researcher_agent
from agents.synthesizer import synthesize_board
from beliefs.service import BeliefService
from db.models import BoardSession, Decision, InboxItem
from memory.retrieval import MemoryService
from orchestrator.context_builder import build_board_context
from orchestrator.graphs.research_graph import research_graph
from orchestrator.graphs.state import BoardState
from research.board_evidence import EvidencePacket


def _as_float(value: object, default: float = 0.5) -> float:
    try:
        n = float(value)  # type: ignore[arg-type]
        if n != n:
            return default
        return max(0.0, min(1.0, n))
    except (TypeError, ValueError):
        return default


async def node_load_context(state: BoardState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    workspace_id = state["workspace_id"]
    project_id = state.get("project_id")
    question = state["question"]

    beliefs = BeliefService(session)
    beliefs_list = await beliefs.list_active(workspace_id)
    beliefs_block = await beliefs.pack_for_prompt(workspace_id)

    memory_result = await MemoryService(session).search(
        question, workspace_id, project_id=project_id, limit=8
    )
    board_ctx = await build_board_context(
        session,
        workspace_id,
        question,
        project_id,
        memory_result,
        beliefs_count=len(beliefs_list),
        research_trace=None,
    )

    return {
        "beliefs_list": beliefs_list,
        "beliefs_block": beliefs_block,
        "memory_result": memory_result,
        "board_ctx_text": board_ctx.text,
        "board_ctx_trace": board_ctx.trace,
    }


async def node_gather_research(state: BoardState, config: RunnableConfig) -> dict:
    research_result = await research_graph.ainvoke(
        {
            "question": state["question"],
            "workspace_id": state["workspace_id"],
            "workspace_context": state.get("board_ctx_text", "")[:2000],
        },
        config=config,
    )
    packet: EvidencePacket = research_result.get("packet") or EvidencePacket()
    research_trace = research_result.get("research_trace") or packet.to_trace()

    board_ctx_trace = dict(state.get("board_ctx_trace") or {})
    board_ctx_trace["research"] = research_trace
    board_ctx_trace["research_sources_count"] = research_trace.get("passed_to_researcher", 0)

    return {
        "evidence_packet": packet,
        "research_trace": research_trace,
        "board_ctx_trace": board_ctx_trace,
    }


async def node_init_board(state: BoardState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    board = BoardSession(
        workspace_id=state["workspace_id"],
        project_id=state.get("project_id"),
        question=state["question"],
        status="running",
        agent_outputs=[],
    )
    session.add(board)
    await session.flush()
    return {"board_session": board}


async def node_run_agents(state: BoardState, config: RunnableConfig) -> dict:
    question = state["question"]
    board_mode: BoardMode = state.get("board_mode", "decision")  # type: ignore[assignment]
    beliefs_block = state.get("beliefs_block", "")
    shared_context = state.get("board_ctx_text", "")
    evidence_packet = state.get("evidence_packet") or EvidencePacket()
    researcher_debug: dict[str, Any] = {}

    async def _run_one(name: str) -> dict[str, Any]:
        if name == "researcher":
            out, dbg = await run_researcher_agent(
                question, evidence_packet, board_mode=board_mode
            )
            researcher_debug.update(dbg)
            return out
        return await run_agent(
            name, question, shared_context, beliefs_block, board_mode=board_mode
        )

    outputs: list[dict[str, Any]] = list(
        await asyncio.gather(*[_run_one(name) for name in AGENT_NAMES])
    )
    return {"agent_outputs": outputs, "researcher_debug": researcher_debug}


async def node_synthesize(state: BoardState, config: RunnableConfig) -> dict:
    board_mode: BoardMode = state.get("board_mode", "decision")  # type: ignore[assignment]
    synthesis = await synthesize_board(
        state["question"],
        state.get("agent_outputs", []),
        state.get("beliefs_block", ""),
        board_mode=board_mode,
    )
    return {"synthesis": synthesis}


async def node_persist(state: BoardState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    board: BoardSession = state["board_session"]
    synthesis = state.get("synthesis") or {}
    outputs = state.get("agent_outputs") or []
    board_mode: BoardMode = state.get("board_mode", "decision")  # type: ignore[assignment]
    workspace_id = state["workspace_id"]
    question = state["question"]
    project_id = state.get("project_id")
    researcher_debug = state.get("researcher_debug") or {}
    board_ctx_trace = state.get("board_ctx_trace") or {}

    board.agent_outputs = outputs
    board.status = "complete"

    decision = Decision(
        workspace_id=workspace_id,
        project_id=project_id,
        title=question[:120],
        question=question,
        synthesis=synthesis.get("recommendation", ""),
        verdict=synthesis.get("verdict"),
        confidence=_as_float(synthesis.get("confidence"), 0.5),
        evidence_score=_as_float(synthesis.get("evidence_score"), 0.5),
        risk_level="moderate",
        unknowns_level=synthesis.get("unknowns_level", "moderate"),
        agent_outputs=outputs,
        risks=synthesis.get("risks", []),
        unknowns=synthesis.get("unknowns", []),
        assumptions=synthesis.get("assumptions", []),
        next_action=synthesis.get("next_action"),
        status="open",
        timeline=[
            {
                "id": str(uuid.uuid4()),
                "stage": "board",
                "label": "Board",
                "summary": synthesis.get("recommendation", "")[:300],
                "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        ],
    )
    session.add(decision)
    await session.flush()

    context_trace = {**board_ctx_trace, "researcher": researcher_debug}
    board.synthesis = {
        **synthesis,
        "decision_id": str(decision.id),
        "board_mode": board_mode,
        "context_trace": context_trace,
    }
    await session.flush()

    if synthesis.get("verdict") in ("conditional", "needs_research", "lean_against"):
        session.add(
            InboxItem(
                workspace_id=workspace_id,
                decision_id=decision.id,
                item_type="unresolved_decision",
                title=f"Board: {question[:80]}",
                body=synthesis.get("next_action"),
                priority="high" if synthesis.get("unknowns_level") == "high" else "medium",
            )
        )

    verdicts = {o.get("verdict") for o in outputs}
    if len(verdicts) > 2:
        session.add(
            InboxItem(
                workspace_id=workspace_id,
                decision_id=decision.id,
                item_type="conflict",
                title="Conflicting agent opinions",
                body=f"Agents disagree on: {question[:100]}",
                priority="high",
            )
        )

    await session.flush()
    return {"board_session": board, "decision_id": str(decision.id)}


def build_board_graph():
    graph = StateGraph(BoardState)

    graph.add_node("load_context", node_load_context)
    graph.add_node("gather_research", node_gather_research)
    graph.add_node("init_board", node_init_board)
    graph.add_node("run_agents", node_run_agents)
    graph.add_node("synthesize", node_synthesize)
    graph.add_node("persist", node_persist)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "gather_research")
    graph.add_edge("gather_research", "init_board")
    graph.add_edge("init_board", "run_agents")
    graph.add_edge("run_agents", "synthesize")
    graph.add_edge("synthesize", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


board_graph = build_board_graph()


async def run_board_session_graph(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    project_id: str | None = None,
    board_mode: BoardMode = "decision",
) -> BoardSession:
    final_state = await board_graph.ainvoke(
        {
            "question": question,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "board_mode": board_mode,
        },
        config={"configurable": {"session": session}},
    )
    return final_state["board_session"]
