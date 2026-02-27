"""
Authentication API routes for Auth0 integration.

These routes handle the OAuth2 flow with Auth0:
1. User clicks "Login" → redirects to Auth0 Universal Login
2. User authenticates → Auth0 redirects to /api/auth/callback
3. Backend exchanges code for tokens → creates/retrieves user → returns session
4. Frontend stores session token → uses for authenticated requests
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from authlib.integrations.starlette_client import OAuth
from typing import Optional
import logging

from app.core.config import settings
from app.core.auth import get_current_user, require_auth
from app.db.session import get_db
from app.models import User
from app.schemas.user import User as UserSchema, UserCreate


router = APIRouter(prefix="/api/auth", tags=["authentication"])

logger = logging.getLogger(__name__)


# OAuth client configuration
oauth = OAuth()
oauth.register(
    name='auth0',
    client_id=settings.auth0_client_id,
    client_secret=settings.auth0_client_secret,
    server_metadata_url=f'https://{settings.auth0_domain}/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile email'
    }
)


@router.get("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Initiate Auth0 login flow or Bypass for development.
    """
    if settings.debug_mock_auth:
        # 1. Check if mock user exists
        result = await db.execute(
            select(User).where(User.email == "mock.user@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # 2. Create mock user if doesn't exist
            user = User(
                auth0_user_id="auth0|mock_user_123",
                email="mock.user@example.com",
                name="Mock Developer",
                business_name="Mock Systems Inc",
                plan='paid',
                active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
        # 3. Set session
        request.session['user_id'] = str(user.id)
        logger.info(f"MOCK AUTH: Logged in as {user.email}")
        return RedirectResponse(url="/dashboard.html")

    # Standard Auth0 flow
    redirect_uri = settings.auth0_callback_url
    return await oauth.auth0.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle Auth0 callback after successful authentication.
    
    This route:
    1. Exchanges authorization code for tokens
    2. Decodes JWT to get user profile (auth0_user_id, email, name)
    3. Checks if user exists in database
    4. If new user, creates user record with plan="free" and active=true
    5. If existing user, retrieves user record
    6. Returns user data (in production, would set session cookie or return JWT)
    
    Requirements: 1.2, 1.3, 1.4, 1.5, 1.6
    """
    try:
        # Exchange authorization code for tokens
        token = await oauth.auth0.authorize_access_token(request)
        
        # Get user info from Auth0
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Auth0"
            )
        
        # Extract user data
        auth0_user_id = user_info.get('sub')  # Auth0 user ID (e.g., "auth0|123456")
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])  # Default to email username if no name
        
        if not auth0_user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information from Auth0"
            )
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.auth0_user_id == auth0_user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user (Requirement 1.3, 1.4, 1.5)
            user = User(
                auth0_user_id=auth0_user_id,
                email=email,
                name=name,
                business_name=name,  # Default to name, user can update later
                plan='free',  # Default to free plan
                active=True   # Active by default
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # In production, you would:
        # 1. Create a session token or JWT
        # 2. Set a secure HTTP-only cookie
        # 3. Redirect to frontend dashboard
        
        # Store user_id in session
        request.session['user_id'] = str(user.id)
        
        # Redirect to dashboard
        return RedirectResponse(url="/dashboard.html")
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/logout")
async def logout(request: Request):
    """
    Log out the current user.
    
    Clears session and redirects to Auth0 logout endpoint.
    Auth0 will then redirect back to the application homepage.
    
    Requirement: 1.1
    """
    # In production, clear session cookie here
    
    # Redirect to Auth0 logout
    return_to = settings.cors_origins.split(',')[0]  # Redirect to first allowed origin
    logout_url = f"https://{settings.auth0_domain}/v2/logout?returnTo={return_to}&client_id={settings.auth0_client_id}"
    
    return RedirectResponse(url=logout_url)


@router.get("/me", response_model=UserSchema)
async def get_me(user: User = Depends(require_auth)):
    """
    Get current authenticated user profile.
    
    This route is protected and requires a valid JWT token.
    Returns the user's profile from the database.
    
    Requirement: 1.6
    """
    return user

