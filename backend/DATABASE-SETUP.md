# Mathvidya Database Setup Guide

## Overview

The complete database schema for Mathvidya has been created with **15 tables**, comprehensive relationships, constraints, and indexes. This guide will help you set up and run the migrations.

## What's Been Created

### ✅ Database Models (15 Models Across 8 Files)

1. **`models/enums.py`** - All enum types (10 enums)
   - UserRole, RelationshipType, PlanType, SubscriptionStatus
   - QuestionType, QuestionDifficulty, QuestionStatus
   - ExamType, ExamStatus, EvaluationStatus

2. **`models/user.py`** - User model with RBAC support
   - 4 roles: student, parent, teacher, admin
   - Timezone-aware timestamps
   - Check constraint for student_class requirement

3. **`models/mapping.py`** - ParentStudentMapping
   - Links parents to students (mandatory for child protection)
   - Prevents self-mapping
   - Tracks primary contact for billing

4. **`models/subscription.py`** - Subscription system (2 models)
   - SubscriptionPlan - Reference data for 4 plans (Basic, Premium MCQ, Premium, Centum)
   - Subscription - User subscriptions with monthly usage tracking

5. **`models/question.py`** - Question bank
   - Supports MCQ, VSA, SA, LA question types
   - JSONB for MCQ choices
   - ARRAY type for tags
   - Versioning support
   - CBSE unit tagging

6. **`models/exam_template.py`** - Configurable exam patterns
   - JSONB config for flexible exam structures
   - Support for board exams, section-wise, unit-wise practice

7. **`models/exam_instance.py`** - Exam attempts (4 models)
   - ExamInstance - Main exam with immutable snapshots
   - StudentMCQAnswer - MCQ answers with auto-evaluation
   - AnswerSheetUpload - S3 references for scanned sheets
   - UnansweredQuestion - Student-declared unanswered

8. **`models/evaluation.py`** - Teacher evaluation (2 models)
   - Evaluation - SLA tracking, teacher assignment
   - QuestionMark - Granular marks per question

9. **`models/system.py`** - System tables (3 models)
   - AuditLog - Immutable audit trail with triggers
   - Holiday - Working day calendar for SLA
   - SystemConfig - JSON key-value configuration

### ✅ Alembic Migrations (2 Files)

1. **`alembic/versions/001_complete_schema.py`** (935 lines)
   - Creates all 10 PostgreSQL ENUM types
   - Creates all 15 tables in correct dependency order
   - Creates 45+ indexes (including partial, composite, GIN)
   - Creates exclusion constraint for subscription overlaps
   - Creates immutability triggers for audit_logs
   - Enables btree_gist extension

2. **`alembic/versions/002_seed_reference_data.py`**
   - Seeds 4 subscription plans (Basic, Premium MCQ, Premium, Centum)
   - Seeds 26 national holidays (2025-2026)
   - Seeds 18 system configuration entries

### ✅ Key Features Implemented

**Production-Ready Constraints:**
- ✅ 30+ CheckConstraints for business rule validation
- ✅ 15+ UniqueConstraints for data integrity
- ✅ Exclusion constraint for overlapping active subscriptions
- ✅ Foreign key relationships with proper ON DELETE behavior
- ✅ Audit log immutability enforced via database triggers

**Performance Optimizations:**
- ✅ 45+ strategically placed indexes
- ✅ Partial indexes for filtered queries (active records only)
- ✅ Composite indexes for common query patterns
- ✅ GIN indexes for JSONB and ARRAY columns
- ✅ Strategic denormalization (class, exam_type, unit in child tables)

**Data Integrity:**
- ✅ UUID primary keys for all tables
- ✅ TIMESTAMPTZ for all timestamps (timezone-aware)
- ✅ Immutable exam snapshots (JSONB)
- ✅ Immutable audit logs (triggers prevent UPDATE/DELETE)
- ✅ Proper check constraints for marks, percentages, dates

---

## Prerequisites

### Python Version Requirement

**IMPORTANT:** Python 3.13 has compatibility issues with numpy 1.26.3. Use Python 3.10 or 3.11 instead.

**Recommended Setup:**

```bash
# Option 1: Using pyenv (Recommended)
pyenv install 3.11.9
pyenv local 3.11.9

# Option 2: Download Python 3.11 from python.org
# Then create a virtual environment with it
```

### PostgreSQL Database

Ensure PostgreSQL is running and accessible at:
```
DATABASE_URL=postgresql://postgres:admin%40246@localhost:5432/mvdb
```

You can verify connection:
```bash
psql -h localhost -U postgres -d mvdb -c "SELECT version();"
```

---

## Setup Instructions

### Step 1: Create Virtual Environment

```bash
cd C:\Users\jpthi\work\ThiruAgenticAI\en9\mathvidya\backend

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Git Bash):
source venv/Scripts/activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Note:** This installs all packages including:
- FastAPI, uvicorn
- SQLAlchemy 2.0, asyncpg, alembic
- Pydantic, python-jose, passlib
- Redis, Celery, Flower
- Boto3 (AWS S3)
- numpy, pandas, scikit-learn

### Step 3: Configure Environment

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and update:
```env
DATABASE_URL=postgresql+asyncpg://postgres:admin%40246@localhost:5432/mvdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

### Step 4: Run Migrations

```bash
# Run both migrations (creates all 15 tables + seeds data)
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgreSQLImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Complete database schema - all tables
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Seed reference data - subscription plans, holidays, system config
```

### Step 5: Verify Database

```bash
# Connect to database
psql -h localhost -U postgres -d mvdb

# List all tables
\dt

# Check table counts
SELECT 'users' as table_name, COUNT(*) as rows FROM users
UNION ALL SELECT 'subscription_plans', COUNT(*) FROM subscription_plans
UNION ALL SELECT 'holidays', COUNT(*) FROM holidays
UNION ALL SELECT 'system_config', COUNT(*) FROM system_config;
```

**Expected Result:**
```
   table_name      | rows
-------------------+------
 users             |    0
 subscription_plans|    4
 holidays          |   26
 system_config     |   18
```

---

## Database Schema Summary

### Tables Created (15)

| # | Table Name | Purpose | Key Features |
|---|------------|---------|--------------|
| 1 | `users` | All user types | 4 roles, RBAC, student_class constraint |
| 2 | `parent_student_mappings` | Parent-child links | Unique pairs, no self-mapping |
| 3 | `subscription_plans` | Plan definitions | 4 plans with limits, features, pricing |
| 4 | `subscriptions` | User subscriptions | Monthly counters, exclusion constraint |
| 5 | `questions` | Question bank | JSONB for MCQ, ARRAY tags, versioning |
| 6 | `exam_templates` | Exam patterns | JSONB config, unit weightage |
| 7 | `exam_instances` | Exam attempts | Immutable JSONB snapshots |
| 8 | `student_mcq_answers` | MCQ answers | Auto-evaluation results |
| 9 | `answer_sheet_uploads` | S3 references | Scanned answer sheets |
| 10 | `unanswered_questions` | Declared unanswered | 0 marks, no penalty |
| 11 | `evaluations` | Teacher assignments | SLA tracking, one per exam |
| 12 | `question_marks` | Granular marking | Per-question marks for analytics |
| 13 | `audit_logs` | Audit trail | Immutable (triggers), all events |
| 14 | `holidays` | SLA calendar | National holidays, working days |
| 15 | `system_config` | System settings | JSON key-value store |

### Key Relationships

```
users (1) ----< (M) subscriptions
users (1) ----< (M) exam_instances
users (1) ----< (M) evaluations (as teacher)
users (1) ----< (M) parent_student_mappings (as parent)
users (1) ----< (M) parent_student_mappings (as student)

subscription_plans (1) ----< (M) subscriptions

exam_templates (1) ----< (M) exam_instances

exam_instances (1) ----< (M) student_mcq_answers
exam_instances (1) ----< (M) answer_sheet_uploads
exam_instances (1) ----< (M) unanswered_questions
exam_instances (1) ---- (1) evaluations

evaluations (1) ----< (M) question_marks
```

---

## Seed Data Loaded

### Subscription Plans (4)

| Plan Type | Display Name | Exams/Month | SLA | Leaderboard | Price (Annual) |
|-----------|--------------|-------------|-----|-------------|----------------|
| `basic` | Basic Plan | 5 | 48hr | No | ₹2,999 |
| `premium_mcq` | Premium MCQ | 15 | 48hr | No | ₹4,999 |
| `premium` | Premium Plan | 50 | 48hr | Yes | ₹9,999 |
| `centum` | Plan Centum | 50 | 24hr | Yes | ₹14,999 |

### National Holidays (26)

2025: Republic Day, Holi, Id-ul-Fitr, Ambedkar Jayanti, Good Friday, May Day, Independence Day, Janmashtami, Gandhi Jayanti, Dussehra, Diwali, Guru Nanak Jayanti, Christmas

2026: (Same holidays for future planning)

### System Configuration (18 entries)

- SLA working hours: 09:00 - 18:00 IST
- Leaderboard top N: 10 students
- Max upload size: 5 MB
- Allowed MIME types: JPEG, PNG, PDF
- Evaluation UI stamps: tick, cross, half, circle, star
- Analytics refresh: 2 AM IST daily
- CBSE unit names for Class X and XII

---

## Testing the Setup

### 1. Test Database Connection

```python
# test_db_connection.py
import asyncio
from database import engine

async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute(sa.text("SELECT version()"))
        print(result.scalar())

asyncio.run(test_connection())
```

### 2. Create Test User

```python
# test_create_user.py
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    async with AsyncSessionLocal() as session:
        # Create student
        student = User(
            email="student@test.com",
            password_hash=pwd_context.hash("password123"),
            role=UserRole.STUDENT,
            first_name="Test",
            last_name="Student",
            student_class="XII"
        )
        session.add(student)
        await session.commit()
        print(f"Created user: {student.email}")

asyncio.run(create_test_user())
```

### 3. Verify Subscription Plans

```python
# test_subscription_plans.py
import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal
from models import SubscriptionPlan

async def list_plans():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SubscriptionPlan))
        plans = result.scalars().all()
        for plan in plans:
            print(f"{plan.display_name}: {plan.exams_per_month} exams/month")

asyncio.run(list_plans())
```

---

## Common Issues & Solutions

### Issue 1: "alembic: command not found"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/Scripts/activate  # Git Bash
venv\Scripts\activate          # Windows CMD

# Or run with python -m
python -m alembic upgrade head
```

### Issue 2: "No module named 'alembic'"

**Solution:**
```bash
pip install alembic==1.13.1
```

### Issue 3: "Database 'mvdb' does not exist"

**Solution:**
```bash
# Create database
psql -h localhost -U postgres -c "CREATE DATABASE mvdb;"
```

### Issue 4: "Extension btree_gist not found"

**Solution:**
```bash
# Connect and create extension
psql -h localhost -U postgres -d mvdb -c "CREATE EXTENSION btree_gist;"
```

### Issue 5: Python 3.13 compatibility issues

**Solution:**
Use Python 3.11 or 3.10 instead. See Prerequisites section above.

---

## Next Steps

### 1. Create Pydantic Schemas

Create validation schemas for all models:
- `schemas/mapping.py`
- `schemas/subscription.py`
- `schemas/question.py`
- `schemas/exam_template.py`
- `schemas/exam_instance.py`
- `schemas/evaluation.py`
- `schemas/system.py`
- `schemas/analytics.py`
- `schemas/leaderboard.py`

### 2. Implement API Routes

Create route handlers:
- `routes/subscriptions.py` - Subscription management
- `routes/questions.py` - Question bank CRUD
- `routes/exams.py` - Exam generation and taking
- `routes/answers.py` - Answer submission
- `routes/evaluations.py` - Teacher evaluation
- `routes/analytics.py` - Performance data
- `routes/leaderboard.py` - Rankings
- `routes/admin.py` - Admin operations
- `routes/parent.py` - Parent dashboard

### 3. Implement Business Logic Services

Create service files:
- `services/subscription_service.py` - Plan validation, counter tracking
- `services/exam_service.py` - Exam generation algorithm
- `services/evaluation_service.py` - Scoring logic
- `services/sla_service.py` - SLA calculation with holiday exclusion
- `services/s3_service.py` - S3 upload/download with signed URLs
- `services/analytics_service.py` - Performance aggregation
- `services/leaderboard_service.py` - Ranking computation

### 4. Implement Background Tasks

Create Celery tasks:
- `tasks/sla_monitoring.py` - Check SLA deadlines
- `tasks/teacher_assignment.py` - Assign evaluations to teachers
- `tasks/leaderboard_refresh.py` - Recompute rankings
- `tasks/analytics_aggregation.py` - Compute analytics
- `tasks/notification_tasks.py` - Send emails/notifications

### 5. Testing

Create comprehensive tests:
- Unit tests for all models
- Integration tests for all routes
- Service layer tests
- Background task tests
- End-to-end workflow tests

### 6. Deployment

Set up AWS infrastructure:
- RDS PostgreSQL (Multi-AZ)
- ElastiCache Redis
- ECS/EKS for containers
- S3 for file storage
- CloudFront CDN
- CloudWatch logging

---

## Database Management Commands

### View Current Migration

```bash
alembic current
```

### Migration History

```bash
alembic history --verbose
```

### Rollback One Migration

```bash
alembic downgrade -1
```

### Rollback to Specific Revision

```bash
alembic downgrade 001
```

### Rollback All Migrations

```bash
alembic downgrade base
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to users"

# Empty migration
alembic revision -m "Custom migration"
```

---

## Database Backup & Restore

### Backup

```bash
# Full database backup
pg_dump -h localhost -U postgres -d mvdb > mathvidya_backup.sql

# Schema only
pg_dump -h localhost -U postgres -d mvdb --schema-only > mathvidya_schema.sql

# Data only
pg_dump -h localhost -U postgres -d mvdb --data-only > mathvidya_data.sql
```

### Restore

```bash
# Restore full backup
psql -h localhost -U postgres -d mvdb < mathvidya_backup.sql

# Restore to new database
createdb mathvidya_test
psql -h localhost -U postgres -d mathvidya_test < mathvidya_backup.sql
```

---

## Performance Tuning Tips

1. **Use connection pooling** (already configured in `database.py`)
2. **Enable query logging** in development:
   ```python
   # database.py
   engine = create_async_engine(settings.DATABASE_URL, echo=True)
   ```
3. **Monitor slow queries**:
   ```sql
   -- Enable slow query logging in PostgreSQL
   ALTER DATABASE mvdb SET log_min_duration_statement = 1000;  -- Log queries > 1s
   ```
4. **Use EXPLAIN ANALYZE** for query optimization:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM exam_instances WHERE student_user_id = '...' AND status = 'evaluated';
   ```
5. **Monitor index usage**:
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   ORDER BY idx_scan ASC;
   ```

---

## Support

For issues or questions:
1. Check this documentation first
2. Review ENGINEERING-SPEC.md for requirements
3. Check CLAUDE.md for project overview
4. Review ALEMBIC-SETUP.md for Alembic details

---

## Summary

✅ **15 tables created** with production-ready schema
✅ **45+ indexes** for optimal performance
✅ **30+ constraints** for data integrity
✅ **Immutable audit logs** with database triggers
✅ **Exclusion constraint** for subscription overlaps
✅ **4 subscription plans** seeded
✅ **26 national holidays** seeded
✅ **18 system configurations** seeded

**Ready for implementation of:**
- Pydantic schemas
- API routes
- Business logic services
- Background tasks
- Testing
- Deployment

Your database is production-ready! 🚀
