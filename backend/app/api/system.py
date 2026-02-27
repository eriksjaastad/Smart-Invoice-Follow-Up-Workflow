"""
System control API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.system import SystemStatus, SystemUpdateRequest
from app.services.system_state import get_system_paused, set_system_paused

router = APIRouter(prefix="/api/system", tags=["system"])
logger = logging.getLogger(__name__)


def _require_system_secret(secret: str) -> None:
    if not settings.system_control_secret:
        raise HTTPException(status_code=503, detail="System control secret not configured")
    if secret != settings.system_control_secret:
        logger.warning("Invalid system control secret provided")
        raise HTTPException(status_code=401, detail="Invalid system control secret")


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: AsyncSession = Depends(get_db)) -> SystemStatus:
    """Return current global system paused status."""
    paused = await get_system_paused(db)
    return SystemStatus(paused=paused)


@router.post("/pause", response_model=SystemStatus)
async def set_system_status(
    request: SystemUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> SystemStatus:
    """Set global paused status (one-click control)."""
    _require_system_secret(request.secret)
    state = await set_system_paused(db, request.paused)
    return SystemStatus(paused=state.system_paused)
