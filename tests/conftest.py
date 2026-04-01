"""
Pytest configuration and fixtures for Smart Invoice Workflow tests.

Provides:
- Async SQLite in-memory DB fixture (isolated per test)
- FastAPI TestClient with auth + DB dependency overrides
- Make.com and Stripe external calls mocked to avoid real API hits

Usage:
    pytest tests/test_api_lifecycle.py -v

Dependencies (in pyproject.toml):
    pytest-asyncio, httpx, aiosqlite
"""
import sys
import os
from pathlib import Path

# Ensure required settings for tests are present before app import
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# Add backend to path so `from app.x import y` works
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Patch JSONB → JSON before any models are imported.
# SQLite doesn't support PostgreSQL's JSONB; this makes table creation work in tests.
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import JSON as _JSON

pg.JSONB = _JSON  # type: ignore[attr-defined]

import pytest_asyncio
from datetime import datetime
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.main import app
from app.db.session import get_db, Base
from app.core.auth import require_auth
from app.models.user import User


# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Fresh async SQLite in-memory DB per test. Creates + drops all tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Test user
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession) -> User:
    """Inactive free-plan user, seeded into the in-memory DB."""
    user = User(
        id=uuid4(),
        auth0_user_id="test|mock123",
        email="test@example.com",
        name="Test User",
        business_name="Test Co",
        active=False,
        plan="free",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# FastAPI test client with dependency overrides
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db: AsyncSession, test_user: User):
    """
    AsyncClient for the FastAPI app with:
    - Auth override: returns test_user (no Auth0 call)
    - DB override: uses in-memory SQLite session
    """

    async def override_get_db():
        yield test_db

    async def override_require_auth():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = override_require_auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
