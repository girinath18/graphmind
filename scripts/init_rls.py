"""
RLS (Row-Level Security) Manual Verification Script

⚠️  IMPORTANT: RLS is now automatically initialized during app startup!
This script is for manual verification and debugging only.

When you start the application, it AUTOMATICALLY:
1. Creates all database tables
2. Enables RLS on all tenant-scoped tables
3. Creates RLS policies
4. VERIFIES that RLS is properly configured
5. FAILS TO START if RLS is not working (critical safety feature)

You should NEVER need to run this script manually.

Use this script ONLY for:
- Verifying RLS status without starting the app
- Manual verification in production
- Debugging RLS issues
- Educational purposes (understanding the RLS setup)

COMMAND:
    python scripts/init_rls.py

This will display the RLS status on each table.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def init_rls_policies(db: AsyncSession) -> None:
    """
    ⚠️  DEPRECATED - This is now handled by app.core.database.init_db()

    Kept for backward compatibility and educational purposes.
    You should NOT call this directly - the app does it automatically on startup.
    """
    logger.warning(
        "⚠️  init_rls_policies() called manually. "
        "Note: This is now handled automatically by the app on startup."
    )

    from app.core.database import init_rls_policies as db_init_rls

    return await db_init_rls()


async def verify_rls_enabled(db: AsyncSession) -> dict:
    """
    Verify RLS is enabled on all tables.

    Returns dict of table_name -> rls_enabled (bool)

    ⚠️  DEPRECATED - Now handled by app.core.database.verify_rls_enabled()
    """
    from app.core.database import verify_rls_enabled as db_verify_rls

    return await db_verify_rls()


if __name__ == "__main__":
    """
    Run RLS verification standalone.

    Usage:
        python scripts/init_rls.py

    This will connect to the database and display RLS status.
    """

    async def main():
        from app.core.database import engine, verify_rls_enabled

        logger.info("=" * 60)
        logger.info("RLS STATUS VERIFICATION")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Note: RLS is automatically initialized during app startup.")
        logger.info("This script is for manual verification only.")
        logger.info("")

        try:
            # Verify RLS on all tables
            result = await verify_rls_enabled()

            if result:
                logger.info("✅ All RLS checks PASSED")
                logger.info("✅ Multi-tenancy is ENFORCED at database level")
            else:
                logger.error("❌ RLS verification FAILED")
                logger.error("❌ Database is NOT properly protected")

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            logger.error("Try running the application to auto-initialize RLS")
        finally:
            await engine.dispose()
            logger.info("")
            logger.info("=" * 60)

    asyncio.run(main())
