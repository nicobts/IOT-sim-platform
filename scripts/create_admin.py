#!/usr/bin/env python3
"""
Create admin user.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User

logger = get_logger(__name__)


async def create_admin_user(
    username: str = "admin",
    email: str = "admin@example.com",
    password: str = "admin123",
):
    """
    Create admin user if it doesn't exist.

    Args:
        username: Admin username
        email: Admin email
        password: Admin password (will be hashed)
    """
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin user already exists
            result = await db.execute(select(User).where(User.username == username))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info("admin_user_already_exists", username=username)
                return

            # Create admin user
            admin = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
            )

            db.add(admin)
            await db.commit()
            await db.refresh(admin)

            logger.info(
                "admin_user_created",
                user_id=admin.id,
                username=admin.username,
                email=admin.email,
            )

            print(f"\n✅ Admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"\n⚠️  Please change the password after first login!\n")

        except Exception as e:
            logger.error("admin_user_creation_failed", error=str(e))
            raise


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@example.com", help="Admin email")
    parser.add_argument("--password", default="admin123", help="Admin password")

    args = parser.parse_args()

    await create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password,
    )


if __name__ == "__main__":
    asyncio.run(main())
