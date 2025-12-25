"""
Check database state

Quick script to see what tables and enums exist.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from database import engine


async def check_db():
    """Check database state"""

    print("📊 Checking database state...\n")

    async with engine.connect() as conn:
        # Check tables
        result = await conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = result.fetchall()

        print(f"Tables ({len(tables)}):")
        if tables:
            for (table_name,) in tables:
                print(f"  - {table_name}")
        else:
            print("  (none)")

        # Check enum types
        result = await conn.execute(text("""
            SELECT typname
            FROM pg_type
            WHERE typtype = 'e'
            AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            ORDER BY typname
        """))
        enums = result.fetchall()

        print(f"\nEnum types ({len(enums)}):")
        if enums:
            for (enum_name,) in enums:
                print(f"  - {enum_name}")
        else:
            print("  (none)")

        # Check alembic version
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"\nAlembic version: {version}")
        except:
            print("\nAlembic version: (no alembic_version table)")


if __name__ == "__main__":
    asyncio.run(check_db())
