from uuid import UUID

import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from api.deps import DbSession
from db.models import ResearchJob
from research.pipeline import run_research_job
from schemas.types import ResearchJobOut

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRun(BaseModel):
    entity_name: str
    workspace_id: str


async def _run_job_after_commit(job_id: UUID) -> None:
    from db.session import get_session_factory

    await asyncio.sleep(0.1)
    factory = get_session_factory()
    async with factory() as session:
        await run_research_job(session, job_id)
        await session.commit()


@router.post("/run", status_code=201)
async def run_research(body: ResearchRun, db: DbSession, background_tasks: BackgroundTasks):
    job = ResearchJob(
        workspace_id=body.workspace_id,
        entity_name=body.entity_name,
        queries=[],
        step="querying",
        sources=[],
        status="pending",
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    background_tasks.add_task(_run_job_after_commit, job_id)
    return ResearchJobOut.from_row(job)


@router.get("/status/{job_id}")
async def research_status(job_id: str, db: DbSession):
    result = await db.execute(select(ResearchJob).where(ResearchJob.id == UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return ResearchJobOut.from_row(job)
