#!/usr/bin/env python3
"""
Initialize database - create all tables.
For development only. Use Alembic migrations in production.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import get_logger
from app.db.session import init_db

logger = get_logger(__name__)


async def main():
    """Initialize database"""
    logger.info("initializing_database")

    try:
        await init_db()
        logger.info("database_initialized_successfully")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
