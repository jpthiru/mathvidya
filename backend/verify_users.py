"""Verify test users were created successfully"""
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User

async def list_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        print(f"\nTotal users in database: {len(users)}\n")
        for user in users:
            print(f"  - {user.role.upper()}: {user.email} ({user.full_name})")
            if user.student_class:
                print(f"    Class: {user.student_class}")

if __name__ == "__main__":
    asyncio.run(list_users())
