from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import DbSession
from beliefs.service import BeliefService
from schemas.types import StrategicBeliefOut

router = APIRouter(prefix="/beliefs", tags=["beliefs"])


class BeliefCreate(BaseModel):
    workspace_id: str
    content: str
    confidence: float = 0.8
    rationale: str | None = None
    override_conditions: list[str] | None = None


class BeliefPatch(BaseModel):
    content: str | None = None
    sort_order: int | None = None
    status: str | None = None
    confidence: float | None = None
    rationale: str | None = None
    override_conditions: list[str] | None = None


@router.get("")
async def list_beliefs(workspace_id: str, db: DbSession):
    svc = BeliefService(db)
    beliefs = await svc.list_active(workspace_id)
    return [StrategicBeliefOut.from_row(b) for b in beliefs]


@router.post("", status_code=201)
async def create_belief(body: BeliefCreate, db: DbSession):
    svc = BeliefService(db)
    belief = await svc.create(
        body.workspace_id,
        body.content,
        confidence=body.confidence,
        rationale=body.rationale,
        override_conditions=body.override_conditions,
    )
    return StrategicBeliefOut.from_row(belief)


@router.patch("/{belief_id}")
async def patch_belief(belief_id: str, body: BeliefPatch, db: DbSession):
    svc = BeliefService(db)
    belief = await svc.update(
        belief_id,
        content=body.content,
        sort_order=body.sort_order,
        status=body.status,
        confidence=body.confidence,
        rationale=body.rationale,
        override_conditions=body.override_conditions,
    )
    if not belief:
        raise HTTPException(404, "Belief not found")
    return StrategicBeliefOut.from_row(belief)


@router.delete("/{belief_id}")
async def delete_belief(belief_id: str, db: DbSession):
    svc = BeliefService(db)
    ok = await svc.delete(belief_id)
    if not ok:
        raise HTTPException(404, "Belief not found")
    return {"status": "archived"}
