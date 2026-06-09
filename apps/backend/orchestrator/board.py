import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AGENT_NAMES, run_agent
from agents.board_modes import BoardMode
from agents.synthesizer import synthesize_board
from beliefs.service import BeliefService
from db.models import BoardSession, Decision, InboxItem
from memory.retrieval import MemoryService
from orchestrator.context_builder import build_board_context


def _as_float(value: object, default: float = 0.5) -> float:
    try:
        n = float(value)  # type: ignore[arg-type]
        if n != n:
            return default
        return max(0.0, min(1.0, n))
    except (TypeError, ValueError):
        return default


async def run_board_session(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    project_id: str | None = None,
    board_mode: BoardMode = "decision",
) -> BoardSession:
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
    )
    context = board_ctx.text

    board = BoardSession(
        workspace_id=workspace_id,
        project_id=project_id,
        question=question,
        status="running",
        agent_outputs=[],
    )
    session.add(board)
    await session.flush()

    tasks = [
        run_agent(name, question, context, beliefs_block, board_mode=board_mode)
        for name in AGENT_NAMES
    ]
    outputs: list[dict[str, Any]] = list(await asyncio.gather(*tasks))

    synthesis = await synthesize_board(question, outputs, beliefs_block, board_mode=board_mode)
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

    board.synthesis = {
        **synthesis,
        "decision_id": str(decision.id),
        "board_mode": board_mode,
        "context_trace": board_ctx.trace,
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
    return board
