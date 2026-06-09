import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BoardSession, Decision, Entity, WorkspaceProfile
from memory.retrieval import MemorySearchResult

MAX_CONTEXT_CHARS = 12000


@dataclass
class BoardContext:
    text: str
    trace: dict[str, Any]


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text)}


def _overlap_score(query: str, text: str) -> int:
    q_words = _tokenize(query)
    if not q_words:
        return 0
    return len(q_words & _tokenize(text))


def _truncate_sections(sections: list[tuple[str, str]], max_chars: int) -> str:
    """Drop lower-priority sections first until within budget."""
    priority_order = [
        "## Memory evidence",
        "## Workspace context",
        "## Known entities",
        "## Recent decisions",
        "## Prior board sessions",
    ]

    def build(active: list[tuple[str, str]]) -> str:
        return "\n\n".join(body for _, body in active if body.strip())

    active = list(sections)
    while active and len(build(active)) > max_chars:
        dropped = False
        for title in reversed(priority_order):
            for i, (t, _) in enumerate(active):
                if t == title:
                    active.pop(i)
                    dropped = True
                    break
            if dropped:
                break
        if not dropped:
            break

    text = build(active)
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."
    return text


async def build_board_context(
    session: AsyncSession,
    workspace_id: str,
    question: str,
    project_id: str | None,
    memory_result: MemorySearchResult,
    beliefs_count: int,
) -> BoardContext:
    profile_lines_count = 0
    entities_count = 0
    decisions_injected = 0
    board_sessions_injected = 0

    workspace_section = ""
    profile = (
        await session.execute(
            select(WorkspaceProfile).where(WorkspaceProfile.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()
    if profile and profile.context_lines:
        lines = [str(line) for line in profile.context_lines if str(line).strip()]
        profile_lines_count = len(lines)
        if lines:
            workspace_section = "## Workspace context\n" + "\n".join(f"- {line}" for line in lines)

    entities_section = ""
    entity_rows = (
        await session.execute(
            select(Entity)
            .where(Entity.workspace_id == workspace_id)
            .order_by(Entity.confidence.desc())
            .limit(10)
        )
    ).scalars().all()
    entities_count = len(entity_rows)
    if entity_rows:
        entity_lines = [
            f"- {e.entity_type} {e.name}: {e.summary} (confidence: {int(round(e.confidence * 100))}%)"
            for e in entity_rows
        ]
        entities_section = "## Known entities\n" + "\n".join(entity_lines)

    decisions_section = ""
    decision_rows = (
        await session.execute(
            select(Decision)
            .where(Decision.workspace_id == workspace_id)
            .order_by(Decision.updated_at.desc())
            .limit(10)
        )
    ).scalars().all()
    if decision_rows:
        ranked = sorted(
            decision_rows,
            key=lambda d: _overlap_score(question, d.question or ""),
            reverse=True,
        )
        top = ranked[:3]
        decisions_injected = len(top)
        dec_lines = [
            f"- {d.question} → {d.verdict or 'n/a'} ({d.status}): {(d.synthesis or '')[:200]}"
            for d in top
        ]
        decisions_section = "## Recent decisions\n" + "\n".join(dec_lines)

    sessions_section = ""
    session_rows = (
        await session.execute(
            select(BoardSession)
            .where(BoardSession.workspace_id == workspace_id, BoardSession.status == "complete")
            .order_by(BoardSession.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    if session_rows:
        ranked = sorted(
            session_rows,
            key=lambda s: _overlap_score(question, s.question or ""),
            reverse=True,
        )
        top = ranked[:3]
        board_sessions_injected = len(top)
        sess_lines = []
        for s in top:
            rec = ""
            if isinstance(s.synthesis, dict):
                rec = str(s.synthesis.get("recommendation") or "")[:200]
            sess_lines.append(f"- {s.question} → {rec}")
        sessions_section = "## Prior board sessions\n" + "\n".join(sess_lines)

    memory_section = ""
    if memory_result.chunks:
        mem_lines = [f"[{c.chunk_type}] {c.content[:800]}" for c in memory_result.chunks]
        memory_section = "## Memory evidence\n" + "\n".join(mem_lines)
    else:
        memory_section = "## Memory evidence\nNo memory chunks retrieved."

    sections = [
        ("## Workspace context", workspace_section),
        ("## Known entities", entities_section),
        ("## Recent decisions", decisions_section),
        ("## Prior board sessions", sessions_section),
        ("## Memory evidence", memory_section),
    ]
    text = _truncate_sections(sections, MAX_CONTEXT_CHARS)

    agent_context_chars = len(text)
    agent_context_tokens = agent_context_chars // 4

    trace = {
        "beliefs_count": beliefs_count,
        "profile_lines_count": profile_lines_count,
        "entities_count": entities_count,
        "decisions_injected": decisions_injected,
        "board_sessions_injected": board_sessions_injected,
        "memory": {
            "retrieved_chunks_count": memory_result.retrieved_chunks_count,
            "vector_hits": memory_result.vector_hits,
            "text_hits": memory_result.text_hits,
            "used_text_fallback": memory_result.used_text_fallback,
            "used_recent_fallback": memory_result.used_recent_fallback,
            "chunk_ids": [c.id for c in memory_result.chunks],
        },
        "agent_context_chars": agent_context_chars,
        "agent_context_tokens": agent_context_tokens,
    }

    return BoardContext(text=text, trace=trace)
