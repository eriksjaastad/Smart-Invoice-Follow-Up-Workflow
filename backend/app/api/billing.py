"""
Billing API routes for Stripe integration.

Provides endpoints for:
- POST /api/billing/create-checkout - Create Stripe Checkout session
- POST /api/billing/webhook - Handle Stripe webhook events
- GET /api/billing/status - Get user's billing status
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
import stripe

from app.core.config import settings
from app.core.auth import require_auth
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter(prefix="/api/billing", tags=["billing"])

# Initialize Stripe with API key
stripe.api_key = settings.stripe_secret_key


# Request/Response models

class CreateCheckoutRequest(BaseModel):
    """Request to create Stripe Checkout session"""
    success_url: str = Field(..., description="URL to redirect to after successful payment")
    cancel_url: str = Field(..., description="URL to redirect to if user cancels")


class CreateCheckoutResponse(BaseModel):
    """Response with Stripe Checkout URL"""
    checkout_url: str = Field(..., description="URL to redirect user to for payment")
    session_id: str = Field(..., description="Stripe Checkout session ID")


class BillingStatusResponse(BaseModel):
    """User's billing status"""
    plan: str = Field(..., description="Current plan: 'free' or 'paid'")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID if exists")
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID if active")
    customer_portal_url: Optional[str] = Field(None, description="URL to Stripe customer portal")


class CheckoutSessionStatusResponse(BaseModel):
    """Verification payload for a Stripe Checkout return."""
    session_id: str
    verified: bool
    status: Optional[str] = None
    payment_status: Optional[str] = None
    amount_total: Optional[int] = None
    currency: Optional[str] = None


# Billing endpoints

@router.post("/create-checkout", response_model=CreateCheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Create a Stripe Checkout session for upgrading to paid plan.
    
    Creates a subscription checkout session for $15/month.
    User is redirected to Stripe Checkout page to complete payment.
    
    Args:
        request: Success and cancel URLs
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Checkout URL and session ID
        
    Raises:
        HTTPException 400: If user is already on paid plan
    """
    # Check if user is already on paid plan
    if current_user.plan == "paid":
        raise HTTPException(status_code=400, detail="User is already on paid plan")
    
    try:
        # Create Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_price_id,  # $15/month price ID
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user.id),
            },
        )
        
        return CreateCheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/customer-portal")
async def create_customer_portal_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Create a Stripe Customer Portal session.
    
    Allows users to manage their subscription and payment methods.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Portal URL
        
    Raises:
        HTTPException 400: If user has no Stripe customer ID
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.frontend_url}/billing.html",
        )
        return {"portal_url": portal_session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.get("/checkout-session/{session_id}", response_model=CheckoutSessionStatusResponse)
async def get_checkout_session_status(
    session_id: str,
    current_user: User = Depends(require_auth)
):
    """
    Verify that a returned Stripe Checkout session belongs to the current user.

    This is used by the dashboard to fire purchase tracking only after a real,
    completed Stripe return instead of relying on a public success URL alone.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    metadata_user_id = session.get("metadata", {}).get("user_id")
    if metadata_user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Checkout session does not belong to current user")

    verified = (
        session.get("status") == "complete"
        and bool(session.get("subscription"))
        and current_user.plan == "paid"
    )

    return CheckoutSessionStatusResponse(
        session_id=session["id"],
        verified=verified,
        status=session.get("status"),
        payment_status=session.get("payment_status"),
        amount_total=session.get("amount_total"),
        currency=session.get("currency"),
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events.
    
    Processes events:
    - checkout.session.completed: User completed payment, upgrade to paid plan
    - customer.subscription.deleted: Subscription cancelled, downgrade to free plan
    - customer.subscription.updated: Subscription changed
    
    Args:
        request: Raw request body
        db: Database session
        stripe_signature: Stripe webhook signature header
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException 400: If signature verification fails
    """
    # Get raw request body
    payload = await request.body()
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(session, db)
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(subscription, db)
    
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await handle_subscription_updated(subscription, db)
    
    return {"status": "success"}


async def handle_checkout_completed(session: dict, db: AsyncSession):
    """
    Handle successful checkout - upgrade user to paid plan.

    Args:
        session: Stripe checkout session object
        db: Database session
    """
    user_id = session["metadata"]["user_id"]

    # Fetch user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return  # User not found, skip

    # Update user to paid plan
    user.plan = "paid"
    user.stripe_customer_id = session["customer"]
    user.stripe_subscription_id = session["subscription"]

    await db.commit()


async def handle_subscription_deleted(subscription: dict, db: AsyncSession):
    """
    Handle subscription cancellation - downgrade user to free plan.

    Args:
        subscription: Stripe subscription object
        db: Database session
    """
    # Find user by subscription ID
    result = await db.execute(
        select(User).where(User.stripe_subscription_id == subscription["id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        return  # User not found, skip

    # Downgrade to free plan
    user.plan = "free"
    user.stripe_subscription_id = None

    await db.commit()


async def handle_subscription_updated(subscription: dict, db: AsyncSession):
    """
    Handle subscription update.

    Args:
        subscription: Stripe subscription object
        db: Database session
    """
    # Find user by subscription ID
    result = await db.execute(
        select(User).where(User.stripe_subscription_id == subscription["id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        return  # User not found, skip

    # Update subscription status based on Stripe status
    if subscription["status"] == "active":
        user.plan = "paid"
    else:
        # Subscription is paused, cancelled, or past_due
        user.plan = "free"

    await db.commit()


@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Get user's current billing status.

    Returns:
    - Current plan (free or paid)
    - Stripe customer ID if exists
    - Stripe subscription ID if active
    - Customer portal URL if on paid plan

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Billing status information
    """
    # Generate customer portal URL if user has Stripe customer ID
    customer_portal_url = None
    if current_user.stripe_customer_id:
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=current_user.stripe_customer_id,
                return_url=settings.frontend_url,
            )
            customer_portal_url = portal_session.url
        except stripe.error.StripeError:
            # If portal creation fails, just don't include the URL
            pass

    return BillingStatusResponse(
        plan=current_user.plan,
        stripe_customer_id=current_user.stripe_customer_id,
        stripe_subscription_id=current_user.stripe_subscription_id,
        customer_portal_url=customer_portal_url
    )
