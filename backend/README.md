# Mathvidya Backend - FastAPI

Python FastAPI backend for the Mathvidya platform.

---

## 📁 Directory Structure

```
backend/
├── models/             # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py
│   ├── exam.py
│   ├── evaluation.py
│   └── ...
│
├── schemas/            # Pydantic validation schemas
│   ├── __init__.py
│   ├── user.py
│   ├── exam.py
│   └── ...
│
├── routes/             # FastAPI route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── exams.py
│   ├── evaluations.py
│   └── ...
│
├── services/           # Business logic layer
│   ├── __init__.py
│   ├── exam_service.py
│   ├── evaluation_service.py
│   ├── s3_service.py
│   └── ...
│
├── dependencies/       # FastAPI dependencies (RBAC, etc.)
│   ├── __init__.py
│   └── auth.py
│
├── tasks/              # Celery background tasks
│   ├── __init__.py
│   ├── celery_app.py
│   ├── sla_tasks.py
│   └── analytics_tasks.py
│
├── config/             # Configuration
│   ├── __init__.py
│   └── settings.py
│
├── tests/              # Pytest tests
│   ├── __init__.py
│   ├── test_auth.py
│   └── ...
│
├── alembic/            # Database migrations
│   └── versions/
│
├── main.py             # FastAPI application entry point
├── database.py         # Database configuration
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variables template
```

---

## 🚀 Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Setup Database

```bash
# Create PostgreSQL database
createdb mathvidya

# Run migrations
alembic upgrade head
```

### 5. Start Development Server

```bash
uvicorn main:app --reload --port 8000
```

---

## 📝 Common Commands

### Development Server

```bash
# Start with auto-reload
uvicorn main:app --reload

# Specify host and port
uvicorn main:app --host 0.0.0.0 --port 8000

# With logging
uvicorn main:app --reload --log-level debug
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (DANGEROUS!)
alembic downgrade base
```

### Celery Workers

```bash
# Start worker
celery -A tasks.celery_app worker --loglevel=info

# Start Beat scheduler
celery -A tasks.celery_app beat --loglevel=info

# Start Flower monitoring
celery -A tasks.celery_app flower --port=5555
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_auth.py -v

# Run with print statements
pytest -s
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Exams (TODO)
- `GET /api/v1/exams/templates` - List exam templates
- `POST /api/v1/exams/start` - Start new exam
- `POST /api/v1/exams/{id}/submit-mcq` - Submit MCQ answers
- `GET /api/v1/exams/{id}/results` - Get exam results

### Evaluations (TODO)
- `GET /api/v1/evaluations/queue` - Get teacher's evaluation queue
- `POST /api/v1/evaluations/{id}/submit` - Submit evaluation

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py         # Pytest fixtures
├── test_auth.py        # Authentication tests
├── test_exams.py       # Exam tests
└── test_evaluations.py # Evaluation tests
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "student",
            "first_name": "Test",
            "last_name": "User",
            "student_class": "XII"
        })
        assert response.status_code == 201
```

---

## 📊 Database Models

### Key Models

1. **User** - Students, parents, teachers, admins
2. **Subscription** - User subscription plans
3. **Question** - Question bank
4. **ExamTemplate** - Configurable exam patterns
5. **ExamInstance** - Student exam attempts
6. **Evaluation** - Teacher evaluations
7. **AuditLog** - Immutable audit trail

See `models/` directory for complete model definitions.

---

## 🔒 Security

### RBAC Implementation

```python
from dependencies.auth import require_role
from models.user import UserRole

@router.get("/admin-only")
async def admin_endpoint(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    # Only admins can access
    return {"message": "Admin access granted"}
```

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash("plain_password")

# Verify password
is_valid = pwd_context.verify("plain_password", hashed)
```

---

## 📦 Adding New Features

### 1. Create Model

```python
# models/exam.py
from sqlalchemy import Column, String, Integer
from database import Base

class Exam(Base):
    __tablename__ = "exams"

    exam_id = Column(UUID, primary_key=True)
    title = Column(String(255))
    # ...
```

### 2. Create Schema

```python
# schemas/exam.py
from pydantic import BaseModel

class ExamCreate(BaseModel):
    title: str
    # ...

class ExamResponse(BaseModel):
    exam_id: UUID
    title: str
    # ...
```

### 3. Create Route

```python
# routes/exams.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session

router = APIRouter()

@router.post("/exams")
async def create_exam(
    exam: ExamCreate,
    session: AsyncSession = Depends(get_session)
):
    # Implementation
    pass
```

### 4. Include Router

```python
# main.py
from routes import exams

app.include_router(exams.router, prefix="/api/v1", tags=["Exams"])
```

---

## 🐛 Debugging

### Enable Debug Mode

```python
# .env
DEBUG=True
```

### View SQL Queries

```python
# database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True  # Logs all SQL queries
)
```

### Use Python Debugger

```python
import pdb

# Set breakpoint
pdb.set_trace()
```

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic](https://docs.pydantic.dev/)
- [Celery](https://docs.celeryq.dev/)
- [Alembic](https://alembic.sqlalchemy.org/)

---

**Happy Coding! 🚀**
