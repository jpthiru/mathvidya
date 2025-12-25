# Mathvidya FastAPI Implementation Quick-Start Guide

**Last Updated:** 2025-12-23
**Stack:** Python FastAPI + React + PostgreSQL + Redis

---

## ✅ What's Been Updated

The ENGINEERING-SPEC.md has been fully updated from Node.js/TypeScript to **Python FastAPI**:

### Updated Sections:

1. **✅ Backend Technology Stack** - Now uses FastAPI + SQLAlchemy + Celery
2. **✅ Background Jobs** - Celery with Redis (instead of Bull)
3. **✅ SLA Enforcement** - Python async code with Celery Beat
4. **✅ RBAC & Security** - FastAPI dependency injection pattern
5. **✅ Input Validation** - Pydantic models (automatic validation)
6. **✅ Rate Limiting** - slowapi library
7. **✅ S3 Integration** - boto3 async operations
8. **✅ Database Integration** - SQLAlchemy 2.0 async
9. **✅ Teacher Assignment** - SQLAlchemy ORM queries
10. **Frontend Architecture** - Already React (no changes needed)

### Database Schemas

No changes needed - PostgreSQL SQL remains identical.

---

## 🚀 Project Setup (From Scratch)

### Prerequisites

```bash
# Required software
Python 3.11+
PostgreSQL 14+
Redis 6+
Node.js 18+ (for frontend only)
```

---

## Backend Setup

### 1. Create Project Structure

```bash
mkdir mathvidya-backend
cd mathvidya-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Project structure
mkdir -p {app,models,schemas,routes,services,dependencies,tasks,config,tests}
touch app/__init__.py
```

### 2. Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << EOF
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Redis & Caching
redis[hiredis]==5.0.1
celery==5.3.6
flower==2.0.1

# AWS
boto3==1.34.26
botocore==1.34.26

# Data Validation
pydantic[email]==2.5.3
pydantic-settings==2.1.0

# Rate Limiting
slowapi==0.1.9

# Math & Analytics (for V2 ML features)
numpy==1.26.3
pandas==2.1.4

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
EOF

# Install
pip install -r requirements.txt
```

### 3. Database Configuration

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# Async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set False in production
    pool_size=20,
    max_overflow=40
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency for FastAPI
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/mathvidya"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # AWS
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "mathvidya-production"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4. Create First Model

```python
# models/user.py
from sqlalchemy import Column, String, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    student = "student"
    parent = "parent"
    teacher = "teacher"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))

    # Student-specific
    student_class = Column(String(10))
    student_photo_url = Column(String)
    school_name = Column(String(255))

    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
```

### 5. Create Main FastAPI App

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routes import auth, exams, evaluations, analytics
from database import engine, Base

app = FastAPI(
    title="Mathvidya API",
    description="CBSE Mathematics Practice Platform",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc"  # ReDoc
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(exams.router, prefix="/api/v1", tags=["Exams"])
app.include_router(evaluations.router, prefix="/api/v1", tags=["Evaluations"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])

@app.on_event("startup")
async def startup():
    # Create tables (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mathvidya-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### 6. Create First Route (Authentication)

```python
# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from database import get_session
from models.user import User
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/auth/register", status_code=201)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """Register new user"""

    # Check if email exists
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    password_hash = pwd_context.hash(request.password)

    # Create user
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        role=request.role,
        first_name=request.first_name,
        last_name=request.last_name,
        student_class=request.student_class if request.role == 'student' else None
    )

    session.add(new_user)
    await session.commit()

    return {
        "user_id": str(new_user.user_id),
        "email": new_user.email,
        "message": "Registration successful"
    }

@router.post("/auth/login")
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """Authenticate user and return JWT"""

    # Find user
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role},
        expires_delta=access_token_expires
    )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await session.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role,
            "first_name": user.first_name
        }
    }

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

```python
# schemas/auth.py
from pydantic import BaseModel, EmailStr
from models.user import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    first_name: str
    last_name: str
    student_class: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
```

### 7. Run the Backend

```bash
# Terminal 1: Start FastAPI server
uvicorn main:app --reload --port 8000

# Terminal 2: Start Redis (if not running as service)
redis-server

# Terminal 3: Start Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Terminal 4: Start Celery Beat (scheduled tasks)
celery -A tasks.celery_app beat --loglevel=info

# Terminal 5: Start Flower (Celery monitoring UI)
celery -A tasks.celery_app flower --port=5555
```

**Access:**
- API Docs (Swagger): http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Flower (Celery): http://localhost:5555

---

## Frontend Setup (React)

### 1. Create React App

```bash
npx create-react-app mathvidya-frontend --template typescript
cd mathvidya-frontend

# Install dependencies
npm install @reduxjs/toolkit react-redux react-router-dom
npm install axios
npm install @mui/material @emotion/react @emotion/styled
npm install react-katex katex  # Math rendering
npm install react-hook-form zod @hookform/resolvers
npm install react-dropzone  # File uploads
```

### 2. Configure API Client

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

### 3. Test API Connection

```typescript
// src/App.tsx
import { useEffect } from 'react';
import apiClient from './api/client';

function App() {
  useEffect(() => {
    apiClient.get('/health')
      .then(response => console.log('API Connected:', response.data))
      .catch(error => console.error('API Error:', error));
  }, []);

  return (
    <div className="App">
      <h1>Mathvidya</h1>
      <p>Check console for API connection status</p>
    </div>
  );
}

export default App;
```

### 4. Run Frontend

```bash
npm start
# Opens http://localhost:3000
```

---

## Database Setup

### 1. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE mathvidya;
CREATE USER mathvidya_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE mathvidya TO mathvidya_user;
\q
```

### 2. Run Migrations (Alembic)

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini
# sqlalchemy.url = postgresql+asyncpg://mathvidya_user:password@localhost/mathvidya

# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

---

## Testing

### Backend Tests

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_register():
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
        assert "user_id" in response.json()
```

```bash
# Run tests
pytest tests/ -v
```

---

## Next Steps

1. **Implement remaining models** (from ENGINEERING-SPEC.md Section 2)
2. **Create exam routes** (start exam, submit MCQ, upload answers)
3. **Implement evaluation routes** (teacher queue, submit evaluation)
4. **Add analytics endpoints**
5. **Integrate S3 for file uploads**
6. **Set up Celery tasks** (SLA monitoring, teacher assignment)
7. **Build React components** (exam UI, dashboard, evaluation interface)

---

## Reference Documents

- **ENGINEERING-SPEC.md** - Complete technical specification (database schemas, API contracts, workflows)
- **CLAUDE.md** - Project overview and architecture summary
- **TECH-STACK-COMPARISON.md** - Why we chose FastAPI over Node.js

---

## Common Commands Cheat Sheet

```bash
# Backend
uvicorn main:app --reload                    # Start API server
celery -A tasks.celery_app worker -l info    # Start Celery worker
celery -A tasks.celery_app beat -l info      # Start Celery scheduler
celery -A tasks.celery_app flower            # Start monitoring UI
alembic upgrade head                         # Run DB migrations
pytest tests/                                # Run tests

# Frontend
npm start                                    # Start React dev server
npm run build                                # Production build
npm test                                     # Run tests

# Database
psql -U mathvidya_user -d mathvidya         # Connect to DB
alembic revision --autogenerate -m "msg"    # Create migration

# Redis
redis-cli                                    # Redis CLI
redis-cli ping                               # Check if running
```

---

## Deployment (AWS ECS - Production)

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml (for local development)
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/mathvidya
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: mathvidya
      POSTGRES_USER: mathvidya_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A tasks.celery_app worker -l info
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
```

```bash
# Build and run
docker-compose up --build
```

---

## Support

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Celery:** https://docs.celeryq.dev
- **React:** https://react.dev

---

**Happy Coding! 🚀**
