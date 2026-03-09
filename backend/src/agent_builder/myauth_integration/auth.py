# -*- coding: utf-8 -*-
"""Custom authentication dependencies for the application."""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> str:
    """Get current user ID from JWT token.

    This dependency expects the auth framework to be registered
    in request.app.state.auth_framework.

    Returns:
        The user ID string from the token.

    Raises:
        HTTPException: If not authenticated or token is invalid.
    """
    from fastapi import HTTPException, status
    from myauth import User

    logger.debug(f"Auth request: {request.url.path}")

    # Get auth framework from app state
    auth_framework = getattr(request.app.state, 'auth_framework', None)
    if not auth_framework:
        logger.error("Auth framework not initialized")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth framework not initialized",
        )

    # Get credentials
    creds = await security(request)
    if not creds:
        logger.warning(f"No credentials provided for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    user = await auth_framework.identity.verify_token(creds.credentials)
    if not user:
        logger.warning(f"Invalid token for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    logger.info(f"User authenticated: {user.id}")
    return user.id


async def get_current_user_obj(request: Request) -> Optional[dict]:
    """Get current user object from JWT token.
    
    Returns the full user object instead of just the ID.
    
    Returns:
        The user object or None if not authenticated.
    """
    from fastapi import HTTPException, status
    
    auth_framework = getattr(request.app.state, 'auth_framework', None)
    if not auth_framework:
        return None
    
    creds = await security(request)
    if not creds:
        return None
    
    try:
        user = await auth_framework.identity.verify_token(creds.credentials)
        return user if user else None
    except Exception:
        return None


async def get_optional_user(request: Request) -> Optional[str]:
    """Get current user ID if authenticated, None otherwise.
    
    Unlike get_current_user, this doesn't raise an exception
    when the user is not authenticated.
    """
    try:
        return await get_current_user(request)
    except Exception:
        return None
