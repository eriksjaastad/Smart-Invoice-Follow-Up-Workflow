"""FastAPI application entry point"""
import logging
import sys
from pathlib import Path

# Ensure 'backend/' is on sys.path so 'from app.x import y' works on Vercel
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


def _logging_level() -> int:
    return getattr(logging, settings.log_level.upper(), logging.INFO)


def _configure_logging() -> None:
    level = _logging_level()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )


def _init_sentry() -> None:
    if not settings.sentry_dsn:
        logging.getLogger(__name__).info("Sentry disabled because SENTRY_DSN is unset")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            LoggingIntegration(
                sentry_logs_level=_logging_level(),
                level=logging.INFO,
                event_level=None,
            ),
        ],
        enable_logs=True,
    )
    logging.getLogger(__name__).info("Sentry initialized")


_configure_logging()
_init_sentry()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Smart Invoice SaaS Backend env=%s", settings.environment)
    yield
    logger.info("Shutting down Smart Invoice SaaS Backend")


# Create FastAPI application
app = FastAPI(
    title="Smart Invoice SaaS API",
    description="Automated invoice follow-up system with direct Google API integration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="siw_session",
    max_age=3600 * 24 * 7,  # 7 days
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }


# Include API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.webhooks import router as webhooks_router
from app.api.onboarding import router as onboarding_router
from app.api.billing import router as billing_router
from app.api.digest import router as digest_router
from app.api.notifications import router as notifications_router
from app.api.system import router as system_router
from app.api.cron import router as cron_router
from app.api.google_oauth import router as google_oauth_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(webhooks_router)
app.include_router(onboarding_router)
app.include_router(billing_router)
app.include_router(digest_router)
app.include_router(notifications_router)
app.include_router(system_router)
app.include_router(cron_router)
app.include_router(google_oauth_router)

# Mount static files (path relative to project root)
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
