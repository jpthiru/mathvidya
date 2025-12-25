# Mathvidya - CBSE Mathematics Practice Platform

**Version:** 1.0.0
**Stack:** Python FastAPI + React + PostgreSQL + Redis

---

## 🎯 Project Overview

Mathvidya is an online mathematics practice platform for CBSE students (Classes X and XII) in India. The platform combines flexible online exam practice with personalized evaluation by expert mathematics teachers, data-driven analytics, and predicted board examination scores.

### Key Features

- ✅ Board-exam-aligned practice questions (CBSE pattern)
- ✅ MCQ auto-evaluation with instant results
- ✅ Teacher evaluation for handwritten answers (VSA/SA)
- ✅ SLA-based evaluation (same-day for Centum plan, 48hrs for others)
- ✅ Unit-wise performance analytics
- ✅ Leaderboard and rank tracking
- ✅ Predicted final board examination scores
- ✅ ML-ready architecture for future AI evaluation

---

## 📁 Project Structure

```
mathvidya/
├── backend/                # Python FastAPI backend
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   ├── dependencies/       # FastAPI dependencies (RBAC)
│   ├── tasks/              # Celery background tasks
│   ├── config/             # Configuration
│   ├── tests/              # Pytest tests
│   ├── alembic/            # Database migrations
│   ├── main.py             # FastAPI app entry point
│   ├── database.py         # Database connection
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React TypeScript frontend
│   └── src/
│       ├── app/            # Redux store
│       ├── features/       # Feature modules
│       ├── components/     # Reusable components
│       ├── api/            # API client
│       └── package.json    # Node dependencies
│
├── docs/                   # Documentation
│   ├── ENGINEERING-SPEC.md         # Complete technical specification
│   ├── FASTAPI-QUICKSTART.md       # Implementation guide
│   ├── TECH-STACK-COMPARISON.md    # Why FastAPI over Node.js
│   └── MIGRATION-SUMMARY.md        # Stack update summary
│
├── docker/                 # Docker configurations
├── scripts/                # Utility scripts
└── README.md               # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Create database
createdb mathvidya

# Run migrations (when implemented)
alembic upgrade head

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

**Access:**
- API Docs (Swagger): http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

**Access:**
- React App: http://localhost:3000

### Background Workers

```bash
cd backend

# Terminal 1: Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Terminal 2: Celery Beat (scheduler)
celery -A tasks.celery_app beat --loglevel=info

# Terminal 3: Flower (monitoring UI)
celery -A tasks.celery_app flower --port=5555
```

**Access:**
- Flower UI: http://localhost:5555

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[ENGINEERING-SPEC.md](docs/ENGINEERING-SPEC.md)** | Complete technical specification (56k words) |
| **[FASTAPI-QUICKSTART.md](docs/FASTAPI-QUICKSTART.md)** | Step-by-step implementation guide |
| **[TECH-STACK-COMPARISON.md](docs/TECH-STACK-COMPARISON.md)** | Technology stack decision rationale |
| **[CLAUDE.md](CLAUDE.md)** | Project overview for AI assistance |

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI 0.109
- **ORM:** SQLAlchemy 2.0 (async)
- **Database:** PostgreSQL 14+
- **Cache:** Redis 6+
- **Background Jobs:** Celery + Beat
- **Authentication:** JWT (python-jose)
- **Validation:** Pydantic v2

### Frontend
- **Framework:** React 18 + TypeScript
- **State Management:** Redux Toolkit + RTK Query
- **UI Library:** Material-UI (MUI)
- **Routing:** React Router v6
- **Forms:** React Hook Form + Zod
- **Math Rendering:** react-katex

### Infrastructure
- **Cloud:** AWS (ECS, RDS, ElastiCache, S3)
- **CI/CD:** GitHub Actions
- **Monitoring:** CloudWatch, Flower

---

## 🔐 Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mathvidya

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# AWS
AWS_REGION=ap-south-1
S3_BUCKET=mathvidya-production

# CORS
CORS_ORIGINS=http://localhost:3000
```

See `backend/.env.example` for complete list.

---

## 📝 Development Workflow

### 1. Create a New Feature

```bash
# Create git branch
git checkout -b feature/exam-generation

# Backend: Create model, schema, route
cd backend
touch models/exam.py schemas/exam.py routes/exams.py

# Frontend: Create feature module
cd frontend/src/features
mkdir exams
```

### 2. Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### 3. Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Add exams table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 📊 API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

### AWS ECS Deployment

See `docs/DEPLOYMENT.md` for detailed deployment guide.

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Ensure tests pass: `pytest` and `npm test`
5. Create pull request

---

## 📧 Support

For questions or issues:
- GitHub Issues: [Create an issue](https://github.com/yourorg/mathvidya/issues)
- Email: support@mathvidya.com

---

## 📄 License

Private - All Rights Reserved

---

## 🗺️ Roadmap

### V1 (Current - Months 1-3)
- ✅ Project setup and architecture
- 🔄 User authentication and RBAC
- 🔄 Exam generation and MCQ evaluation
- 🔄 Teacher evaluation interface
- 🔄 Analytics dashboard

### V2 (Months 4-6)
- 🔜 AI-assisted evaluation (handwriting recognition)
- 🔜 Mobile app (React Native)
- 🔜 Advanced analytics (ML predictions)
- 🔜 Payment gateway integration

### V3 (Months 7-12)
- 🔜 Classes IX and XI support
- 🔜 Long answer (LA) evaluation
- 🔜 School/Institute licensing
- 🔜 Multi-language support

---

**Built with ❤️ for CBSE students**
