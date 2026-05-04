"""
Auth0 authentication utilities.

This module provides JWT validation and user authentication via Auth0.
Auth0 is non-negotiable for security - do NOT replace with custom JWT or homebrew auth.
"""
import time
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from sqlalchemy import select


# HTTP Bearer token security scheme - auto_error=False to allow session-based auth
security = HTTPBearer(auto_error=False)

JWKS_CACHE_TTL_SECONDS = 60 * 60
_JWKS_CACHE: dict[str, object] = {
    "expires_at": 0.0,
    "keys_by_kid": {},
}


class AuthError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, error: str, status_code: int):
        self.error = error
        self.status_code = status_code


def _auth0_domain() -> str:
    return settings.auth0_domain.removeprefix("https://").removeprefix("http://").rstrip("/")


def _auth0_issuer() -> str:
    return f"https://{_auth0_domain()}/"


def _jwks_url() -> str:
    return f"https://{_auth0_domain()}/.well-known/jwks.json"


def clear_jwks_cache() -> None:
    """Clear cached Auth0 JWKS keys. Intended for tests and emergency refreshes."""
    _JWKS_CACHE["expires_at"] = 0.0
    _JWKS_CACHE["keys_by_kid"] = {}


async def _fetch_jwks_keys() -> dict[str, dict]:
    if not settings.auth0_domain:
        raise AuthError("Auth0 domain is not configured", status.HTTP_401_UNAUTHORIZED)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(_jwks_url())
            response.raise_for_status()
            jwks = response.json()
    except Exception:
        raise AuthError("Unable to fetch Auth0 signing keys", status.HTTP_401_UNAUTHORIZED)

    keys_by_kid = {
        key["kid"]: key
        for key in jwks.get("keys", [])
        if isinstance(key, dict) and key.get("kid")
    }
    if not keys_by_kid:
        raise AuthError("Auth0 signing keys are unavailable", status.HTTP_401_UNAUTHORIZED)

    _JWKS_CACHE["keys_by_kid"] = keys_by_kid
    _JWKS_CACHE["expires_at"] = time.monotonic() + JWKS_CACHE_TTL_SECONDS
    return keys_by_kid


async def _get_jwks_keys(force_refresh: bool = False) -> dict[str, dict]:
    cached_keys = _JWKS_CACHE.get("keys_by_kid", {})
    expires_at = float(_JWKS_CACHE.get("expires_at", 0.0))

    if (
        not force_refresh
        and isinstance(cached_keys, dict)
        and cached_keys
        and time.monotonic() < expires_at
    ):
        return cached_keys

    return await _fetch_jwks_keys()


async def _get_signing_key(kid: str) -> dict:
    keys_by_kid = await _get_jwks_keys()
    key = keys_by_kid.get(kid)
    if key:
        return key

    # Auth0 may rotate keys while the local cache is still valid.
    keys_by_kid = await _get_jwks_keys(force_refresh=True)
    key = keys_by_kid.get(kid)
    if not key:
        raise AuthError("Token signing key is not recognized", status.HTTP_401_UNAUTHORIZED)
    return key


async def verify_jwt(token: str) -> dict:
    """
    Verify and decode an Auth0 RS256 JWT using the tenant JWKS.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    if not settings.auth0_audience:
        raise AuthError("Auth0 audience is not configured", status.HTTP_401_UNAUTHORIZED)

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise AuthError("Invalid token signing algorithm", status.HTTP_401_UNAUTHORIZED)

        kid = header.get("kid")
        if not kid:
            raise AuthError("Token is missing key id", status.HTTP_401_UNAUTHORIZED)

        signing_key = await _get_signing_key(kid)
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=_auth0_issuer(),
        )
        return payload
    except AuthError:
        raise
    except ExpiredSignatureError:
        raise AuthError("Token has expired", status.HTTP_401_UNAUTHORIZED)
    except JWTClaimsError:
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
            payload = await verify_jwt(credentials.credentials)
            
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

