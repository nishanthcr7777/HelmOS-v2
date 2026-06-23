from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.models import SpendLedger


async def check_spend_cap(session: AsyncSession, category: str, estimated_usd: float = 0.0) -> bool:
    """Return True if spend is within daily cap."""
    settings = get_settings()
    today = date.today()
    result = await session.execute(
        select(func.coalesce(func.sum(SpendLedger.amount_usd), 0.0)).where(SpendLedger.day == today)
    )
    total = float(result.scalar_one())
    return (total + estimated_usd) <= settings.daily_spend_cap_usd


async def record_spend(session: AsyncSession, category: str, amount_usd: float) -> None:
    today = date.today()
    existing = await session.execute(
        select(SpendLedger).where(SpendLedger.day == today, SpendLedger.category == category)
    )
    row = existing.scalar_one_or_none()
    if row:
        row.amount_usd += amount_usd
    else:
        session.add(SpendLedger(day=today, category=category, amount_usd=amount_usd))
