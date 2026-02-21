"""
Auth0 authentication utilities.

This module provides JWT validation and user authentication via Auth0.
Auth0 is non-negotiable for security - do NOT replace with custom JWT or homebrew auth.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from sqlalchemy import select


# HTTP Bearer token security scheme - auto_error=False to allow session-based auth
security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, error: str, status_code: int):
        self.error = error
        self.status_code = status_code


def verify_jwt(token: str) -> dict:
    """
    Verify and decode a JWT token from Auth0.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    try:
        # Decode JWT token
        # Note: In production, you should fetch and cache Auth0's public keys (JWKS)
        # and use them to verify the signature. For now, we're using the shared secret.
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.auth0_audience,
            issuer=f"https://{settings.auth0_domain}/"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", status.HTTP_401_UNAUTHORIZED)
    except jwt.JWTClaimsError:
        raise AuthError("Invalid token claims", status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise AuthError("Invalid token", status.HTTP_401_UNAUTHORIZED)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    
    This validates either the JWT token in the Authorization header 
    OR the session cookie set during Auth0 callback.
    
    Args:
        request: FastAPI request object (for session)
        credentials: HTTP Bearer credentials from request header
        db: Database session
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If authentication fails
    """
    # 1. Try JWT Bearer Token (API path)
    if credentials:
        try:
            # Verify JWT token
            payload = verify_jwt(credentials.credentials)
            
            # Extract auth0_user_id from token
            auth0_user_id: str = payload.get("sub")
            if auth0_user_id:
                # Fetch user from database
                result = await db.execute(
                    select(User).where(User.auth0_user_id == auth0_user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    if not user.active:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="User account is inactive",
                        )
                    return user
        except AuthError as e:
            # Only raise if Bearer was provided but invalid
            raise HTTPException(
                status_code=e.status_code,
                detail=e.error,
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Try Session Cookie (Frontend path)
    user_id = request.session.get("user_id")
    if user_id:
        try:
            # Fetch user from database using UUID
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            
            if user:
                if not user.active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User account is inactive",
                    )
                return user
        except (ValueError, TypeError):
            # Invalid UUID in session
            pass

    # No valid auth found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    
    This is a convenience wrapper around get_current_user that explicitly
    checks the active status (though get_current_user already does this).
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def require_auth(user: User = Depends(get_current_active_user)) -> User:
    """
    Decorator/dependency for protecting routes that require authentication.

    Usage:
        @app.get("/api/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"user_id": user.id}

    Args:
        user: User from get_current_active_user dependency

    Returns:
        Authenticated user object
    """
    return user


def verify_make_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    Verify Make.com API key for webhook/config endpoints.

    This dependency validates that requests from Make.com scenarios include
    the correct API key in the Authorization header.

    Args:
        authorization: Authorization header value (format: "Bearer <api_key>")

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Expected format: "Bearer <api_key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    api_key = parts[1]
    if api_key != settings.make_webhook_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

