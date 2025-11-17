"""
Authentication API endpoints.
Handles user login, token refresh, and API key management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_current_superuser
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    APIKeyCreate,
    APIKeyInfo,
    APIKeyResponse,
    Login,
    RefreshToken,
    Token,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/login", response_model=Token, summary="Login with username and password")
async def login(
    login_data: Login,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.

    - **username**: Username
    - **password**: Password

    Returns access token and refresh token.
    """
    user = await AuthService.authenticate_user(
        db, login_data.username, login_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = await AuthService.create_tokens(user)

    logger.info("user_logged_in", user_id=user.id, username=user.username)

    return tokens


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(refresh_data: RefreshToken):
    """
    Get new access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token.
    """
    access_token = await AuthService.refresh_access_token(refresh_data.refresh_token)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse, summary="Register new user")
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),  # Only admins can create users
):
    """
    Register a new user (admin only).

    - **username**: Unique username (min 3 characters)
    - **email**: Valid email address
    - **password**: Password (min 8 characters)
    - **is_superuser**: Whether user is a superuser

    Returns created user.
    """
    try:
        user = await AuthService.create_user(db, user_create)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current authenticated user information.

    Returns user details.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    summary="Create API key",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new API key for the current user.

    - **name**: Optional name for the API key
    - **expires_in_days**: Optional expiration in days (1-365)

    Returns the API key. **This is the only time the key is visible!**
    Save it securely.
    """
    try:
        api_key = await AuthService.create_api_key(
            db,
            current_user,
            name=api_key_data.name,
            expires_in_days=api_key_data.expires_in_days,
        )
        return api_key
    except Exception as e:
        logger.error("api_key_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get("/api-keys", response_model=List[APIKeyInfo], summary="List API keys")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all API keys for the current user.

    Returns list of API keys (without the actual key values).
    """
    api_keys = await AuthService.get_user_api_keys(db, current_user)
    return [APIKeyInfo.model_validate(key) for key in api_keys]


@router.delete(
    "/api-keys/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key",
)
async def revoke_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke (deactivate) an API key.

    - **api_key_id**: ID of the API key to revoke

    The API key will be deactivated and can no longer be used.
    """
    try:
        revoked = await AuthService.revoke_api_key(db, current_user, api_key_id)

        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("api_key_revocation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )
