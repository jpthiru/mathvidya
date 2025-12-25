# Mathvidya FastAPI Backend - Quick Start

## Prerequisites

- Python 3.14+
- PostgreSQL 14+ (running on localhost:5432)
- Redis 6+ (optional, for Celery tasks)

## Setup

### 1. Activate Virtual Environment

```bash
# Windows
cd backend
source mvenv/Scripts/activate

# Linux/Mac
cd backend
source venv/bin/activate
```

### 2. Install Dependencies (if not already installed)

```bash
pip install -r requirements_3_14.txt
```

### 3. Configure Environment

The `.env` file is already configured. Key settings:

```env
DATABASE_URL=postgresql+asyncpg://postgres:admin@246@localhost:5432/mvdb
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

### 4. Database is Ready

The database migrations have already been run:
- ✅ 16 tables created
- ✅ Seed data loaded
- ✅ Test users created

## Running the Server

### Start FastAPI Application

```bash
uvicorn main:app --reload --port 8000
```

The server will start on: **http://localhost:8000**

### Verify Server is Running

Open in browser or use curl:

```bash
# Health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# API documentation
# Open: http://localhost:8000/api/docs
```

## Testing the API

### Option 1: Interactive API Documentation

Visit **http://localhost:8000/api/docs** to use the interactive Swagger UI.

### Option 2: Test Script

Run the provided test script:

```bash
# Make sure server is running first!
python test_api.py
```

### Option 3: Manual Testing with curl

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mathvidya.com","password":"admin123"}'

# Save the access_token from the response

# 2. Get current user info
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 3. Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@test.com",
    "password": "SecurePass123",
    "role": "student",
    "first_name": "New",
    "last_name": "Student",
    "student_class": "XII"
  }'
```

## Test Users

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@mathvidya.com | admin123 |
| Teacher | teacher@mathvidya.com | teacher123 |
| Student | student@mathvidya.com | student123 |

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user (requires auth)
- `POST /api/v1/auth/change-password` - Change password (requires auth)
- `POST /api/v1/auth/logout` - Logout

### Health

- `GET /health` - Service health check
- `GET /health/db` - Database connection health

## Features Implemented

✅ **Authentication & Authorization**
- JWT token-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Secure token generation

✅ **Core Infrastructure**
- FastAPI with async/await
- SQLAlchemy 2.0 async ORM
- Pydantic validation
- CORS middleware
- Rate limiting
- Custom exception handling
- Logging

✅ **Database**
- PostgreSQL with asyncpg driver
- 16 tables with relationships
- Alembic migrations
- Enum type handling
- Seed data

## Development

### File Structure

```
backend/
├── routes/          # API endpoints
│   └── auth.py     # Authentication routes
├── schemas/         # Pydantic models
│   └── auth.py     # Auth request/response schemas
├── dependencies/    # FastAPI dependencies
│   └── auth.py     # JWT & RBAC dependencies
├── models/          # SQLAlchemy models
│   ├── user.py
│   ├── subscription.py
│   ├── exam_*.py
│   └── ...
├── config/
│   └── settings.py  # Configuration
├── main.py          # FastAPI app
└── database.py      # Database setup
```

### Adding New Endpoints

1. Create schema in `schemas/`
2. Create route in `routes/`
3. Add router to `main.py`
4. Use dependencies for auth/RBAC

### Using RBAC

```python
from dependencies.auth import require_role, require_student, require_teacher
from models.enums import UserRole

# Single role
@router.get("/student-only")
async def student_endpoint(user = Depends(require_student)):
    ...

# Multiple roles
@router.get("/teacher-or-admin")
async def admin_endpoint(user = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))):
    ...
```

## Debugging

### Enable Debug Mode

Already enabled in `.env`:
```env
DEBUG=True
```

This enables:
- Detailed error messages
- API documentation at `/api/docs`
- Auto-reload on code changes

### View Logs

The application logs to console with timestamps:
```
2025-12-24 01:13:00,451 - main - INFO - Starting Mathvidya API v1.0.0
```

### Database Queries

SQLAlchemy query logging is enabled. View SQL in console.

## Common Issues

### Port Already in Use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error

1. Verify PostgreSQL is running
2. Check DATABASE_URL in `.env`
3. Test connection: `psql -U postgres -d mvdb`

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements_3_14.txt --force-reinstall
```

## Next Steps

1. **Implement Exam Routes** - Start exam, submit answers
2. **Implement Evaluation Routes** - Teacher evaluation workflow
3. **Add S3 Integration** - File upload service
4. **Setup Celery** - Background tasks
5. **Add Tests** - pytest test suite

## Documentation

- **Implementation Status**: See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
- **API Quickstart**: See [FASTAPI-QUICKSTART.md](../FASTAPI-QUICKSTART.md)
- **Project Overview**: See [CLAUDE.md](../CLAUDE.md)

## Support

For questions or issues:
1. Check implementation status document
2. Review API documentation at `/api/docs`
3. Check logs for errors
4. Verify database is accessible

---

**Server Ready!** 🚀

Start with: `uvicorn main:app --reload --port 8000`
