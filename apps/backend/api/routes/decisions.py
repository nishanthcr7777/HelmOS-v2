from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DbSession
from db.models import Decision
from schemas.types import DecisionOut

router = APIRouter(prefix="/decisions", tags=["decisions"])


class DecisionPatch(BaseModel):
    status: str


@router.get("")
async def list_decisions(db: DbSession, workspace_id: str, status: str | None = None):
    q = select(Decision).where(Decision.workspace_id == workspace_id)
    if status:
        q = q.where(Decision.status == status)
    q = q.order_by(Decision.updated_at.desc())
    result = await db.execute(q)
    return [DecisionOut.from_row(d) for d in result.scalars().all()]


@router.get("/{decision_id}")
async def get_decision(decision_id: str, db: DbSession):
    result = await db.execute(select(Decision).where(Decision.id == UUID(decision_id)))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Decision not found")
    return DecisionOut.from_row(row)


@router.patch("/{decision_id}")
async def patch_decision(decision_id: str, body: DecisionPatch, db: DbSession):
    result = await db.execute(select(Decision).where(Decision.id == UUID(decision_id)))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Decision not found")
    row.status = body.status
    row.updated_at = datetime.now(timezone.utc)
    if body.status in ("resolved", "rejected"):
        row.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return DecisionOut.from_row(row)
