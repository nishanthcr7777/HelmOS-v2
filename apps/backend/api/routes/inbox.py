from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DbSession
from db.models import InboxItem
from schemas.types import InboxItemOut

router = APIRouter(prefix="/inbox", tags=["inbox"])

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class InboxPatch(BaseModel):
    status: str


@router.get("")
async def list_inbox(workspace_id: str, db: DbSession):
    result = await db.execute(
        select(InboxItem).where(
            InboxItem.workspace_id == workspace_id,
            InboxItem.status == "open",
        )
    )
    items = list(result.scalars().all())
    items.sort(key=lambda i: PRIORITY_ORDER.get(i.priority, 9))
    return [InboxItemOut.from_row(i) for i in items]


@router.patch("/{item_id}")
async def patch_inbox(item_id: str, body: InboxPatch, db: DbSession):
    result = await db.execute(select(InboxItem).where(InboxItem.id == UUID(item_id)))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Inbox item not found")
    row.status = body.status
    await db.flush()
    return InboxItemOut.from_row(row)
