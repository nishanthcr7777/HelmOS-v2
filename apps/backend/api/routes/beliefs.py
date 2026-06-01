from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.deps import DbSession
from beliefs.service import BeliefService
from schemas.types import StrategicBeliefOut

router = APIRouter(prefix="/beliefs", tags=["beliefs"])


class BeliefCreate(BaseModel):
    workspace_id: str
    content: str


class BeliefPatch(BaseModel):
    content: str | None = None
    sort_order: int | None = None
    status: str | None = None


@router.get("")
async def list_beliefs(workspace_id: str, db: DbSession):
    svc = BeliefService(db)
    beliefs = await svc.list_active(workspace_id)
    return [StrategicBeliefOut.from_row(b) for b in beliefs]


@router.post("", status_code=201)
async def create_belief(body: BeliefCreate, db: DbSession):
    svc = BeliefService(db)
    belief = await svc.create(body.workspace_id, body.content)
    return StrategicBeliefOut.from_row(belief)


@router.patch("/{belief_id}")
async def patch_belief(belief_id: str, body: BeliefPatch, db: DbSession):
    svc = BeliefService(db)
    belief = await svc.update(
        belief_id,
        content=body.content,
        sort_order=body.sort_order,
        status=body.status,
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
