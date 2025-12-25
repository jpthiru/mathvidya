# Alembic Database Migrations

This directory contains database migration files for Mathvidya.

---

## 🚀 Quick Start

### Initial Setup

```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Create database if not exists
createdb mathvidya

# Run initial migration
alembic upgrade head
```

---

## 📋 Common Commands

### View Migration History

```bash
# Show current migration version
alembic current

# Show all migrations
alembic history

# Show pending migrations
alembic history --verbose
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add exams table"

# Create empty migration (manual)
alembic revision -m "Add custom index"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Upgrade to specific version
alembic upgrade 002

# Show SQL without executing
alembic upgrade head --sql
```

### Rollback Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001

# Rollback all migrations (DANGEROUS!)
alembic downgrade base
```

### Check Migration Status

```bash
# Show current database version
alembic current

# Show pending migrations
alembic show head
```

---

## 📁 Directory Structure

```
alembic/
├── README.md              # This file
├── env.py                 # Migration environment (async SQLAlchemy)
├── script.py.mako         # Template for new migrations
└── versions/              # Migration files
    └── 001_initial_schema.py
```

---

## 🔨 Creating Migrations

### 1. Auto-generate from Models (Recommended)

```bash
# After creating/modifying a model
alembic revision --autogenerate -m "Add evaluation table"
```

Alembic will detect changes and generate migration code automatically.

### 2. Manual Migration

```bash
# Create empty migration file
alembic revision -m "Add custom index on email"
```

Then edit the generated file:

```python
def upgrade() -> None:
    op.create_index('idx_custom_email', 'users', ['email', 'is_active'])

def downgrade() -> None:
    op.drop_index('idx_custom_email', table_name='users')
```

---

## ⚠️ Important Notes

### Before Creating Migrations

1. **Import all models** in `alembic/env.py`:
```python
from models.user import User
from models.exam import Exam  # Add as you create models
from models.evaluation import Evaluation
```

2. **Test in development first**:
```bash
# Test upgrade
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

3. **Review generated migrations**:
   - Auto-generated migrations may not be perfect
   - Always review before committing
   - Add data migrations manually if needed

### Migration Best Practices

✅ **DO:**
- Keep migrations small and focused
- Test both upgrade and downgrade
- Review auto-generated migrations
- Add comments for complex changes
- Use descriptive migration messages
- Version control all migrations

❌ **DON'T:**
- Edit migrations after they're committed
- Delete old migrations
- Skip migrations in sequence
- Run migrations on production without testing
- Modify existing tables without migrations

---

## 🔄 Migration Workflow

### Development Flow

```bash
# 1. Create/modify model
# Edit models/exam.py

# 2. Generate migration
alembic revision --autogenerate -m "Add exam table"

# 3. Review migration file
# Check alembic/versions/XXX_add_exam_table.py

# 4. Test migration
alembic upgrade head

# 5. Test rollback
alembic downgrade -1

# 6. Re-apply
alembic upgrade head

# 7. Commit migration file
git add alembic/versions/XXX_add_exam_table.py
git commit -m "Add exam table migration"
```

### Production Deployment

```bash
# 1. Backup database first!
pg_dump mathvidya > backup_$(date +%Y%m%d).sql

# 2. Check current version
alembic current

# 3. Show pending migrations
alembic history --verbose

# 4. Dry run (show SQL)
alembic upgrade head --sql

# 5. Apply migrations
alembic upgrade head

# 6. Verify
alembic current
```

---

## 🐛 Troubleshooting

### "Target database is not up to date"

```bash
# Reset alembic version table
alembic stamp head

# Or start fresh
alembic downgrade base
alembic upgrade head
```

### "Can't locate revision identified by 'XXX'"

```bash
# Check migration history
alembic history

# Stamp to specific version
alembic stamp 001
```

### Migration conflicts

```bash
# If you have conflicting migrations:
# 1. Downgrade to common ancestor
alembic downgrade 001

# 2. Delete conflicting migration files
rm alembic/versions/002_*.py

# 3. Regenerate
alembic revision --autogenerate -m "Regenerated migration"

# 4. Upgrade
alembic upgrade head
```

### Database doesn't match models

```bash
# This happens when you changed models without creating migrations

# Option 1: Generate migration for differences
alembic revision --autogenerate -m "Sync database with models"

# Option 2: Reset database (DEVELOPMENT ONLY!)
alembic downgrade base
alembic upgrade head
```

---

## 📊 Example: Adding a New Table

### 1. Create the Model

```python
# models/exam.py
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid

class Exam(Base):
    __tablename__ = "exams"

    exam_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    total_marks = Column(Integer, nullable=False)
```

### 2. Import in env.py

```python
# alembic/env.py
from models.user import User
from models.exam import Exam  # Add this line
```

### 3. Generate Migration

```bash
alembic revision --autogenerate -m "Add exams table"
```

### 4. Review Generated File

```python
# alembic/versions/002_add_exams_table.py
def upgrade() -> None:
    op.create_table('exams',
        sa.Column('exam_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('total_marks', sa.Integer(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('exams')
```

### 5. Apply Migration

```bash
alembic upgrade head
```

---

## 📚 Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Async Alembic with FastAPI](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)
- [SQLAlchemy Core Operations](https://docs.sqlalchemy.org/en/20/core/metadata.html)

---

**Migration Version:** 001 (Initial Schema)
**Last Updated:** 2025-12-23
