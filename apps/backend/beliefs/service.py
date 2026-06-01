from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import StrategicBelief


class BeliefService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self, workspace_id: str) -> list[StrategicBelief]:
        result = await self.session.execute(
            select(StrategicBelief)
            .where(
                StrategicBelief.workspace_id == workspace_id,
                StrategicBelief.status == "active",
            )
            .order_by(StrategicBelief.sort_order, StrategicBelief.created_at)
        )
        return list(result.scalars().all())

    async def create(self, workspace_id: str, content: str) -> StrategicBelief:
        beliefs = await self.list_active(workspace_id)
        belief = StrategicBelief(
            workspace_id=workspace_id,
            content=content,
            sort_order=len(beliefs) + 1,
        )
        self.session.add(belief)
        await self.session.flush()
        return belief

    async def update(
        self,
        belief_id: str,
        *,
        content: str | None = None,
        sort_order: int | None = None,
        status: str | None = None,
    ) -> StrategicBelief | None:
        from uuid import UUID

        result = await self.session.execute(
            select(StrategicBelief).where(StrategicBelief.id == UUID(belief_id))
        )
        belief = result.scalar_one_or_none()
        if not belief:
            return None
        if content is not None:
            belief.content = content
        if sort_order is not None:
            belief.sort_order = sort_order
        if status is not None:
            belief.status = status
        await self.session.flush()
        return belief

    async def delete(self, belief_id: str) -> bool:
        from uuid import UUID

        result = await self.session.execute(
            select(StrategicBelief).where(StrategicBelief.id == UUID(belief_id))
        )
        belief = result.scalar_one_or_none()
        if not belief:
            return False
        belief.status = "archived"
        await self.session.flush()
        return True

    async def pack_for_prompt(self, workspace_id: str) -> str:
        beliefs = await self.list_active(workspace_id)
        if not beliefs:
            return ""
        lines = [f"- {b.content}" for b in beliefs]
        return "## Strategic beliefs (founding doctrine)\n" + "\n".join(lines)
