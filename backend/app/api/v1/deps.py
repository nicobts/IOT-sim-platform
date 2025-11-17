"""
API dependencies for authentication and database access.
Provides dependency injection for FastAPI endpoints.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.once_client import OnceClient, get_once_client
from app.core.logging import get_logger
from app.core.security import verify_api_key, verify_token
from app.db.session import get_db
from app.models.user import APIKey, User
from app.schemas.user import UserResponse

logger = get_logger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from JWT token.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    logger.debug("user_authenticated", user_id=user.id, username=user.username)
    return user


async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from API key.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If API key is invalid or user not found
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get all active API keys and check against provided key
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True)  # noqa: E712
    )
    api_keys = result.scalars().all()

    matched_api_key = None
    for db_key in api_keys:
        if verify_api_key(api_key, db_key.key_hash):
            matched_api_key = db_key
            break

    if not matched_api_key:
        logger.warning("invalid_api_key_attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Check if API key is expired
    if not matched_api_key.is_valid:
        logger.warning("expired_api_key_used", api_key_id=matched_api_key.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
        )

    # Get user
    result = await db.execute(
        select(User).where(User.id == matched_api_key.user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive",
        )

    logger.debug(
        "user_authenticated_via_api_key",
        user_id=user.id,
        api_key_id=matched_api_key.id,
    )
    return user


async def get_current_user(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """
    Get current user from either JWT token or API key.
    Tries token first, then API key.

    Args:
        token_user: User from JWT token
        api_key_user: User from API key

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If no valid authentication provided
    """
    # Try token first
    if token_user:
        return token_user

    # Fall back to API key
    if api_key_user:
        return api_key_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from authentication

    Returns:
        Active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current superuser.

    Args:
        current_user: Current active user

    Returns:
        Superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges",
        )
    return current_user


async def get_once_client_dep() -> OnceClient:
    """
    Get 1NCE API client as dependency.

    Returns:
        Configured OnceClient instance
    """
    return await get_once_client()
