"""
Reset Database Script

This script drops and recreates the public schema to clean the database
before running fresh Alembic migrations.

Usage:
    python scripts/reset_database.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from database import engine


async def reset_database():
    """Drop and recreate the public schema"""

    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("Database:", engine.url)

    confirmation = input("\nType 'yes' to continue: ")

    if confirmation.lower() != 'yes':
        print("❌ Operation cancelled.")
        return

    print("\n🔄 Resetting database...")

    async with engine.begin() as conn:
        # Drop all enum types first (they're not automatically dropped with CASCADE)
        print("  - Dropping enum types...")
        await conn.execute(text("""
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public'))
                LOOP
                    EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
            END $$;
        """))

        # Drop all tables
        print("  - Dropping all tables...")
        await conn.execute(text("DROP SCHEMA public CASCADE"))

        # Recreate schema
        print("  - Recreating public schema...")
        await conn.execute(text("CREATE SCHEMA public"))

        # Grant permissions
        print("  - Granting permissions...")
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))

    print("✅ Database reset successfully!")
    print("\nNext step: Run migrations with:")
    print("  alembic upgrade head")


if __name__ == "__main__":
    asyncio.run(reset_database())
