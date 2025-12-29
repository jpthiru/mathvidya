# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mathvidya** is an online mathematics practice platform for CBSE students (Classes X and XII) in India. The platform combines flexible online exam practice with personalized evaluation by expert mathematics teachers.

**Core Value Proposition:** Students choose Mathvidya for board-exam-aligned practice with same-day or SLA-based evaluation by expert teachers, data-driven analytics, and predicted board examination scores.

## Architecture

### Logical Architecture (3-Tier Modular Design)

**Client Layer:**
- Web browser-based SPA (V1 scope)
- Role-specific UIs: Student, Parent (read-only), Teacher, Administrator
- Math notation rendering (LaTeX/MathML support required)
- Image upload/preview for scanned answer sheets

**API & Access Layer:**
- API Gateway with JWT/OAuth authentication
- Role-Based Access Control (RBAC) for 4 roles
- Subscription entitlement enforcement at API level
- SLA timer initiation on exam submission

**Core Application Services (9 modular services):**
1. **User & Profile Service** - Student/parent/teacher/admin management, parent-student mapping
2. **Subscription & Entitlement Service** - Plan validation, monthly exam counters, SLA priority
3. **Question Bank Service** - CRUD with versioning, unit-wise tagging, text+image support
4. **Exam Generation Service** - Config-driven templates, randomized selection, unique exam IDs
5. **Evaluation Service** - MCQ auto-evaluation, teacher annotation interface, score computation
6. **SLA & Workflow Manager** - Evaluation timers, priority queues, working-day calculations
7. **Analytics & Prediction Service** - Unit-wise analysis, performance trends, board score prediction
8. **Leaderboard Service** - Top 10 computation with eligibility enforcement
9. **Audit & Logging Service** - Cross-cutting immutable audit logs for all critical actions

**Data Layer:**
- PostgreSQL (transactional data, strong consistency)
- S3 (scanned answer sheets, question images)
- Redis (exam counters, SLA timers, session tokens)

### Physical Architecture (AWS India Region)

**Infrastructure Stack:**
- CloudFront CDN + WAF for edge security
- Application Load Balancer
- ECS (Fargate) or EKS for containerized services
- RDS PostgreSQL with Multi-AZ (implied)
- ElastiCache Redis for caching
- S3 with signed URLs for secure image access
- CloudWatch for observability
- All data hosted in AWS India region for compliance

## Key Design Principles

1. **Configuration over Code** - Exam templates fully configurable; CBSE pattern changes via config updates, not code changes
2. **Deterministic Scoring** - Transparent, auditable, reproducible scoring and ranking logic
3. **Human-in-the-Loop Evaluation** - Teachers central to VSA/SA evaluation (not automated in V1)
4. **API-First Architecture** - RESTful/GraphQL modular services, mobile-ready for future expansion
5. **Auditability by Default** - All evaluations, score changes, config changes logged immutably
6. **Single-Teacher Ownership** - One exam → one teacher; no re-evaluation or moderation in V1

## User Roles & Workflows

**Student:**
- Takes exams (MCQ answered on-screen, VSA/SA written on paper, scanned, uploaded)
- Reviews evaluated answers with explanations
- Accesses performance dashboard with unit-wise analysis and predicted board scores

**Parent/Guardian:**
- Read-only access to student performance, analytics, and subscription details
- Parent visibility is mandatory (child data protection)

**Teacher:**
- Evaluates scanned handwritten answers with image annotation tools (tick/cross stamps)
- Assigns marks based on CBSE marking scheme
- Adds questions to question bank
- No re-evaluation capability in V1

**Administrator:**
- Manages teachers, configuration parameters, question bank
- Views system-wide dashboards and SLA compliance

**System (Automated):**
- Generates exams dynamically from question bank
- Auto-evaluates MCQs
- Enforces subscription limits and SLA timers
- Calculates ranks and predictions

## Question Types & Exam Structure

**Supported Question Types (V1):**
- **MCQ** - Multiple Choice (1 mark, auto-evaluated)
- **VSA** - Very Short Answer (2 marks, teacher-evaluated)
- **SA** - Short Answer (3 marks, teacher-evaluated)

**Not in V1 (Future):** LA (Long Answer), Case Study questions

**Practice Modes:**
1. Full Board Examination (standard CBSE pattern, e.g., 38 questions, 80 marks for Class XII)
2. Section-wise practice (only MCQ / only VSA / only SA)
3. Unit-wise practice (based on CBSE unit weightage)

## Evaluation Workflows

**MCQ Evaluation (Automated):**
```
Student selects answers → Score = (Correct/Total) × 100 → Immediate results with explanations
```

**VSA/SA Evaluation (Human):**
```
Student uploads scanned pages → Exam enters "Pending Evaluation" → SLA Manager assigns to teacher → Teacher annotates images + assigns marks → Final score computed → Audit log written → Student/Parent notified
```

## SLA Rules

- **Centum Plan:** Same working day evaluation
- **All Other Plans:** Within 48 working hours
- Sundays and declared holidays excluded from calculation
- System-enforced with breach tracking
- Priority queue sorting based on SLA tier

## Subscription Plans

| Plan | Price | Exams/Month | Features | Leaderboard | SLA |
|------|-------|-------------|----------|-------------|-----|
| Basic | INR XXX/mo (annual) | 5 | Board Exam only, 1hr teacher interaction | No | 48hr |
| Premium MCQ | INR XXX/mo (annual) | 15 | MCQ only | No | 48hr |
| Premium | INR XXXX/mo | 50 | Board + Unit-wise, 1hr coaching/month | Yes | 48hr |
| Centum | INR XXXX/mo (annual) | 50 | Board + Unit-wise, direct teacher access | Yes | Same-day |

**Enforcement:** Monthly exam limits hard-enforced at exam start time; leaderboard eligibility checked at rendering time.

## Database Schema (Key Tables)

- **users** - students, parents, teachers, admins
- **parent_student_mapping** - enforces parent access
- **questions** - with versioning, unit tagging, text/image content
- **exam_templates** - configurable CBSE patterns
- **exam_instances** - unique IDs, immutable snapshots
- **student_answers** - MCQ selections + uploaded image references
- **teacher_evaluations** - marks, annotations, timestamps
- **subscriptions** - plans, limits, renewal dates
- **audit_logs** - immutable event log
- **analytics** - aggregated performance data
- **leaderboard** - computed read-optimized views

## Security & Compliance

- **RBAC enforcement at API level** for all 4 roles
- **Child data protection** - assume students are minors (<18)
- **Parent access mandatory** - no student-only accounts without parent visibility
- **Encryption:** At rest (KMS), in transit (TLS)
- **Signed URLs** for S3 access to answer sheets and question images
- **Audit logs immutable** with user attribution for all critical actions
- **Data residency:** AWS India region only

## ML-Readiness & Future Evolution Path

**V1:** Human teachers evaluate all VSA/SA; MCQ auto-evaluated

**Future phases:**
1. AI suggests marks to teachers (assistive mode)
2. AI flags inconsistencies or missing steps
3. Partial auto-evaluation for VSA/SA
4. Full auto-evaluation capability

**Design decisions supporting ML:**
- Original scanned images preserved immutably
- Question-to-answer mappings explicit
- Marks stored separately from explanations
- Teacher annotations as structured metadata
- Separation: Student answer → Teacher evaluation → Final score

## V1 Scope Constraints

**IN SCOPE:**
- Classes X and XII only
- Web platform only (no mobile apps)
- Question types: MCQ, VSA, SA
- Manual teacher evaluation for non-MCQ
- Individual student/parent subscriptions
- Same-day or 48-hour evaluation SLAs

**OUT OF SCOPE (but architecturally prepared for):**
- Classes IX and XI
- Mobile apps
- LA and Case Study questions
- AI-based handwritten evaluation
- Re-evaluation/moderation workflows
- School/institute licensing models

## Development Commands

### Local Development (Windows)

**Local Project Path:** `C:\Users\jpthi\work\ThiruAgenticAI\en9\mathvidya`

**Virtual Environment:** `backend\mvenv`

```bash
# Activate virtual environment
cd backend
.\mvenv\Scripts\activate

# Or run Python directly without activating
.\mvenv\Scripts\python -m uvicorn main:app --reload --port 8000

# Install dependencies (if needed)
.\mvenv\Scripts\pip install -r requirements.txt

# Database migrations
.\mvenv\Scripts\python -m alembic upgrade head

# Run tests
.\mvenv\Scripts\python -m pytest

# Batch import questions locally (dry run)
.\mvenv\Scripts\python scripts\batch_import_questions.py ..\Data-BatchUpload\MCQ-ClassXII-Batch1.xlsx --dry-run
```

### Production Deployment (EC2)

**EC2 Location:** `/opt/mathvidya`

**Production URL:** https://mathvidya.com

```bash
# SSH to EC2
ssh -i ~/.ssh/your-key.pem ubuntu@<EC2-IP>

# Navigate to project
cd /opt/mathvidya

# Pull latest code
git pull origin main

# Rebuild and restart containers
sudo docker-compose -f docker-compose.prod.yml build --no-cache backend
sudo docker-compose -f docker-compose.prod.yml up -d --force-recreate

# View logs
sudo docker-compose -f docker-compose.prod.yml logs -f backend

# Run database migrations in container
sudo docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# Batch import questions
sudo docker-compose -f docker-compose.prod.yml exec backend python scripts/batch_import_questions.py /app/Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx
```

### Docker Configuration

**Compose file:** `docker-compose.prod.yml`

Key services:
- `backend` - FastAPI application (port 8000)
- `postgres` - PostgreSQL database
- `redis` - Redis cache
- `nginx` - Reverse proxy (ports 80, 443)

### Batch Question Import

Excel format for batch import (`Data-BatchUpload/` folder):
- Columns: Class, Chapter/Unit, Question Type, Topic, Difficulty, Marks, Question Text in LaTeX, Option A-D text, Correct option and answer, Explanation or solution text in LaTeX, image
- All imported questions marked as `is_verified=false`
- Use Verify Questions page to review and approve

## Critical Technical Considerations

1. **Math Notation Rendering:** Frontend must support LaTeX/MathML for equations
2. **Large Image Handling:** Lazy loading for scanned answer sheets; assume low bandwidth (Indian network conditions)
3. **Upload Reliability:** Robust retry logic and progress indicators for image uploads
4. **SLA Calculations:** Working-day logic excluding Sundays and configurable holidays
5. **Deterministic Exam Generation:** Randomized but reproducible question selection with unit weightage
6. **Real-time Subscription Tracking:** Redis counters for monthly exam limits with atomic operations
7. **Scalable Teacher Assignment:** Queue-based distribution with SLA priority sorting

## API Design Expectations

- RESTful or GraphQL endpoints
- JWT/OAuth tokens for authentication
- RBAC middleware on all protected routes
- Subscription validation middleware
- Request/response logging for audit
- Rate limiting per role
- Standardized error responses
- API versioning for future compatibility

## State Management Patterns

- **Frontend:** Role-based UI rendering; client-side subscription state caching
- **Backend:** Stateless services; session state in Redis; transactional guarantees for exam submission and evaluation
- **Caching Strategy:** Session tokens, exam counters, leaderboard in Redis; CDN for static assets

## Documentation References

See `Documents/` folder for:
- `mathvidya-PRD.docx` - Product Requirements Document
- `Logical-Physical-Architecture.docx` - Detailed architecture diagrams
- `2Claude-optimised-engineering-prompt-byGhatGPT.docx` - Engineering prompt guidelines
- `Idea-And-prompt-for-PRD.docx` - Original project vision

## Working with This Codebase

When implementing features:

1. **Always check subscription entitlements** before allowing actions
2. **Write audit logs** for all evaluation actions, score changes, config updates
3. **Use configuration tables** instead of hardcoding exam structures
4. **Preserve immutability** of exam snapshots, student answers, and audit logs
5. **Enforce RBAC** at API layer, not just UI layer
6. **Validate parent-student mappings** before granting access
7. **Calculate SLA deadlines** using working-day logic (exclude Sundays + holidays)
8. **Generate unique exam IDs** with timestamp + randomness for traceability
9. **Store marks per question** separately for granular analytics
10. **Use signed URLs** for all S3 image access (answer sheets, question images)
