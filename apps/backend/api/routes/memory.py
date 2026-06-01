from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DbSession
from db.models import MemoryChunk
from memory.ingestion import create_note_chunk, ingest_pdf_bytes
from memory.retrieval import MemoryService
from schemas.types import MemoryChunkOut

router = APIRouter(prefix="/memory", tags=["memory"])


class ChunkCreate(BaseModel):
    workspace_id: str
    project_id: str | None = None
    chunk_type: str = "strategy_note"
    content: str
    entity_name: str | None = None


@router.get("/chunks")
async def list_chunks(
    db: DbSession,
    workspace_id: str,
    project_id: str | None = None,
    type: str | None = None,
    search: str | None = None,
):
    q = select(MemoryChunk).where(MemoryChunk.workspace_id == workspace_id)
    if project_id:
        q = q.where(MemoryChunk.project_id == project_id)
    if type:
        q = q.where(MemoryChunk.chunk_type == type)
    if search:
        q = q.where(MemoryChunk.content.ilike(f"%{search}%"))
    q = q.order_by(MemoryChunk.created_at.desc()).limit(200)
    result = await db.execute(q)
    return [MemoryChunkOut.from_row(c) for c in result.scalars().all()]


@router.post("/chunks", status_code=201)
async def create_chunk(body: ChunkCreate, db: DbSession):
    chunk = await create_note_chunk(
        db,
        body.workspace_id,
        body.content,
        chunk_type=body.chunk_type,
        project_id=body.project_id,
        entity_name=body.entity_name,
    )
    return MemoryChunkOut.from_row(chunk)


@router.post("/ingest")
async def ingest_file(
    db: DbSession,
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    project_id: str | None = Form(None),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    filename = file.filename or "upload.pdf"
    if filename.lower().endswith(".pdf"):
        count, _ = await ingest_pdf_bytes(db, workspace_id, filename, data, project_id)
    else:
        text = data.decode("utf-8", errors="replace")
        chunk = await create_note_chunk(
            db, workspace_id, text, chunk_type="document_chunk", project_id=project_id
        )
        count = 1
    return {"status": "indexed", "chunk_count": count}
