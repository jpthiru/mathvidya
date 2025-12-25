import asyncio
from sqlalchemy import select, func, text
from database import AsyncSessionLocal
from models import (
    User, ParentStudentMapping, SubscriptionPlan, Subscription,
    Question, ExamTemplate, ExamInstance, StudentMCQAnswer,
    AnswerSheetUpload, UnansweredQuestion, Evaluation, QuestionMark,
    AuditLog, Holiday, SystemConfig
)

async def verify_database():
    async with AsyncSessionLocal() as session:
        # Count tables
        result = await session.execute(
            text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
        )
        table_count = result.scalar()
        print(f"OK Total tables created: {table_count}")
        
        # Check seed data
        plans_count = await session.scalar(select(func.count()).select_from(SubscriptionPlan))
        holidays_count = await session.scalar(select(func.count()).select_from(Holiday))
        configs_count = await session.scalar(select(func.count()).select_from(SystemConfig))
        
        print(f"OK Subscription plans seeded: {plans_count}")
        print(f"OK Holidays seeded: {holidays_count}")
        print(f"OK System configs seeded: {configs_count}")
        
        # List subscription plans
        result = await session.execute(select(SubscriptionPlan))
        plans = result.scalars().all()
        
        print("\nSubscription Plans:")
        for plan in plans:
            print(f"  - {plan.display_name}: {plan.exams_per_month} exams/month, SLA: {plan.sla_hours}hrs")

if __name__ == "__main__":
    asyncio.run(verify_database())