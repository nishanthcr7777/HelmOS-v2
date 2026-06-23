from fastapi import APIRouter
from sqlalchemy import select

from api.deps import DbSession
from db.models import Entity
from schemas.types import EntityCardOut

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("")
async def list_entities(workspace_id: str, db: DbSession):
    result = await db.execute(
        select(Entity).where(Entity.workspace_id == workspace_id).order_by(Entity.name)
    )
    return [EntityCardOut.from_row(e) for e in result.scalars().all()]
