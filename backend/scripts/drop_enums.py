"""
Drop all mv_* enum types

Quick script to drop all Mathvidya enum types before running migrations.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from database import engine


async def drop_enums():
    """Drop all mv_* enum types"""

    print("🔄 Dropping all mv_* enum types...")

    async with engine.begin() as conn:
        # Get all mv_* enum types
        result = await conn.execute(text("""
            SELECT typname
            FROM pg_type
            WHERE typtype = 'e'
            AND typname LIKE 'mv_%'
            AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        """))

        enums = result.fetchall()

        if not enums:
            print("✅ No mv_* enum types found.")
            return

        print(f"Found {len(enums)} enum types to drop:")
        for (enum_name,) in enums:
            print(f"  - {enum_name}")

        # Drop each enum
        for (enum_name,) in enums:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
            print(f"  ✓ Dropped {enum_name}")

    print("✅ All mv_* enum types dropped successfully!")
    print("\nNext step: Run migrations with:")
    print("  alembic upgrade head")


if __name__ == "__main__":
    asyncio.run(drop_enums())
