from fastapi import APIRouter
from sqlalchemy import func, select

from api.deps import DbSession
from db.models import Decision, InboxItem, Workspace
from schemas.types import DashboardPayloadOut, DecisionOut, FounderStateOut

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(db: DbSession):
    founder = await _founder_state(db, None)
    workspaces = (await db.execute(select(Workspace))).scalars().all()
    focus = []
    for ws in workspaces:
        open_dec = await db.execute(
            select(func.count())
            .select_from(Decision)
            .where(Decision.workspace_id == ws.id, Decision.status.in_(("open", "pursuing")))
        )
        n = int(open_dec.scalar_one())
        if n:
            focus.append(
                {
                    "id": f"focus-{ws.id}",
                    "workspace_id": ws.id,
                    "workspace_name": ws.name,
                    "items": [f"Review {n} open decision(s) in {ws.name}"],
                }
            )

    decisions = (
        await db.execute(
            select(Decision)
            .where(Decision.status.in_(("open", "pursuing")))
            .order_by(Decision.updated_at.desc())
            .limit(10)
        )
    ).scalars().all()

    alerts = []
    for d in decisions[:5]:
        if len(d.agent_outputs or []) >= 3:
            verdicts = {o.get("verdict") for o in d.agent_outputs}
            if len(verdicts) > 2:
                alerts.append(
                    {
                        "id": f"alert-{d.id}",
                        "workspace_id": d.workspace_id,
                        "alert_type": "conflict",
                        "title": f"Conflicting opinions: {d.title or d.question[:60]}",
                        "detail": "Multiple agents disagree on this decision.",
                        "session_id": None,
                        "created_at": d.updated_at.isoformat().replace("+00:00", "Z"),
                    }
                )

    opportunities = [
        {
            "id": "opp-seed-1",
            "workspace_id": "clawback-labs",
            "workspace_name": "Clawback Labs",
            "title": "Review ICP-band targets from memory",
            "detail": "Run research on high-fit entities in your knowledge base.",
            "entity_name": None,
            "created_at": "2026-05-27T09:00:00Z",
        }
    ]

    return DashboardPayloadOut(
        founder_state=founder,
        todays_focus=focus,
        active_decisions=[DecisionOut.from_row(d) for d in decisions],
        board_alerts=alerts,
        opportunities=opportunities,
    )


@router.get("/founder-state")
async def get_founder_state(db: DbSession):
    return await _founder_state(db, None)


async def _founder_state(db: DbSession, workspace_id: str | None) -> FounderStateOut:
    dec_q = select(func.count()).select_from(Decision).where(Decision.status.in_(("open", "pursuing")))
    blocked_q = (
        select(func.count())
        .select_from(InboxItem)
        .where(InboxItem.item_type == "blocked_action", InboxItem.status == "open")
    )
    research_q = (
        select(func.count())
        .select_from(InboxItem)
        .where(InboxItem.item_type.in_(("risky_assumption", "unresolved_decision")), InboxItem.status == "open")
    )
    if workspace_id:
        dec_q = dec_q.where(Decision.workspace_id == workspace_id)
        blocked_q = blocked_q.where(InboxItem.workspace_id == workspace_id)
        research_q = research_q.where(InboxItem.workspace_id == workspace_id)

    open_dec = int((await db.execute(dec_q)).scalar_one())
    blocked = int((await db.execute(blocked_q)).scalar_one())
    research_needed = int((await db.execute(research_q)).scalar_one())

    if open_dec >= 5:
        load = "high"
    elif open_dec >= 2:
        load = "moderate"
    else:
        load = "low"

    return FounderStateOut(
        decision_load=load,
        blocked_items=blocked,
        open_decisions=open_dec,
        research_needed=research_needed,
    )
