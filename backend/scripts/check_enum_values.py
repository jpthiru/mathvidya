"""
Check actual enum values in PostgreSQL
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from database import engine


async def check_enums():
    """Check enum values in database"""

    print("🔍 Checking PostgreSQL enum values...\n")

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT t.typname AS enum_name,
                   e.enumlabel AS enum_value
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            AND t.typname LIKE 'mv_%'
            ORDER BY t.typname, e.enumsortorder
        """))

        enums = result.fetchall()

        current_enum = None
        for enum_name, enum_value in enums:
            if enum_name != current_enum:
                if current_enum is not None:
                    print()
                print(f"{enum_name}:")
                current_enum = enum_name
            print(f"  - {repr(enum_value)}")


if __name__ == "__main__":
    asyncio.run(check_enums())
