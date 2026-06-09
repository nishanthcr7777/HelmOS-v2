from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


def _dt(v: datetime) -> str:
    return v.isoformat().replace("+00:00", "Z") if v.tzinfo else v.isoformat() + "Z"


class WorkspaceOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "WorkspaceOut":
        return cls(id=row.id, name=row.name, description=row.description)


class ProjectOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    status: str

    @classmethod
    def from_row(cls, row: Any) -> "ProjectOut":
        return cls(id=row.id, workspace_id=row.workspace_id, name=row.name, status=row.status)


class StrategicBeliefOut(BaseModel):
    id: str
    workspace_id: str
    content: str
    confidence: float = 0.8
    rationale: str | None = None
    override_conditions: list[str] = Field(default_factory=list)
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "StrategicBeliefOut":
        overrides = row.override_conditions if hasattr(row, "override_conditions") else []
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            content=row.content,
            confidence=float(getattr(row, "confidence", 0.8) or 0.8),
            rationale=getattr(row, "rationale", None),
            override_conditions=list(overrides or []),
            created_at=_dt(row.created_at),
        )


class MemoryChunkOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None = None
    chunk_type: str
    content: str
    summary: str | None = None
    source_url: str | None = None
    source_file: str | None = None
    entity_name: str | None = None
    fetched_at: str | None = None
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "MemoryChunkOut":
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            project_id=row.project_id,
            chunk_type=row.chunk_type,
            content=row.content,
            summary=row.summary,
            source_url=row.source_url,
            source_file=row.source_file,
            entity_name=row.entity_name,
            fetched_at=_dt(row.fetched_at) if row.fetched_at else None,
            created_at=_dt(row.created_at),
        )


class EntityCardOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    entity_type: str
    last_researched_at: str | None = None
    research_age_days: int | None = None
    confidence: float
    linked_decision_ids: list[str]
    summary: str

    @classmethod
    def from_row(cls, row: Any) -> "EntityCardOut":
        from datetime import timezone

        age = None
        if row.last_researched_at:
            delta = datetime.now(timezone.utc) - row.last_researched_at.replace(tzinfo=timezone.utc)
            age = max(0, delta.days)
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            name=row.name,
            entity_type=row.entity_type,
            last_researched_at=_dt(row.last_researched_at) if row.last_researched_at else None,
            research_age_days=age,
            confidence=row.confidence,
            linked_decision_ids=list(row.linked_decision_ids or []),
            summary=row.summary,
        )


class WorkspaceProfileOut(BaseModel):
    workspace_id: str
    metrics: list[dict[str, str]]
    context_lines: list[str]


class FounderStateOut(BaseModel):
    decision_load: str
    blocked_items: int
    open_decisions: int
    research_needed: int


class DecisionOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None = None
    title: str
    question: str
    synthesis: str
    verdict: str | None = None
    confidence: float | None = None
    evidence_score: float | None = None
    risk_level: str | None = None
    unknowns_level: str | None = None
    agent_outputs: list[Any] = Field(default_factory=list)
    risks: list[Any] = Field(default_factory=list)
    unknowns: list[Any] = Field(default_factory=list)
    assumptions: list[Any] = Field(default_factory=list)
    next_action: str | None = None
    status: str
    resolved_at: str | None = None
    updated_at: str
    created_at: str
    timeline: list[Any] | None = None

    @classmethod
    def from_row(cls, row: Any) -> "DecisionOut":
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            project_id=row.project_id,
            title=row.title or row.question[:80],
            question=row.question,
            synthesis=row.synthesis or "",
            verdict=row.verdict,
            confidence=row.confidence,
            evidence_score=row.evidence_score,
            risk_level=row.risk_level,
            unknowns_level=row.unknowns_level,
            agent_outputs=row.agent_outputs or [],
            risks=row.risks or [],
            unknowns=row.unknowns or [],
            assumptions=row.assumptions or [],
            next_action=row.next_action,
            status=row.status,
            resolved_at=_dt(row.resolved_at) if row.resolved_at else None,
            updated_at=_dt(row.updated_at),
            created_at=_dt(row.created_at),
            timeline=row.timeline or [],
        )


class InboxItemOut(BaseModel):
    id: str
    workspace_id: str
    decision_id: str | None = None
    item_type: str
    title: str
    body: str | None = None
    priority: str
    status: str
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "InboxItemOut":
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            decision_id=str(row.decision_id) if row.decision_id else None,
            item_type=row.item_type,
            title=row.title,
            body=row.body,
            priority=row.priority,
            status=row.status,
            created_at=_dt(row.created_at),
        )


class BoardSessionOut(BaseModel):
    id: str
    workspace_id: str
    project_id: str | None = None
    question: str
    status: str
    decision_id: str | None = None
    board_mode: str | None = None
    agent_outputs: list[Any] = Field(default_factory=list)
    synthesis: dict[str, Any] | None = None
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "BoardSessionOut":
        synthesis = row.synthesis
        decision_id = None
        board_mode = None
        if isinstance(synthesis, dict):
            decision_id = synthesis.get("decision_id")
            board_mode = synthesis.get("board_mode")
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            project_id=row.project_id,
            question=row.question,
            status=row.status,
            decision_id=str(decision_id) if decision_id else None,
            board_mode=str(board_mode) if board_mode else None,
            agent_outputs=row.agent_outputs or [],
            synthesis=synthesis,
            created_at=_dt(row.created_at),
        )


class ResearchJobOut(BaseModel):
    id: str
    workspace_id: str
    entity_name: str
    queries: list[str]
    step: str
    sources: list[Any] = Field(default_factory=list)
    created_at: str

    @classmethod
    def from_row(cls, row: Any) -> "ResearchJobOut":
        return cls(
            id=str(row.id),
            workspace_id=row.workspace_id,
            entity_name=row.entity_name,
            queries=list(row.queries or []),
            step=row.step,
            sources=list(row.sources or []),
            created_at=_dt(row.created_at),
        )


class DashboardPayloadOut(BaseModel):
    founder_state: FounderStateOut
    todays_focus: list[dict[str, Any]]
    active_decisions: list[DecisionOut]
    board_alerts: list[dict[str, Any]]
    opportunities: list[dict[str, Any]]
