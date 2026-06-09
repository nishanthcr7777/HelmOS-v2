import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AGENT_NAMES, run_agent
from agents.synthesizer import synthesize_board
from beliefs.service import BeliefService


def _as_float(value: object, default: float = 0.5) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
from db.models import BoardSession, Decision, InboxItem
from memory.retrieval import MemoryService


async def _build_context(session: AsyncSession, workspace_id: str, question: str) -> str:
    memory = MemoryService(session)
    chunks = await memory.search(question, workspace_id, limit=8)
    lines = [f"[{c.chunk_type}] {c.content[:800]}" for c in chunks]
    return "\n".join(lines) if lines else "No memory chunks retrieved."


async def run_board_session(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    project_id: str | None = None,
) -> BoardSession:
    beliefs = BeliefService(session)
    beliefs_block = await beliefs.pack_for_prompt(workspace_id)
    context = await _build_context(session, workspace_id, question)

    board = BoardSession(
        workspace_id=workspace_id,
        project_id=project_id,
        question=question,
        status="running",
        agent_outputs=[],
    )
    session.add(board)
    await session.flush()

    tasks = [run_agent(name, question, context, beliefs_block) for name in AGENT_NAMES]
    outputs: list[dict[str, Any]] = list(await asyncio.gather(*tasks))

    synthesis = await synthesize_board(question, outputs, beliefs_block)
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

    board.synthesis = {**synthesis, "decision_id": str(decision.id)}
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
    return board
