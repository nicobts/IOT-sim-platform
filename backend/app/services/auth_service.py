"""
Authentication service for user management and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    get_password_hash,
    hash_api_key,
    verify_password,
    verify_token,
)
from app.models.user import APIKey, User
from app.schemas.auth import APIKeyResponse, Token
from app.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            db: Database session
            username: Username
            password: Password

        Returns:
            User if authenticated, None otherwise
        """
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("login_attempt_user_not_found", username=username)
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning("login_attempt_invalid_password", username=username)
            return None

        if not user.is_active:
            logger.warning("login_attempt_inactive_user", username=username)
            return None

        logger.info("user_authenticated", user_id=user.id, username=username)
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            user_create: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        result = await db.execute(
            select(User).where(User.username == user_create.username)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"Username {user_create.username} already exists")

        # Check if email exists
        result = await db.execute(select(User).where(User.email == user_create.email))
        if result.scalar_one_or_none():
            raise ValueError(f"Email {user_create.email} already exists")

        # Create user
        user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=get_password_hash(user_create.password),
            is_active=True,
            is_superuser=user_create.is_superuser,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info("user_created", user_id=user.id, username=user.username)
        return user

    @staticmethod
    async def create_tokens(user: User) -> Token:
        """
        Create access and refresh tokens for user.

        Args:
            user: User to create tokens for

        Returns:
            Token with access and refresh tokens
        """
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New access token if valid, None otherwise
        """
        user_id = verify_token(refresh_token, token_type="refresh")

        if not user_id:
            logger.warning("invalid_refresh_token_attempt")
            return None

        access_token = create_access_token(subject=user_id)
        logger.info("access_token_refreshed", user_id=user_id)

        return access_token

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user: User,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> APIKeyResponse:
        """
        Create API key for user.

        Args:
            db: Database session
            user: User to create API key for
            name: Optional name for the API key
            expires_in_days: Optional expiration in days

        Returns:
            API key response with the actual key (only returned once)
        """
        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create API key record
        db_api_key = APIKey(
            user_id=user.id,
            key_hash=key_hash,
            name=name,
            is_active=True,
            expires_at=expires_at,
        )

        db.add(db_api_key)
        await db.commit()
        await db.refresh(db_api_key)

        logger.info(
            "api_key_created",
            user_id=user.id,
            api_key_id=db_api_key.id,
            name=name,
        )

        # Return response with actual key (only time it's visible)
        return APIKeyResponse(
            api_key=api_key,
            id=db_api_key.id,
            name=db_api_key.name,
            expires_at=db_api_key.expires_at,
            created_at=db_api_key.created_at,
        )

    @staticmethod
    async def get_user_api_keys(db: AsyncSession, user: User) -> list[APIKey]:
        """
        Get all API keys for user.

        Args:
            db: Database session
            user: User to get API keys for

        Returns:
            List of API keys (without the actual key values)
        """
        result = await db.execute(
            select(APIKey).where(APIKey.user_id == user.id).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke_api_key(
        db: AsyncSession, user: User, api_key_id: int
    ) -> bool:
        """
        Revoke (deactivate) an API key.

        Args:
            db: Database session
            user: User who owns the API key
            api_key_id: ID of API key to revoke

        Returns:
            True if revoked, False if not found

        Raises:
            ValueError: If API key doesn't belong to user
        """
        result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        if api_key.user_id != user.id:
            raise ValueError("API key does not belong to user")

        api_key.is_active = False
        await db.commit()

        logger.info(
            "api_key_revoked",
            user_id=user.id,
            api_key_id=api_key_id,
        )

        return True

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession, username: str
    ) -> Optional[User]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: Email

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
