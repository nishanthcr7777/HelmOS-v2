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

    async def create(
        self,
        workspace_id: str,
        content: str,
        *,
        confidence: float = 0.8,
        rationale: str | None = None,
        override_conditions: list[str] | None = None,
    ) -> StrategicBelief:
        beliefs = await self.list_active(workspace_id)
        belief = StrategicBelief(
            workspace_id=workspace_id,
            content=content,
            sort_order=len(beliefs) + 1,
            confidence=confidence,
            rationale=rationale,
            override_conditions=list(override_conditions or []),
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
        confidence: float | None = None,
        rationale: str | None = None,
        override_conditions: list[str] | None = None,
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
        if confidence is not None:
            belief.confidence = confidence
        if rationale is not None:
            belief.rationale = rationale
        if override_conditions is not None:
            belief.override_conditions = list(override_conditions)
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
        lines = [
            "Beliefs are heuristics — not immutable laws.",
            "Evaluate whether override conditions justify an exception before applying a belief.",
            "",
        ]
        for b in beliefs:
            conf = getattr(b, "confidence", 0.8) or 0.8
            block = [f"- Belief: {b.content}", f"  Confidence: {conf:.2f}"]
            rationale = getattr(b, "rationale", None)
            if rationale:
                block.append(f"  Rationale: {rationale}")
            overrides = getattr(b, "override_conditions", None) or []
            if overrides:
                block.append("  Override when:")
                for cond in overrides:
                    block.append(f"    · {cond}")
            lines.extend(block)
        return "## Strategic beliefs (founding heuristics)\n" + "\n".join(lines)
