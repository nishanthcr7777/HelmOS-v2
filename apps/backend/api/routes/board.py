from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DbSession
from db.models import BoardSession
from orchestrator.board import run_board_session
from schemas.types import BoardSessionOut

router = APIRouter(prefix="/board", tags=["board"])


class BoardCreate(BaseModel):
    question: str
    workspace_id: str
    project_id: str | None = None


@router.post("/sessions", status_code=201)
async def create_session(body: BoardCreate, db: DbSession):
    session = await run_board_session(db, body.workspace_id, body.question, body.project_id)
    return BoardSessionOut.from_row(session)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: DbSession):
    result = await db.execute(select(BoardSession).where(BoardSession.id == UUID(session_id)))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Session not found")
    return BoardSessionOut.from_row(row)
