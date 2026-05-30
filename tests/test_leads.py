"""Lead capture API tests."""
import pytest
from sqlalchemy import select

from app.models.lead import Lead


@pytest.mark.asyncio
async def test_capture_lead_without_auth(test_client, test_db):
    response = await test_client.post(
        "/api/leads",
        json={
            "email": "Prospect@Example.com",
            "source": "landing_waitlist",
            "intent": "sample-reminder",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"

    lead = await test_db.scalar(select(Lead).where(Lead.email == "prospect@example.com"))
    assert lead is not None
    assert lead.source == "landing_waitlist"
    assert lead.intent == "sample-reminder"


@pytest.mark.asyncio
async def test_capture_lead_upserts_existing_source(test_client, test_db):
    payload = {"email": "prospect@example.com", "source": "enterprise_sales", "intent": "demo"}
    first = await test_client.post("/api/leads", json=payload)
    second = await test_client.post(
        "/api/leads",
        json={"email": "prospect@example.com", "source": "enterprise_sales", "intent": "pricing"},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    leads = (await test_db.scalars(select(Lead).where(Lead.email == "prospect@example.com"))).all()
    assert len(leads) == 1
    assert leads[0].intent == "pricing"
