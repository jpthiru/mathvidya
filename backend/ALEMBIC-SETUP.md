# Alembic Setup Guide

**Status:** ✅ Fully Configured with Async SQLAlchemy Support

---

## ✅ What's Already Configured

1. ✅ `alembic.ini` - Main configuration file
2. ✅ `alembic/env.py` - Async SQLAlchemy environment
3. ✅ `alembic/script.py.mako` - Migration template
4. ✅ `alembic/versions/` - Migration folder
5. ✅ `alembic/versions/001_initial_schema.py` - Initial User table migration

---

## 🚀 First Time Setup

### 1. Create PostgreSQL Database

```bash
# Create database
createdb mathvidya

# Or connect to PostgreSQL and create manually
psql -U postgres
CREATE DATABASE mathvidya;
CREATE USER mathvidya_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mathvidya TO mathvidya_user;
\q
```

### 2. Configure Environment

```bash
cd backend

# Create .env file (if not exists)
cp .env.example .env

# Edit .env and set DATABASE_URL
# DATABASE_URL=postgresql+asyncpg://mathvidya_user:password@localhost:5432/mathvidya
```

### 3. Run Initial Migration

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Apply initial migration (creates users table)
alembic upgrade head

# Verify
alembic current
# Should show: 001 (head)
```

### 4. Verify Database

```bash
# Connect to database
psql -U mathvidya_user -d mathvidya

# List tables
\dt

# Should see:
# - users
# - alembic_version

# Describe users table
\d users

# Exit
\q
```

---

## 📝 Daily Development Workflow

### Scenario 1: Adding a New Table

```bash
# 1. Create model
# Edit models/exam.py and create Exam class

# 2. Import in alembic/env.py
# Add: from models.exam import Exam

# 3. Generate migration
alembic revision --autogenerate -m "Add exams table"

# 4. Review generated file
# Check alembic/versions/XXX_add_exams_table.py

# 5. Apply migration
alembic upgrade head

# 6. Verify
psql -U mathvidya_user -d mathvidya -c "\dt"
```

### Scenario 2: Modifying an Existing Table

```bash
# 1. Modify model
# Edit models/user.py and add new column

# 2. Generate migration
alembic revision --autogenerate -m "Add bio field to users"

# 3. Review and apply
alembic upgrade head
```

### Scenario 3: Rolling Back a Migration

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001

# View history
alembic history --verbose
```

---

## 🔍 Useful Commands

```bash
# Show current database version
alembic current

# Show all migrations
alembic history

# Show pending migrations
alembic history --verbose

# Show SQL without executing
alembic upgrade head --sql

# Stamp database to specific version (without running migrations)
alembic stamp 001

# Reset to base (DANGEROUS - drops all tables!)
alembic downgrade base
```

---

## 🔥 Quick Reset (Development Only!)

If you want to start fresh with migrations:

```bash
# 1. Drop database
dropdb mathvidya

# 2. Recreate database
createdb mathvidya

# 3. Run migrations from scratch
alembic upgrade head

# All tables will be recreated from migrations
```

---

## 🧪 Testing Migrations

### Before Committing a Migration

```bash
# 1. Apply migration
alembic upgrade head

# 2. Test rollback
alembic downgrade -1

# 3. Re-apply
alembic upgrade head

# 4. Verify both work without errors
```

### Test with Fresh Database

```bash
# Create test database
createdb mathvidya_test

# Update DATABASE_URL in .env temporarily
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mathvidya_test

# Run migrations
alembic upgrade head

# Verify everything works

# Clean up
dropdb mathvidya_test

# Restore original DATABASE_URL in .env
```

---

## 📋 Migration Checklist

Before creating a migration:
- [ ] Model changes are complete
- [ ] Model imported in `alembic/env.py`
- [ ] Database backup created (production)
- [ ] `.env` configured correctly

After creating a migration:
- [ ] Review generated migration file
- [ ] Test `alembic upgrade head`
- [ ] Test `alembic downgrade -1`
- [ ] Test `alembic upgrade head` again
- [ ] Verify database schema is correct
- [ ] Commit migration file to git

---

## ⚠️ Common Issues & Solutions

### Issue: "Can't locate revision identified by 'XXX'"

**Solution:**
```bash
# Check what version database thinks it is
psql -U mathvidya_user -d mathvidya -c "SELECT * FROM alembic_version;"

# Stamp to correct version
alembic stamp head  # or specific revision
```

### Issue: "Target database is not up to date"

**Solution:**
```bash
# Show current version
alembic current

# Show what version should be
alembic history

# Stamp to head
alembic stamp head
```

### Issue: Migration fails with "relation already exists"

**Solution:**
```bash
# Option 1: Drop the table manually and retry
psql -U mathvidya_user -d mathvidya -c "DROP TABLE IF EXISTS table_name CASCADE;"
alembic upgrade head

# Option 2: Skip this migration (NOT RECOMMENDED)
alembic stamp +1
```

### Issue: Auto-generate doesn't detect changes

**Solution:**
```bash
# Make sure model is imported in alembic/env.py
# Check: from models.your_model import YourModel

# Make sure model inherits from Base
# Check: class YourModel(Base):

# Try manual migration
alembic revision -m "Manual migration"
# Then edit the file manually
```

---

## 📚 Additional Resources

- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **Async Tutorial:** https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
- **Full README:** See `alembic/README.md` for detailed commands

---

## ✅ Configuration Status

| Component | Status | File |
|-----------|--------|------|
| Alembic Config | ✅ Complete | `alembic.ini` |
| Async Environment | ✅ Complete | `alembic/env.py` |
| Migration Template | ✅ Complete | `alembic/script.py.mako` |
| Initial Migration | ✅ Complete | `alembic/versions/001_initial_schema.py` |
| Documentation | ✅ Complete | `alembic/README.md` |

**Alembic is fully configured and ready to use!** 🚀

---

## 🎯 Next Steps

1. Run initial migration:
   ```bash
   alembic upgrade head
   ```

2. Start building more models (see `ENGINEERING-SPEC.md` Section 2 for all schemas)

3. Generate migrations as you add models:
   ```bash
   alembic revision --autogenerate -m "Add new model"
   ```

**Happy migrating! 🔄**
