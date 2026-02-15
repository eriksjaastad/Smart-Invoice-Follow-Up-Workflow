"""FastAPI application entry point"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Smart Invoice SaaS Backend...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔗 Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'configured'}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Smart Invoice SaaS Backend...")


# Create FastAPI application
app = FastAPI(
    title="Smart Invoice SaaS API",
    description="Automated invoice follow-up system with Make.com integration",
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

# Mount static files (path relative to project root)
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - will serve landing page in production"""
    return {
        "message": "Smart Invoice SaaS API",
        "version": "2.0.0",
        "docs": "/api/docs" if settings.debug else None
    }


# Include API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.webhooks import router as webhooks_router
from app.api.onboarding import router as onboarding_router
from app.api.billing import router as billing_router
from app.api.digest import router as digest_router
from app.api.notifications import router as notifications_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(webhooks_router)
app.include_router(onboarding_router)
app.include_router(billing_router)
app.include_router(digest_router)
app.include_router(notifications_router)

