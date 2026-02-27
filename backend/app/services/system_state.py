"""
Service helpers for global system state.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.system_state import SystemState


async def get_system_paused(db: AsyncSession) -> bool:
    """Return the global paused flag (DB first, env fallback)."""
    result = await db.execute(
        select(SystemState.system_paused).order_by(SystemState.id.asc()).limit(1)
    )
    paused = result.scalar_one_or_none()
    if paused is None:
        return settings.system_paused
    return paused


async def set_system_paused(db: AsyncSession, paused: bool) -> SystemState:
    """Set the global paused flag, creating the row if missing."""
    result = await db.execute(
        select(SystemState).order_by(SystemState.id.asc()).limit(1)
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = SystemState(system_paused=paused)
        db.add(state)
    else:
        state.system_paused = paused

    await db.flush()
    return state
