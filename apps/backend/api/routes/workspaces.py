from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.deps import DbSession
from db.models import Project, Workspace, WorkspaceProfile
from schemas.types import ProjectOut, WorkspaceOut, WorkspaceProfileOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("")
async def list_workspaces(db: DbSession):
    result = await db.execute(select(Workspace).order_by(Workspace.name))
    return [WorkspaceOut.from_row(w) for w in result.scalars().all()]


@router.get("/{workspace_id}/projects")
async def list_projects(workspace_id: str, db: DbSession):
    result = await db.execute(select(Project).where(Project.workspace_id == workspace_id))
    return [ProjectOut.from_row(p) for p in result.scalars().all()]


@router.get("/{workspace_id}/profile")
async def get_profile(workspace_id: str, db: DbSession):
    result = await db.execute(
        select(WorkspaceProfile).where(WorkspaceProfile.workspace_id == workspace_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return WorkspaceProfileOut(
        workspace_id=profile.workspace_id,
        metrics=profile.metrics or [],
        context_lines=profile.context_lines or [],
    )
