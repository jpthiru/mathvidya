# Mathvidya Engineering Specification

**Document Version:** 1.0
**Last Updated:** 2025-12-23
**Status:** V1 Implementation Design

This document provides complete implementation-level specifications for the Mathvidya platform, including architectural decisions, concrete schemas, API contracts, workflows, and trade-offs.

---

## Table of Contents

1. [Architectural Decisions](#1-architectural-decisions)
2. [Database Schema](#2-database-schema)
3. [API Contracts](#3-api-contracts)
4. [Key Workflows](#4-key-workflows)
5. [SLA Enforcement Logic](#5-sla-enforcement-logic)
6. [Security & RBAC Strategy](#6-security--rbac-strategy)
7. [Frontend Architecture](#7-frontend-architecture)
8. [ML-Readiness Design](#8-ml-readiness-design)
9. [Assumptions](#9-assumptions)
10. [Trade-offs](#10-trade-offs)

---

## 1. Architectural Decisions

### 1.1 Backend Technology Stack

**Decision:** Python FastAPI + SQLAlchemy (async) + PostgreSQL + Redis

**Rationale:**
- **FastAPI** provides excellent async I/O with automatic API documentation and validation
- **Pydantic** ensures type safety with runtime validation (types = validation)
- **PostgreSQL** offers strong ACID guarantees for transactional data (exam submissions, marks)
- **Redis** provides fast counters for subscription limits and SLA timers
- **Native ML integration** - TensorFlow, PyTorch, OpenCV in same codebase (critical for V2 AI features in 3 months)
- **Mathematical operations** - NumPy, Pandas for analytics and scoring algorithms
- **Single codebase** - API + ML together, no microservice complexity

**Why FastAPI over alternatives:**
- Faster development: 20% less code than Flask/Django
- Automatic OpenAPI/Swagger docs generation
- Built-in dependency injection for clean RBAC
- Performance: 1900+ req/sec (more than sufficient for 1000 concurrent users)
- Type safety: Pydantic models provide both validation and serialization

### 1.2 API Architecture

**Decision:** RESTful APIs with versioned endpoints (/api/v1/...)

**Rationale:**
- REST is simpler for mobile app integration (future)
- Clear HTTP semantics for CRUD operations
- Easier to cache with CloudFront

**Alternative Considered:** GraphQL
- Rejected for V1 due to complexity in RBAC enforcement and caching
- Can be added in V2 for complex analytics queries

### 1.3 Authentication & Session Management

**Decision:** JWT with refresh tokens stored in Redis

**Rationale:**
- JWTs are stateless and scale horizontally
- Short-lived access tokens (15 min) with long-lived refresh tokens (30 days)
- Redis stores refresh tokens for instant revocation capability

**Token Structure:**
```json
{
  "sub": "user_id",
  "role": "student|parent|teacher|admin",
  "subscription_plan": "basic|premium|premium_mcq|centum",
  "parent_id": "parent_user_id (for students)",
  "iat": 1234567890,
  "exp": 1234567890
}
```

### 1.4 File Storage Strategy

**Decision:** S3 with pre-signed URLs (15-minute expiry)

**Rationale:**
- Direct browser-to-S3 upload reduces backend load
- Pre-signed URLs provide time-limited access without exposing credentials
- S3 versioning enabled for answer sheet immutability

**Bucket Structure:**
```
mathvidya-production/
├── question-images/
│   └── {question_id}/{version}/{filename}
├── answer-sheets/
│   └── {exam_instance_id}/{student_id}/{page_number}.{jpg|pdf}
└── teacher-annotations/
    └── {evaluation_id}/{page_number}_annotated.jpg
```

### 1.5 Exam Generation Strategy

**Decision:** Pre-generated exam instances stored as immutable snapshots

**Rationale:**
- Questions can be edited/deleted after exam creation
- Student sees exact questions they were assigned
- Reproducible scoring even if question bank changes

**Snapshot Structure:** JSON blob containing full question content, not just IDs

### 1.6 Caching Strategy

**Decision:** Multi-layer caching

| Layer | Technology | Use Case | TTL |
|-------|------------|----------|-----|
| CDN | CloudFront | Static assets, question images | 1 year |
| Application | Redis | Leaderboard, subscription counters | 5 min - 1 hour |
| Database | PostgreSQL materialized views | Analytics aggregations | Refreshed nightly |

### 1.7 Background Job Processing

**Decision:** Celery (Redis-backed queue) for async tasks

**Use Cases:**
- SLA deadline calculations (triggered on exam submission)
- Leaderboard recomputation (triggered on evaluation completion)
- Analytics aggregation (scheduled nightly)
- Email/SMS notifications

**Queue Configuration:**
```python
# celery_config.py
from kombu import Queue, Exchange

task_queues = (
    Queue('evaluation', Exchange('evaluation'), routing_key='evaluation', priority=9),
    Queue('analytics', Exchange('analytics'), routing_key='analytics', priority=3),
    Queue('notifications', Exchange('notifications'), routing_key='notifications', priority=7),
)

task_routes = {
    'tasks.assign_evaluation': {'queue': 'evaluation', 'priority': 9},
    'tasks.refresh_leaderboard': {'queue': 'analytics', 'priority': 3},
    'tasks.send_notification': {'queue': 'notifications', 'priority': 7},
}
```

**Why Celery:**
- Most mature job queue for Python
- Advanced features: task chaining, workflows, retries, schedules
- Excellent monitoring (Flower UI)
- Celery Beat for cron-like scheduled tasks

### 1.8 Deployment Architecture

**Decision:** ECS Fargate with Application Load Balancer

```
CloudFront → ALB → ECS Fargate (3 services)
                    ├── api-service (2+ instances)
                    ├── evaluation-worker (2+ instances)
                    └── analytics-worker (1 instance)
```

**Rationale:**
- Fargate removes server management overhead
- Auto-scaling based on CPU/memory
- Separate evaluation workers prevent API slowdowns during peak evaluation times

---

## 2. Database Schema

### 2.1 Users Table

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'parent', 'teacher', 'admin')),

    -- Profile fields (all roles)
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),

    -- Student-specific fields
    student_class VARCHAR(10) CHECK (student_class IN ('X', 'XII', NULL)),
    student_photo_url TEXT,
    school_name VARCHAR(255),

    -- Status fields
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,

    -- Audit fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,

    CONSTRAINT student_fields_check
        CHECK (role != 'student' OR (student_class IS NOT NULL))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
```

### 2.2 Parent-Student Mapping

```sql
CREATE TABLE parent_student_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    student_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    relationship VARCHAR(50) NOT NULL, -- 'father', 'mother', 'guardian'
    is_primary BOOLEAN DEFAULT false, -- For billing purposes

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(parent_user_id, student_user_id),

    CONSTRAINT parent_role_check
        CHECK (parent_user_id IN (SELECT user_id FROM users WHERE role = 'parent')),
    CONSTRAINT student_role_check
        CHECK (student_user_id IN (SELECT user_id FROM users WHERE role = 'student'))
);

CREATE INDEX idx_parent_mappings_student ON parent_student_mappings(student_user_id);
CREATE INDEX idx_parent_mappings_parent ON parent_student_mappings(parent_user_id);
```

### 2.3 Subscriptions

```sql
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('basic', 'premium_mcq', 'premium', 'centum')),

    -- Subscription period
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    billing_cycle VARCHAR(20) CHECK (billing_cycle IN ('monthly', 'annual')),

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),

    -- Monthly counters (reset on billing date each month)
    exams_used_this_month INTEGER DEFAULT 0,
    exams_limit_per_month INTEGER NOT NULL,
    teacher_hours_used DECIMAL(5,2) DEFAULT 0,
    teacher_hours_limit DECIMAL(5,2),

    -- Billing reset date (day of month)
    billing_day_of_month INTEGER CHECK (billing_day_of_month BETWEEN 1 AND 28),
    last_counter_reset_date DATE,

    -- Payment
    amount_paid DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'INR',
    payment_gateway_ref VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT one_active_subscription
        UNIQUE(student_user_id, status)
        WHERE status = 'active'
);

CREATE INDEX idx_subscriptions_student ON subscriptions(student_user_id);
CREATE INDEX idx_subscriptions_active ON subscriptions(status) WHERE status = 'active';
```

### 2.4 Plan Configurations (Reference Data)

```sql
CREATE TABLE plan_configs (
    plan_type VARCHAR(20) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    exams_per_month INTEGER NOT NULL,
    teacher_hours_per_month DECIMAL(5,2),

    -- Allowed exam types
    allow_board_exam BOOLEAN DEFAULT true,
    allow_section_practice BOOLEAN DEFAULT true,
    allow_unit_practice BOOLEAN DEFAULT false,
    allow_mcq_only BOOLEAN DEFAULT true,

    -- Features
    leaderboard_eligible BOOLEAN DEFAULT false,
    sla_hours INTEGER NOT NULL, -- 24 for same-day, 48 for 2-day

    -- Pricing
    monthly_price DECIMAL(10,2),
    annual_price DECIMAL(10,2),

    is_active BOOLEAN DEFAULT true
);

-- Seed data
INSERT INTO plan_configs VALUES
('basic', 'Basic Plan', 5, 1.0, true, true, false, true, false, 48, 299, 2999, true),
('premium_mcq', 'Premium MCQ', 15, 0, true, true, false, true, false, 48, 499, 4999, true),
('premium', 'Premium Plan', 50, 1.0, true, true, true, true, true, 48, 999, 9999, true),
('centum', 'Plan Centum', 50, NULL, true, true, true, true, true, 24, 1499, 14999, true);
```

### 2.5 Questions Table

```sql
CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INTEGER DEFAULT 1,

    -- Classification
    class VARCHAR(10) NOT NULL CHECK (class IN ('X', 'XII')),
    unit VARCHAR(100) NOT NULL, -- 'Relations and Functions', 'Algebra', etc.
    topic VARCHAR(255),
    question_type VARCHAR(10) NOT NULL CHECK (question_type IN ('MCQ', 'VSA', 'SA', 'LA')),
    marks INTEGER NOT NULL,

    -- Question content (one of these must be non-null)
    question_text TEXT,
    question_image_url TEXT,
    diagram_image_url TEXT, -- Optional diagram accompanying text

    -- MCQ-specific fields (JSON for flexibility)
    mcq_choices JSONB, -- [{"label": "A", "text": "...", "image_url": "..."}, ...]
    mcq_correct_choices JSONB, -- ["A", "B"] for multi-correct

    -- Answer and explanation
    correct_answer_text TEXT,
    correct_answer_image_url TEXT,
    explanation TEXT,
    explanation_image_url TEXT,

    -- Metadata
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    cbse_year INTEGER, -- Which board exam year this appeared in

    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),

    -- Audit
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT question_content_check
        CHECK (question_text IS NOT NULL OR question_image_url IS NOT NULL),
    CONSTRAINT mcq_choices_check
        CHECK (question_type != 'MCQ' OR (mcq_choices IS NOT NULL AND mcq_correct_choices IS NOT NULL))
);

CREATE INDEX idx_questions_class_unit_type ON questions(class, unit, question_type);
CREATE INDEX idx_questions_status ON questions(status) WHERE status = 'active';
CREATE INDEX idx_questions_type ON questions(question_type);

-- MCQ choices JSON structure example:
-- [
--   {"label": "A", "text": "Option A text", "image_url": null},
--   {"label": "B", "text": "Option B text", "image_url": "https://..."},
--   {"label": "C", "text": null, "image_url": "https://..."},
--   {"label": "D", "text": "Option D text", "image_url": null}
-- ]
```

### 2.6 Exam Templates (Configuration)

```sql
CREATE TABLE exam_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) NOT NULL,
    class VARCHAR(10) NOT NULL CHECK (class IN ('X', 'XII')),
    exam_type VARCHAR(50) NOT NULL CHECK (exam_type IN ('board_exam', 'section_mcq', 'section_vsa', 'section_sa', 'unit_practice')),

    -- Template configuration (JSON for flexibility)
    config JSONB NOT NULL,
    /* Example config structure:
    {
      "total_marks": 80,
      "duration_minutes": 180,
      "sections": [
        {
          "section_name": "A",
          "question_type": "MCQ",
          "marks_per_question": 1,
          "question_count": 20,
          "unit_weightage": {
            "Relations and Functions": 0.15,
            "Algebra": 0.20,
            ...
          }
        },
        {
          "section_name": "B",
          "question_type": "VSA",
          "marks_per_question": 2,
          "question_count": 5,
          "unit_weightage": {...}
        }
      ]
    }
    */

    -- For unit-practice exams
    specific_unit VARCHAR(100), -- NULL for board exams, specific unit for unit practice

    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_class_type ON exam_templates(class, exam_type);
CREATE INDEX idx_templates_active ON exam_templates(is_active) WHERE is_active = true;
```

### 2.7 Exam Instances

```sql
CREATE TABLE exam_instances (
    exam_instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_user_id UUID NOT NULL REFERENCES users(user_id),
    template_id UUID NOT NULL REFERENCES exam_templates(template_id),

    -- Exam snapshot (immutable after creation)
    exam_snapshot JSONB NOT NULL,
    /* Snapshot structure:
    {
      "template_config": {...},
      "questions": [
        {
          "question_number": 1,
          "section": "A",
          "question_id": "uuid",
          "version": 1,
          "marks": 1,
          "question_content": {...full question JSON...}
        },
        ...
      ]
    }
    */

    -- Exam metadata
    exam_type VARCHAR(50) NOT NULL,
    class VARCHAR(10) NOT NULL,
    total_marks INTEGER NOT NULL,

    -- Timing
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    duration_minutes INTEGER,

    -- Status
    status VARCHAR(30) DEFAULT 'created' CHECK (status IN
        ('created', 'in_progress', 'submitted_mcq', 'pending_upload',
         'uploaded', 'pending_evaluation', 'evaluated')),

    -- Scores
    mcq_score DECIMAL(5,2),
    manual_score DECIMAL(5,2),
    total_score DECIMAL(5,2),
    percentage DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exam_instances_student ON exam_instances(student_user_id);
CREATE INDEX idx_exam_instances_status ON exam_instances(status);
CREATE INDEX idx_exam_instances_created ON exam_instances(created_at DESC);
```

### 2.8 Student Answers (MCQ)

```sql
CREATE TABLE student_mcq_answers (
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(exam_instance_id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,
    question_id UUID NOT NULL,

    -- Student's answer
    selected_choices JSONB NOT NULL, -- ["A"] or ["A", "C"] for multi-select

    -- Evaluation (computed immediately)
    is_correct BOOLEAN NOT NULL,
    marks_awarded DECIMAL(5,2) NOT NULL,
    marks_possible DECIMAL(5,2) NOT NULL,

    answered_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(exam_instance_id, question_number)
);

CREATE INDEX idx_mcq_answers_exam ON student_mcq_answers(exam_instance_id);
```

### 2.9 Answer Sheet Uploads

```sql
CREATE TABLE answer_sheet_uploads (
    upload_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(exam_instance_id) ON DELETE CASCADE,
    student_user_id UUID NOT NULL REFERENCES users(user_id),

    -- Upload details
    page_number INTEGER NOT NULL,
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- Question mapping (which questions are on this page)
    questions_on_page JSONB, -- [1, 2, 3] for questions 1-3

    uploaded_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(exam_instance_id, page_number)
);

CREATE INDEX idx_uploads_exam ON answer_sheet_uploads(exam_instance_id);
```

### 2.10 Unanswered Questions

```sql
CREATE TABLE unanswered_questions (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(exam_instance_id) ON DELETE CASCADE,
    question_number INTEGER NOT NULL,

    -- Student declares this was not attempted
    declared_unanswered BOOLEAN DEFAULT true,

    declared_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(exam_instance_id, question_number)
);
```

### 2.11 Evaluations

```sql
CREATE TABLE evaluations (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(exam_instance_id),
    teacher_user_id UUID NOT NULL REFERENCES users(user_id),

    -- SLA tracking
    assigned_at TIMESTAMP DEFAULT NOW(),
    sla_deadline TIMESTAMP NOT NULL,
    sla_breached BOOLEAN DEFAULT false,

    -- Evaluation status
    status VARCHAR(30) DEFAULT 'assigned' CHECK (status IN
        ('assigned', 'in_progress', 'completed')),

    -- Completion
    completed_at TIMESTAMP,
    total_manual_marks DECIMAL(5,2),

    -- Annotations (references to S3 annotated images)
    annotation_data JSONB,
    /* Structure:
    {
      "pages": [
        {
          "page_number": 1,
          "annotated_image_url": "https://...",
          "annotations": [
            {"type": "stamp", "x": 100, "y": 200, "stamp": "tick"},
            {"type": "stamp", "x": 150, "y": 300, "stamp": "cross"}
          ]
        }
      ]
    }
    */

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT one_evaluation_per_exam UNIQUE(exam_instance_id)
);

CREATE INDEX idx_evaluations_teacher ON evaluations(teacher_user_id);
CREATE INDEX idx_evaluations_status ON evaluations(status);
CREATE INDEX idx_evaluations_sla ON evaluations(sla_deadline) WHERE status != 'completed';
```

### 2.12 Question-wise Marks

```sql
CREATE TABLE question_marks (
    mark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(evaluation_id) ON DELETE CASCADE,
    exam_instance_id UUID NOT NULL REFERENCES exam_instances(exam_instance_id),

    question_number INTEGER NOT NULL,
    question_type VARCHAR(10) NOT NULL,

    -- Marks
    marks_awarded DECIMAL(5,2) NOT NULL,
    marks_possible DECIMAL(5,2) NOT NULL,

    -- Teacher notes (optional)
    teacher_comment TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(evaluation_id, question_number)
);

CREATE INDEX idx_question_marks_evaluation ON question_marks(evaluation_id);
CREATE INDEX idx_question_marks_exam ON question_marks(exam_instance_id);
```

### 2.13 Leaderboard (Materialized View)

```sql
CREATE MATERIALIZED VIEW leaderboard AS
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    u.student_photo_url,
    u.student_class,
    COUNT(ei.exam_instance_id) as total_exams,
    AVG(ei.percentage) as avg_percentage,
    SUM(ei.total_score) as total_marks,
    RANK() OVER (PARTITION BY u.student_class ORDER BY AVG(ei.percentage) DESC) as class_rank
FROM users u
JOIN exam_instances ei ON ei.student_user_id = u.user_id
JOIN subscriptions s ON s.student_user_id = u.user_id
JOIN plan_configs pc ON pc.plan_type = s.plan_type
WHERE
    u.role = 'student'
    AND ei.status = 'evaluated'
    AND s.status = 'active'
    AND pc.leaderboard_eligible = true
GROUP BY u.user_id, u.first_name, u.last_name, u.student_photo_url, u.student_class;

CREATE UNIQUE INDEX idx_leaderboard_user ON leaderboard(user_id);
CREATE INDEX idx_leaderboard_class_rank ON leaderboard(student_class, class_rank);

-- Refresh trigger (refresh after each evaluation completion)
CREATE OR REPLACE FUNCTION refresh_leaderboard()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_leaderboard
AFTER UPDATE OF status ON exam_instances
FOR EACH ROW
WHEN (NEW.status = 'evaluated')
EXECUTE FUNCTION refresh_leaderboard();
```

### 2.14 Analytics (Materialized View)

```sql
CREATE MATERIALIZED VIEW student_analytics AS
SELECT
    ei.student_user_id,
    u.student_class,

    -- Overall performance
    COUNT(ei.exam_instance_id) as total_exams,
    AVG(ei.percentage) as avg_percentage,
    MAX(ei.percentage) as best_percentage,
    MIN(ei.percentage) as worst_percentage,

    -- Unit-wise performance (extracted from exam snapshots)
    jsonb_object_agg(
        unit_stats.unit,
        jsonb_build_object(
            'avg_percentage', unit_stats.avg_percentage,
            'exams_count', unit_stats.exams_count
        )
    ) as unit_performance,

    -- Predicted board score (simple rule-based for V1)
    CASE
        WHEN AVG(ei.percentage) >= 95 THEN 98
        WHEN AVG(ei.percentage) >= 85 THEN 92
        WHEN AVG(ei.percentage) >= 75 THEN 82
        WHEN AVG(ei.percentage) >= 60 THEN 70
        ELSE AVG(ei.percentage)
    END as predicted_board_score,

    MAX(ei.updated_at) as last_exam_date
FROM exam_instances ei
JOIN users u ON u.user_id = ei.student_user_id
LEFT JOIN LATERAL (
    -- Extract unit-wise performance from exam snapshots
    SELECT
        question_data->>'unit' as unit,
        AVG((marks_data.marks_awarded / marks_data.marks_possible) * 100) as avg_percentage,
        COUNT(*) as exams_count
    FROM exam_instances ei2
    CROSS JOIN LATERAL jsonb_array_elements(ei2.exam_snapshot->'questions') as question_data
    LEFT JOIN question_marks marks_data ON
        marks_data.exam_instance_id = ei2.exam_instance_id
        AND marks_data.question_number = (question_data->>'question_number')::INTEGER
    WHERE ei2.student_user_id = ei.student_user_id
    GROUP BY question_data->>'unit'
) unit_stats ON true
WHERE ei.status = 'evaluated'
GROUP BY ei.student_user_id, u.student_class;

CREATE UNIQUE INDEX idx_analytics_student ON student_analytics(student_user_id);

-- Refresh nightly
```

### 2.15 Audit Logs

```sql
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    /* Event types:
       - 'evaluation.assigned'
       - 'evaluation.started'
       - 'evaluation.completed'
       - 'score.updated'
       - 'config.template_updated'
       - 'config.plan_updated'
       - 'user.login'
       - 'user.role_changed'
       - 'exam.started'
       - 'exam.submitted'
    */

    -- Who did it
    actor_user_id UUID REFERENCES users(user_id),
    actor_role VARCHAR(20),
    actor_ip VARCHAR(45),

    -- What was affected
    resource_type VARCHAR(50), -- 'exam', 'evaluation', 'user', 'config'
    resource_id UUID,

    -- Details (JSON for flexibility)
    event_data JSONB,
    /* Example for evaluation.completed:
    {
      "exam_instance_id": "uuid",
      "teacher_id": "uuid",
      "total_marks": 75.5,
      "sla_breached": false,
      "completion_time_hours": 22.5
    }
    */

    -- When
    created_at TIMESTAMP DEFAULT NOW(),

    -- Immutability enforcement (no UPDATE/DELETE allowed via triggers)
    CONSTRAINT immutable_log CHECK (created_at IS NOT NULL)
);

CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_actor ON audit_logs(actor_user_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);

-- Prevent updates and deletes
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER prevent_audit_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
```

### 2.16 System Configuration

```sql
CREATE TABLE system_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value JSONB NOT NULL,
    description TEXT,

    updated_by UUID REFERENCES users(user_id),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Seed data
INSERT INTO system_config VALUES
('holidays', '["2025-01-26", "2025-08-15", "2025-10-02"]'::jsonb, 'List of holidays (YYYY-MM-DD) excluded from SLA calculations', NULL, NOW()),
('sla_working_hours', '{"start": "09:00", "end": "18:00"}'::jsonb, 'Working hours for SLA calculations', NULL, NOW()),
('leaderboard_top_n', '10'::jsonb, 'Number of students shown on leaderboard', NULL, NOW()),
('evaluation_ui_config', '{"marks_panel_position": "right"}'::jsonb, 'Teacher evaluation UI preferences', NULL, NOW());
```

---

## 3. API Contracts

### 3.1 Authentication APIs

#### POST /api/v1/auth/register
**Description:** Register new user (student or parent)

**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!",
  "role": "student",
  "first_name": "Rahul",
  "last_name": "Sharma",
  "phone": "+919876543210",
  "student_class": "XII",
  "school_name": "Delhi Public School"
}
```

**Response:** 201 Created
```json
{
  "user_id": "uuid",
  "email": "student@example.com",
  "role": "student",
  "email_verified": false,
  "message": "Registration successful. Please verify email."
}
```

**Error:** 400 Bad Request
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Email already registered",
  "field": "email"
}
```

#### POST /api/v1/auth/login
**Request:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "user": {
    "user_id": "uuid",
    "email": "student@example.com",
    "role": "student",
    "first_name": "Rahul",
    "subscription_plan": "premium"
  }
}
```

#### POST /api/v1/auth/refresh
**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

### 3.2 Subscription APIs

#### GET /api/v1/subscriptions/me
**Headers:** `Authorization: Bearer <token>`
**Description:** Get current user's subscription details

**Response:** 200 OK
```json
{
  "subscription_id": "uuid",
  "plan_type": "premium",
  "plan_name": "Premium Plan",
  "status": "active",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "billing_cycle": "annual",
  "exams_used_this_month": 12,
  "exams_limit_per_month": 50,
  "exams_remaining": 38,
  "teacher_hours_used": 0.5,
  "teacher_hours_limit": 1.0,
  "leaderboard_eligible": true,
  "sla_hours": 48,
  "next_billing_date": "2025-02-01"
}
```

#### POST /api/v1/subscriptions
**Description:** Create new subscription (payment integration)

**Request:**
```json
{
  "plan_type": "premium",
  "billing_cycle": "annual",
  "payment_method": "razorpay",
  "payment_token": "pay_xyz123"
}
```

**Response:** 201 Created
```json
{
  "subscription_id": "uuid",
  "plan_type": "premium",
  "status": "active",
  "start_date": "2025-01-15",
  "end_date": "2026-01-15",
  "amount_paid": 9999.00,
  "currency": "INR",
  "payment_gateway_ref": "pay_xyz123"
}
```

### 3.3 Exam APIs

#### GET /api/v1/exams/templates
**Description:** List available exam templates for current user's class

**Query Params:**
- `class`: X or XII (defaults to user's class)
- `exam_type`: board_exam | section_mcq | section_vsa | section_sa | unit_practice

**Response:** 200 OK
```json
{
  "templates": [
    {
      "template_id": "uuid",
      "template_name": "Class XII Board Exam Pattern",
      "class": "XII",
      "exam_type": "board_exam",
      "total_marks": 80,
      "duration_minutes": 180,
      "sections": [
        {
          "section_name": "A",
          "question_type": "MCQ",
          "question_count": 20,
          "marks_per_question": 1
        },
        {
          "section_name": "B",
          "question_type": "VSA",
          "question_count": 5,
          "marks_per_question": 2
        }
      ]
    }
  ]
}
```

#### POST /api/v1/exams/start
**Description:** Start a new exam (generates questions, decrements counter)

**Request:**
```json
{
  "template_id": "uuid"
}
```

**Response:** 201 Created
```json
{
  "exam_instance_id": "uuid",
  "template_name": "Class XII Board Exam",
  "total_marks": 80,
  "duration_minutes": 180,
  "started_at": "2025-01-15T10:00:00Z",
  "status": "in_progress",
  "questions": [
    {
      "question_number": 1,
      "section": "A",
      "marks": 1,
      "question_type": "MCQ",
      "question_text": "If f(x) = x^2 + 2x + 1, what is f'(x)?",
      "mcq_choices": [
        {"label": "A", "text": "2x + 1"},
        {"label": "B", "text": "2x + 2"},
        {"label": "C", "text": "x + 1"},
        {"label": "D", "text": "2x"}
      ]
    }
  ]
}
```

**Error:** 403 Forbidden
```json
{
  "error": "SUBSCRIPTION_LIMIT_EXCEEDED",
  "message": "You have used all 50 exams for this month",
  "exams_used": 50,
  "exams_limit": 50,
  "reset_date": "2025-02-01"
}
```

#### POST /api/v1/exams/{exam_instance_id}/submit-mcq
**Description:** Submit MCQ answers

**Request:**
```json
{
  "answers": [
    {
      "question_number": 1,
      "selected_choices": ["B"]
    },
    {
      "question_number": 2,
      "selected_choices": ["A", "C"]
    }
  ]
}
```

**Response:** 200 OK
```json
{
  "exam_instance_id": "uuid",
  "status": "submitted_mcq",
  "mcq_score": 18.0,
  "mcq_total": 20.0,
  "mcq_percentage": 90.0,
  "results": [
    {
      "question_number": 1,
      "is_correct": true,
      "marks_awarded": 1.0,
      "selected_choices": ["B"],
      "correct_choices": ["B"],
      "explanation": "f'(x) = 2x + 2 by power rule"
    },
    {
      "question_number": 2,
      "is_correct": false,
      "marks_awarded": 0.0,
      "selected_choices": ["A", "C"],
      "correct_choices": ["A", "B"],
      "explanation": "..."
    }
  ],
  "next_step": "upload_answer_sheets"
}
```

#### GET /api/v1/exams/{exam_instance_id}/upload-urls
**Description:** Get pre-signed URLs for uploading answer sheets

**Query Params:**
- `page_count`: Number of pages to upload (e.g., 3)

**Response:** 200 OK
```json
{
  "upload_urls": [
    {
      "page_number": 1,
      "upload_url": "https://s3.amazonaws.com/mathvidya-prod/answer-sheets/...?X-Amz-Signature=...",
      "expires_in": 900
    },
    {
      "page_number": 2,
      "upload_url": "https://s3.amazonaws.com/...",
      "expires_in": 900
    }
  ],
  "instructions": "Upload images in JPG or PDF format, max 5MB per page"
}
```

#### POST /api/v1/exams/{exam_instance_id}/confirm-upload
**Description:** Confirm all answer sheets uploaded

**Request:**
```json
{
  "pages_uploaded": [1, 2, 3],
  "unanswered_questions": [15, 16],
  "page_question_mapping": {
    "1": [1, 2, 3, 4, 5],
    "2": [6, 7, 8, 9, 10],
    "3": [11, 12, 13, 14]
  }
}
```

**Response:** 200 OK
```json
{
  "exam_instance_id": "uuid",
  "status": "pending_evaluation",
  "submitted_at": "2025-01-15T12:30:00Z",
  "sla_deadline": "2025-01-17T18:00:00Z",
  "estimated_evaluation_by": "Within 48 working hours",
  "message": "Your answer sheets have been submitted for evaluation"
}
```

#### GET /api/v1/exams/{exam_instance_id}/results
**Description:** Get exam results (only after evaluation completed)

**Response:** 200 OK
```json
{
  "exam_instance_id": "uuid",
  "status": "evaluated",
  "submitted_at": "2025-01-15T12:30:00Z",
  "evaluated_at": "2025-01-16T14:00:00Z",
  "mcq_score": 18.0,
  "manual_score": 42.5,
  "total_score": 60.5,
  "total_marks": 80.0,
  "percentage": 75.63,
  "class_rank": 45,
  "question_wise_results": [
    {
      "question_number": 1,
      "question_type": "MCQ",
      "marks_awarded": 1.0,
      "marks_possible": 1.0,
      "is_correct": true
    },
    {
      "question_number": 21,
      "question_type": "VSA",
      "marks_awarded": 1.5,
      "marks_possible": 2.0,
      "teacher_comment": "Correct method but calculation error"
    }
  ],
  "annotated_pages": [
    {
      "page_number": 1,
      "original_url": "https://...",
      "annotated_url": "https://..."
    }
  ]
}
```

### 3.4 Evaluation APIs (Teacher)

#### GET /api/v1/evaluations/queue
**Description:** Get teacher's evaluation queue sorted by SLA

**Headers:** `Authorization: Bearer <teacher_token>`

**Query Params:**
- `status`: assigned | in_progress | completed
- `limit`: Number of items (default 20)
- `offset`: Pagination offset

**Response:** 200 OK
```json
{
  "queue": [
    {
      "evaluation_id": "uuid",
      "exam_instance_id": "uuid",
      "student_name": "Rahul Sharma",
      "student_class": "XII",
      "assigned_at": "2025-01-15T12:30:00Z",
      "sla_deadline": "2025-01-16T18:00:00Z",
      "hours_until_deadline": 5.5,
      "status": "assigned",
      "exam_type": "board_exam",
      "total_manual_questions": 18,
      "plan_type": "centum"
    }
  ],
  "total_count": 45,
  "offset": 0,
  "limit": 20
}
```

#### GET /api/v1/evaluations/{evaluation_id}/details
**Description:** Get full evaluation details for marking

**Response:** 200 OK
```json
{
  "evaluation_id": "uuid",
  "exam_instance_id": "uuid",
  "student_user_id": "uuid",
  "student_name": "Rahul Sharma",
  "student_class": "XII",
  "questions": [
    {
      "question_number": 21,
      "question_type": "VSA",
      "marks_possible": 2.0,
      "question_text": "Solve the equation...",
      "correct_answer_text": "x = 5",
      "explanation": "..."
    }
  ],
  "answer_sheets": [
    {
      "page_number": 1,
      "s3_url": "https://...",
      "presigned_url": "https://...",
      "questions_on_page": [21, 22, 23, 24, 25]
    }
  ],
  "unanswered_questions": [30],
  "sla_deadline": "2025-01-16T18:00:00Z"
}
```

#### POST /api/v1/evaluations/{evaluation_id}/annotations
**Description:** Save image annotations (intermediate save)

**Request:**
```json
{
  "page_number": 1,
  "annotations": [
    {
      "type": "stamp",
      "x": 150,
      "y": 200,
      "stamp": "tick"
    },
    {
      "type": "stamp",
      "x": 150,
      "y": 400,
      "stamp": "cross"
    }
  ]
}
```

**Response:** 200 OK
```json
{
  "message": "Annotations saved",
  "annotated_image_url": "https://..."
}
```

#### POST /api/v1/evaluations/{evaluation_id}/submit
**Description:** Submit final evaluation with marks

**Request:**
```json
{
  "question_marks": [
    {
      "question_number": 21,
      "marks_awarded": 2.0,
      "teacher_comment": "Correct"
    },
    {
      "question_number": 22,
      "marks_awarded": 1.5,
      "teacher_comment": "Correct method, minor error"
    },
    {
      "question_number": 30,
      "marks_awarded": 0.0,
      "teacher_comment": "Not attempted"
    }
  ]
}
```

**Response:** 200 OK
```json
{
  "evaluation_id": "uuid",
  "exam_instance_id": "uuid",
  "status": "completed",
  "total_manual_marks": 42.5,
  "total_exam_score": 60.5,
  "percentage": 75.63,
  "sla_breached": false,
  "completed_at": "2025-01-16T14:00:00Z",
  "message": "Evaluation submitted successfully"
}
```

### 3.5 Analytics APIs

#### GET /api/v1/analytics/dashboard
**Description:** Student dashboard data

**Headers:** `Authorization: Bearer <student_token>`

**Response:** 200 OK
```json
{
  "student_id": "uuid",
  "student_name": "Rahul Sharma",
  "class": "XII",
  "subscription": {
    "plan_type": "premium",
    "exams_used": 12,
    "exams_limit": 50,
    "exams_remaining": 38
  },
  "performance": {
    "total_exams": 12,
    "avg_percentage": 78.5,
    "best_percentage": 92.0,
    "worst_percentage": 65.0,
    "predicted_board_score": 82
  },
  "unit_performance": [
    {
      "unit": "Relations and Functions",
      "avg_percentage": 85.0,
      "exams_count": 3
    },
    {
      "unit": "Algebra",
      "avg_percentage": 72.0,
      "exams_count": 4
    }
  ],
  "rank": {
    "class_rank": 45,
    "total_students": 250,
    "leaderboard_eligible": true
  },
  "recent_exams": [
    {
      "exam_instance_id": "uuid",
      "exam_type": "board_exam",
      "taken_at": "2025-01-15T10:00:00Z",
      "score": 60.5,
      "percentage": 75.63,
      "status": "evaluated"
    }
  ]
}
```

#### GET /api/v1/analytics/parent-view/{student_id}
**Description:** Parent view of student performance

**Headers:** `Authorization: Bearer <parent_token>`

**Validation:** Verify parent-student mapping exists

**Response:** Same as student dashboard (read-only)

### 3.6 Leaderboard APIs

#### GET /api/v1/leaderboard
**Description:** Get top 10 students for user's class

**Headers:** `Authorization: Bearer <token>`

**Query Params:**
- `class`: X | XII (defaults to user's class)

**Response:** 200 OK
```json
{
  "class": "XII",
  "top_students": [
    {
      "rank": 1,
      "student_name": "Priya Singh",
      "photo_url": "https://...",
      "avg_percentage": 96.5,
      "total_exams": 25
    },
    {
      "rank": 2,
      "student_name": "Rahul Kumar",
      "photo_url": "https://...",
      "avg_percentage": 95.2,
      "total_exams": 22
    }
  ],
  "user_rank": 45,
  "user_eligible": true
}
```

**Error:** 403 Forbidden
```json
{
  "error": "LEADERBOARD_NOT_AVAILABLE",
  "message": "Leaderboard access requires Premium or Centum plan",
  "current_plan": "basic"
}
```

### 3.7 Admin APIs

#### POST /api/v1/admin/questions
**Description:** Create new question

**Headers:** `Authorization: Bearer <admin_or_teacher_token>`

**Request:**
```json
{
  "class": "XII",
  "unit": "Relations and Functions",
  "topic": "Functions",
  "question_type": "MCQ",
  "marks": 1,
  "question_text": "If f(x) = x^2, what is f(3)?",
  "mcq_choices": [
    {"label": "A", "text": "6"},
    {"label": "B", "text": "9"},
    {"label": "C", "text": "12"},
    {"label": "D", "text": "3"}
  ],
  "mcq_correct_choices": ["B"],
  "explanation": "f(3) = 3^2 = 9",
  "difficulty": "easy"
}
```

**Response:** 201 Created
```json
{
  "question_id": "uuid",
  "version": 1,
  "status": "active",
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### GET /api/v1/admin/reports/sla-compliance
**Description:** SLA compliance report

**Query Params:**
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response:** 200 OK
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  },
  "summary": {
    "total_evaluations": 450,
    "on_time": 430,
    "breached": 20,
    "compliance_rate": 95.6
  },
  "by_plan": [
    {
      "plan_type": "centum",
      "sla_hours": 24,
      "total": 100,
      "on_time": 98,
      "compliance_rate": 98.0
    },
    {
      "plan_type": "premium",
      "sla_hours": 48,
      "total": 350,
      "on_time": 332,
      "compliance_rate": 94.9
    }
  ]
}
```

---

## 4. Key Workflows

### 4.1 MCQ Exam Workflow

```
┌─────────────┐
│   Student   │
└──────┬──────┘
       │
       ├─► POST /api/v1/exams/start
       │   ├─ Check subscription limit
       │   ├─ Decrement monthly counter (Redis)
       │   ├─ Generate exam from template
       │   ├─ Select questions per unit weightage
       │   ├─ Create exam_instance with snapshot
       │   └─ Return questions
       │
       ├─► Student answers MCQs in browser
       │
       ├─► POST /api/v1/exams/{id}/submit-mcq
       │   ├─ Validate answers format
       │   ├─ Auto-evaluate each MCQ
       │   ├─ Store student_mcq_answers
       │   ├─ Compute MCQ score
       │   ├─ Update exam_instance.mcq_score
       │   ├─ Set status = 'submitted_mcq'
       │   └─ Return results with explanations
       │
       ├─► GET /api/v1/exams/{id}/results
       │   └─ Return detailed results
       │
       └─► Analytics updated (materialized view refresh)
```

### 4.2 VSA/SA Exam Workflow (Full Journey)

```
┌─────────────┐
│   Student   │
└──────┬──────┘
       │
       ├─► POST /api/v1/exams/start
       │   (Same as MCQ workflow)
       │
       ├─► POST /api/v1/exams/{id}/submit-mcq
       │   (Submit MCQ portion)
       │
       ├─► Student writes VSA/SA on paper
       │   Student scans pages using phone/scanner
       │
       ├─► GET /api/v1/exams/{id}/upload-urls?page_count=3
       │   ├─ Generate S3 pre-signed URLs
       │   └─ Return upload URLs (15-min expiry)
       │
       ├─► Student uploads directly to S3
       │   (Browser → S3, not via backend)
       │
       ├─► POST /api/v1/exams/{id}/confirm-upload
       │   ├─ Create answer_sheet_uploads records
       │   ├─ Mark unanswered questions
       │   ├─ Set status = 'pending_evaluation'
       │   ├─ Trigger SLA calculation job
       │   └─ Return SLA deadline
       │
┌──────────────────────────────────────────┐
│   Background Job: Assign Evaluation      │
└───────────────┬──────────────────────────┘
                │
                ├─► Calculate SLA deadline
                │   ├─ Get plan (centum = 24hr, others = 48hr)
                │   ├─ Exclude Sundays & holidays
                │   ├─ Calculate working hours only
                │   └─ Set sla_deadline timestamp
                │
                ├─► Assign to teacher
                │   ├─ Find teacher with lowest queue
                │   ├─ Create evaluation record
                │   ├─ Enqueue in evaluation-queue (Redis)
                │   └─ Notify teacher
                │
┌─────────────┐
│   Teacher   │
└──────┬──────┘
       │
       ├─► GET /api/v1/evaluations/queue
       │   └─ Return exams sorted by SLA deadline
       │
       ├─► GET /api/v1/evaluations/{id}/details
       │   ├─ Return answer sheet URLs
       │   ├─ Return questions with correct answers
       │   └─ Return pre-signed S3 URLs for images
       │
       ├─► Teacher views page 1
       │   Teacher adds tick/cross stamps
       │
       ├─► POST /api/v1/evaluations/{id}/annotations
       │   ├─ Save annotations to annotation_data JSON
       │   ├─ Generate annotated image (overlay stamps)
       │   ├─ Store in S3 teacher-annotations/
       │   └─ Return annotated image URL
       │
       ├─► Teacher repeats for all pages
       │   Teacher enters marks for each question
       │
       ├─► POST /api/v1/evaluations/{id}/submit
       │   ├─ Validate all questions marked
       │   ├─ Store question_marks records
       │   ├─ Compute total_manual_marks
       │   ├─ Update exam_instance.manual_score
       │   ├─ Compute exam_instance.total_score
       │   ├─ Set evaluation.status = 'completed'
       │   ├─ Set exam_instance.status = 'evaluated'
       │   ├─ Check if SLA breached
       │   ├─ Write audit_logs
       │   ├─ Trigger analytics refresh
       │   ├─ Trigger leaderboard refresh
       │   └─ Notify student & parent
       │
┌─────────────┐
│   Student   │
└──────┬──────┘
       │
       ├─► Receives notification
       │
       └─► GET /api/v1/exams/{id}/results
           ├─ Return MCQ + manual scores
           ├─ Return question-wise marks
           ├─ Return annotated answer sheets
           └─ Return teacher comments
```

### 4.3 Subscription Counter Reset Workflow

```
┌──────────────────────────────────────┐
│   Scheduled Job (runs daily 1 AM)   │
└───────────────┬──────────────────────┘
                │
                ├─► SELECT all active subscriptions
                │   WHERE billing_day_of_month = TODAY
                │
                ├─► For each subscription:
                │   ├─ UPDATE exams_used_this_month = 0
                │   ├─ UPDATE teacher_hours_used = 0
                │   ├─ UPDATE last_counter_reset_date = TODAY
                │   └─ DELETE Redis counter keys
                │
                └─► Write audit_logs for each reset
```

### 4.4 SLA Deadline Calculation Logic

**Inputs:**
- Exam submission timestamp
- Plan type (centum = 24hr, others = 48hr)
- Holidays list from system_config
- Working hours (9 AM - 6 PM)

**Algorithm:**
```python
def calculate_sla_deadline(submission_time, sla_hours, holidays):
    """
    Calculate SLA deadline excluding Sundays and holidays,
    counting only working hours (9 AM - 6 PM).
    """
    current = submission_time
    remaining_hours = sla_hours

    while remaining_hours > 0:
        # Move to next working hour
        current = next_working_hour(current)

        # Check if current day is Sunday or holiday
        if current.weekday() == 6 or current.date() in holidays:
            current = start_of_next_working_day(current)
            continue

        # Check if we're in working hours (9 AM - 6 PM)
        if current.hour < 9:
            current = current.replace(hour=9, minute=0)
        elif current.hour >= 18:
            current = start_of_next_working_day(current)
            continue

        # Consume one working hour
        remaining_hours -= 1
        current += timedelta(hours=1)

    return current
```

**Example:**
- Submission: Friday 5 PM
- SLA: 24 working hours (centum plan)
- Holidays: None

Calculation:
- Friday 5-6 PM: 1 hour (total: 1)
- Monday 9 AM - 6 PM: 9 hours (total: 10)
- Tuesday 9 AM - 6 PM: 9 hours (total: 19)
- Wednesday 9 AM - 2 PM: 5 hours (total: 24)
- **Deadline: Wednesday 2 PM**

---

## 5. SLA Enforcement Logic

### 5.1 SLA Configuration

```python
# config/sla.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class SLAConfig:
    hours: int
    description: str
    priority: int

SLA_CONFIG: Dict[str, SLAConfig] = {
    "centum": SLAConfig(
        hours=24,
        description="Same working day",
        priority=1  # Highest
    ),
    "premium": SLAConfig(
        hours=48,
        description="Within 2 working days",
        priority=2
    ),
    "premium_mcq": SLAConfig(
        hours=48,
        description="Within 2 working days",
        priority=3
    ),
    "basic": SLAConfig(
        hours=48,
        description="Within 2 working days",
        priority=4  # Lowest
    )
}
```

### 5.2 Evaluation Queue Management

**Redis Queue Structure:**
```
evaluation-queue:pending
├─ Sorted Set (score = SLA deadline timestamp)
├─ Member = evaluation_id
└─ Sorted by earliest deadline first

Example:
ZADD evaluation-queue:pending 1705492800 "eval-uuid-1"  // Deadline: Jan 17, 2PM
ZADD evaluation-queue:pending 1705579200 "eval-uuid-2"  // Deadline: Jan 18, 2PM
```

**Queue Operations:**
```python
# services/queue_service.py
from datetime import datetime
from typing import Optional
from redis import Redis

redis_client = Redis(host='localhost', port=6379, decode_responses=True)

async def add_to_evaluation_queue(evaluation_id: str, sla_deadline: datetime) -> None:
    """Add evaluation to priority queue sorted by SLA deadline"""
    deadline_timestamp = int(sla_deadline.timestamp())
    await redis_client.zadd('evaluation-queue:pending', {evaluation_id: deadline_timestamp})

async def get_next_evaluation(teacher_id: str) -> Optional[str]:
    """Get next evaluation for teacher (earliest deadline)"""
    # Get evaluation with earliest deadline
    results = await redis_client.zrange('evaluation-queue:pending', 0, 0)

    if not results:
        return None

    evaluation_id = results[0]

    # Assign to teacher and remove from queue (atomic operation)
    pipe = redis_client.pipeline()
    pipe.zrem('evaluation-queue:pending', evaluation_id)
    pipe.sadd(f'teacher:{teacher_id}:active', evaluation_id)
    await pipe.execute()

    return evaluation_id
```

### 5.3 SLA Breach Detection

**Scheduled Job (runs every 15 minutes via Celery Beat):**
```python
# tasks/sla_tasks.py
from celery import shared_task
from datetime import datetime
from sqlalchemy import update
from models import Evaluation
from services.audit_service import log_audit_event
from services.notification_service import notify_admin

@shared_task
async def detect_sla_breaches():
    """Detect and mark evaluations that have breached SLA"""
    now = int(datetime.now().timestamp())

    # Get all evaluations past deadline
    breached_evaluations = await redis_client.zrangebyscore(
        'evaluation-queue:pending',
        '-inf',
        now
    )

    for evaluation_id in breached_evaluations:
        async with get_session() as session:
            # Mark as breached in database
            await session.execute(
                update(Evaluation)
                .where(Evaluation.evaluation_id == evaluation_id)
                .values(sla_breached=True)
            )

            # Get evaluation details
            eval_data = await session.get(Evaluation, evaluation_id)

            # Log audit event
            await log_audit_event(
                event_type='sla.breached',
                resource_id=evaluation_id,
                event_data={
                    'breach_time': datetime.now().isoformat(),
                    'deadline_missed_by_minutes': calculate_delay(eval_data),
                    'teacher_id': str(eval_data.teacher_user_id)
                }
            )

            # Notify admin
            await notify_admin(
                notification_type='SLA_BREACH',
                evaluation_id=evaluation_id,
                teacher_id=eval_data.teacher_user_id
            )

            await session.commit()

# celerybeat_schedule.py (scheduled tasks)
from celery.schedules import crontab

beat_schedule = {
    'detect-sla-breaches': {
        'task': 'tasks.sla_tasks.detect_sla_breaches',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

### 5.4 Teacher Assignment Strategy

**Load Balancing Algorithm:**
```python
# services/teacher_assignment.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Evaluation
from config.sla import SLA_CONFIG
from services.queue_service import add_to_evaluation_queue
from services.notification_service import notify_teacher

async def assign_teacher_to_evaluation(
    evaluation_id: str,
    exam_instance_id: str,
    plan_type: str,
    session: AsyncSession
) -> None:
    """Assign teacher with lowest active workload to evaluation"""

    # Get all active teachers with their current workload
    subquery = (
        select(func.count())
        .select_from(Evaluation)
        .where(
            Evaluation.teacher_user_id == User.user_id,
            Evaluation.status.in_(['assigned', 'in_progress'])
        )
        .scalar_subquery()
    )

    query = (
        select(User, subquery.label('active_count'))
        .where(User.role == 'teacher', User.is_active == True)
        .order_by('active_count', func.random())
        .limit(1)
    )

    result = await session.execute(query)
    teacher = result.scalar_one()

    # Calculate SLA deadline
    sla_hours = SLA_CONFIG[plan_type].hours
    deadline = await calculate_sla_deadline(datetime.now(), sla_hours)

    # Create evaluation record
    new_evaluation = Evaluation(
        evaluation_id=evaluation_id,
        exam_instance_id=exam_instance_id,
        teacher_user_id=teacher.user_id,
        sla_deadline=deadline,
        status='assigned'
    )
    session.add(new_evaluation)
    await session.commit()

    # Add to queue
    await add_to_evaluation_queue(evaluation_id, deadline)

    # Notify teacher (async task)
    await notify_teacher(teacher.user_id, evaluation_id)
```

---

## 6. Security & RBAC Strategy

### 6.1 Role-Based Access Control Matrix

| Resource | Student | Parent | Teacher | Admin |
|----------|---------|--------|---------|-------|
| Start Exam | Own only | ❌ | ❌ | View all |
| View Exam Results | Own only | Child only | Assigned only | View all |
| Submit MCQ Answers | Own only | ❌ | ❌ | ❌ |
| Upload Answer Sheets | Own only | ❌ | ❌ | ❌ |
| View Evaluation Queue | ❌ | ❌ | Own queue | All queues |
| Submit Evaluation | ❌ | ❌ | Assigned only | ❌ |
| View Analytics | Own only | Child only | ❌ | All students |
| View Leaderboard | If eligible | If child eligible | ❌ | All |
| Manage Questions | ❌ | ❌ | Create/Edit | Full CRUD |
| Manage Users | ❌ | ❌ | ❌ | Full CRUD |
| View Audit Logs | ❌ | ❌ | ❌ | Read-only |

### 6.2 RBAC Middleware Implementation

**FastAPI Dependency Injection for RBAC:**

```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from typing import List
from models import User, ExamInstance, Evaluation, ParentStudentMapping
from database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Extract and validate user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker

async def verify_exam_ownership(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Verify user owns the exam or is admin"""
    if current_user.role == 'admin':
        return current_user

    result = await session.execute(
        select(ExamInstance).where(ExamInstance.exam_instance_id == exam_id)
    )
    exam = result.scalar_one_or_none()

    if not exam or exam.student_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )

    return current_user

async def verify_evaluation_ownership(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Verify teacher owns the evaluation or is admin"""
    if current_user.role == 'admin':
        return current_user

    result = await session.execute(
        select(Evaluation).where(Evaluation.evaluation_id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation or evaluation.teacher_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource"
        )

    return current_user

async def verify_parent_relationship(
    student_id: str,
    current_user: User = Depends(require_role('parent', 'admin')),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Verify parent has access to student data"""
    if current_user.role == 'admin':
        return current_user

    result = await session.execute(
        select(ParentStudentMapping).where(
            ParentStudentMapping.parent_user_id == current_user.user_id,
            ParentStudentMapping.student_user_id == student_id
        )
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this student's data"
        )

    return current_user
```

**Usage in FastAPI Routes:**

```python
# routes/exams.py
from fastapi import APIRouter, Depends
from dependencies.auth import require_role, verify_exam_ownership
from models import User

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

@router.get("/{exam_id}/results")
async def get_exam_results(
    exam_id: str,
    current_user: User = Depends(verify_exam_ownership),
    session: AsyncSession = Depends(get_session)
):
    """Get exam results (only owner, parent of owner, or admin)"""
    # current_user is already verified by dependency
    results = await fetch_exam_results(exam_id, session)
    return results

@router.post("/start")
async def start_exam(
    request: StartExamRequest,
    current_user: User = Depends(require_role('student')),
    session: AsyncSession = Depends(get_session)
):
    """Start new exam (students only)"""
    exam = await create_exam_instance(request, current_user.user_id, session)
    return exam

# routes/analytics.py
@router.get("/parent-view/{student_id}")
async def get_parent_view(
    student_id: str,
    current_user: User = Depends(verify_parent_relationship),
    session: AsyncSession = Depends(get_session)
):
    """Get student analytics for parent"""
    analytics = await get_student_analytics(student_id, session)
    return analytics
```

### 6.3 Data Protection Mechanisms

**1. S3 Pre-signed URLs (Time-limited Access)**
```python
# services/s3_service.py
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import ExamInstance

s3_client = boto3.client('s3', region_name='ap-south-1')

async def generate_answer_sheet_view_url(
    exam_instance_id: str,
    user_id: str,
    session: AsyncSession
) -> str:
    """Generate pre-signed URL for viewing answer sheet"""

    # Verify ownership
    result = await session.execute(
        select(ExamInstance).where(ExamInstance.exam_instance_id == exam_instance_id)
    )
    exam = result.scalar_one_or_none()

    if not exam or exam.student_user_id != user_id:
        raise PermissionError("Unauthorized access to answer sheet")

    # Generate 15-minute pre-signed URL
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'mathvidya-production',
                'Key': f'answer-sheets/{exam_instance_id}/page_1.jpg'
            },
            ExpiresIn=900  # 15 minutes
        )
        return url
    except ClientError as e:
        raise Exception(f"Failed to generate pre-signed URL: {str(e)}")

async def generate_upload_url(
    exam_instance_id: str,
    page_number: int,
    user_id: str
) -> str:
    """Generate pre-signed URL for uploading answer sheet"""

    # Generate upload URL (PUT)
    url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'mathvidya-production',
            'Key': f'answer-sheets/{exam_instance_id}/{user_id}/page_{page_number}.jpg',
            'ContentType': 'image/jpeg'
        },
        ExpiresIn=900  # 15 minutes
    )
    return url
```

**2. Row-Level Security (PostgreSQL)**
```sql
-- Enable RLS on sensitive tables
ALTER TABLE exam_instances ENABLE ROW LEVEL SECURITY;

-- Students can only see their own exams
CREATE POLICY student_own_exams ON exam_instances
FOR SELECT
TO student_role
USING (student_user_id = current_user_id());

-- Parents can see their children's exams
CREATE POLICY parent_child_exams ON exam_instances
FOR SELECT
TO parent_role
USING (
  student_user_id IN (
    SELECT student_user_id
    FROM parent_student_mappings
    WHERE parent_user_id = current_user_id()
  )
);

-- Teachers can only see assigned evaluations
CREATE POLICY teacher_assigned_exams ON exam_instances
FOR SELECT
TO teacher_role
USING (
  exam_instance_id IN (
    SELECT exam_instance_id
    FROM evaluations
    WHERE teacher_user_id = current_user_id()
  )
);
```

### 6.4 Input Validation & Sanitization

**Pydantic Models for Automatic Validation:**

```python
# schemas/exam_schemas.py
from pydantic import BaseModel, UUID4, Field, validator
from typing import List
import re

class StartExamRequest(BaseModel):
    template_id: UUID4

class MCQAnswer(BaseModel):
    question_number: int = Field(..., gt=0)
    selected_choices: List[str]

    @validator('selected_choices')
    def validate_choices(cls, v):
        """Validate choices are single uppercase letters"""
        for choice in v:
            if not re.match(r'^[A-Z]$', choice):
                raise ValueError('Choices must be single uppercase letters (A-Z)')
        if not v:
            raise ValueError('At least one choice must be selected')
        return v

class SubmitMCQRequest(BaseModel):
    answers: List[MCQAnswer] = Field(..., min_items=1)

class QuestionMark(BaseModel):
    question_number: int = Field(..., gt=0)
    marks_awarded: float = Field(..., ge=0, le=5)
    teacher_comment: str = Field(None, max_length=500)

class SubmitEvaluationRequest(BaseModel):
    question_marks: List[QuestionMark] = Field(..., min_items=1)

# Usage in FastAPI route - validation is automatic!
@router.post("/exams/start")
async def start_exam(
    request: StartExamRequest,  # Pydantic validates automatically
    current_user: User = Depends(require_role('student'))
):
    # If we reach here, request is already validated
    exam = await create_exam(request.template_id, current_user.user_id)
    return exam

# FastAPI automatically returns 422 Unprocessable Entity with validation errors
```

**Example Validation Error Response (automatic):**
```json
{
  "detail": [
    {
      "loc": ["body", "answers", 0, "selected_choices", 0],
      "msg": "Choices must be single uppercase letters (A-Z)",
      "type": "value_error"
    }
  ]
}
```

### 6.5 Rate Limiting

**Using slowapi (FastAPI rate limiting library):**

```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from redis import Redis

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)
redis_client = Redis(host='localhost', port=6379, decode_responses=True)

# Add to FastAPI app
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom rate limit per user role
async def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key based on user ID and role"""
    user = request.state.user  # Set by auth middleware
    return f"{user.user_id}:{user.role}"

# Usage in routes
@router.post("/exams/start")
@limiter.limit("10/hour", key_func=get_rate_limit_key)  # 10 exams per hour
async def start_exam(
    request: Request,
    exam_request: StartExamRequest,
    current_user: User = Depends(require_role('student'))
):
    exam = await create_exam_instance(exam_request, current_user.user_id)
    return exam

@router.post("/exams/{exam_id}/submit-mcq")
@limiter.limit("5/minute", key_func=get_rate_limit_key)  # 5 submissions per minute
async def submit_mcq_answers(
    request: Request,
    exam_id: str,
    answers: SubmitMCQRequest,
    current_user: User = Depends(verify_exam_ownership)
):
    result = await process_mcq_submission(exam_id, answers, current_user.user_id)
    return result

@router.post("/evaluations/{evaluation_id}/submit")
@limiter.limit("20/hour", key_func=get_rate_limit_key)  # 20 evaluations per hour
async def submit_evaluation(
    request: Request,
    evaluation_id: str,
    evaluation: SubmitEvaluationRequest,
    current_user: User = Depends(verify_evaluation_ownership)
):
    result = await process_evaluation(evaluation_id, evaluation)
    return result
```

**Rate Limit Error Response (automatic):**
```json
{
  "error": "Rate limit exceeded: 10 per 1 hour"
}
```

---

## 7. Frontend Architecture

### 7.1 Technology Stack Recommendation

**Framework:** React 18 with TypeScript
**State Management:** Redux Toolkit + RTK Query
**Routing:** React Router v6
**UI Library:** Material-UI (MUI) or Chakra UI
**Math Rendering:** react-katex or mathjax-react
**Form Handling:** React Hook Form + Zod validation
**File Upload:** react-dropzone
**Image Annotation:** Konva.js or Fabric.js (for teacher annotations)

### 7.2 Application Structure

```
src/
├── app/
│   ├── store.ts                 # Redux store configuration
│   └── api.ts                   # RTK Query API slice
├── features/
│   ├── auth/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   └── authSlice.ts
│   ├── exams/
│   │   ├── ExamList.tsx
│   │   ├── StartExam.tsx
│   │   ├── TakeExam.tsx
│   │   ├── UploadAnswers.tsx
│   │   ├── ExamResults.tsx
│   │   └── examsSlice.ts
│   ├── dashboard/
│   │   ├── StudentDashboard.tsx
│   │   ├── ParentDashboard.tsx
│   │   ├── TeacherDashboard.tsx
│   │   └── AdminDashboard.tsx
│   ├── evaluation/
│   │   ├── EvaluationQueue.tsx
│   │   ├── EvaluateExam.tsx
│   │   ├── ImageAnnotator.tsx
│   │   └── evaluationSlice.ts
│   ├── analytics/
│   │   ├── PerformanceCharts.tsx
│   │   ├── UnitAnalysis.tsx
│   │   └── PredictedScore.tsx
│   └── leaderboard/
│       └── Leaderboard.tsx
├── components/
│   ├── common/
│   │   ├── MathRenderer.tsx     # LaTeX/MathML renderer
│   │   ├── QuestionDisplay.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── LoadingSpinner.tsx
│   ├── exam/
│   │   ├── MCQQuestion.tsx
│   │   ├── Timer.tsx
│   │   └── ProgressBar.tsx
│   └── upload/
│       ├── ImageUploader.tsx
│       └── UploadProgress.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useSubscription.ts
│   └── useFileUpload.ts
├── utils/
│   ├── mathRenderer.ts
│   ├── s3Upload.ts
│   └── dateFormatter.ts
└── types/
    ├── exam.ts
    ├── user.ts
    └── api.ts
```

### 7.3 State Management Strategy

**Redux Slices:**
```typescript
// Auth Slice
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

// Exam Slice
interface ExamState {
  currentExam: ExamInstance | null;
  answers: { [questionNumber: number]: string[] };
  timeRemaining: number;
  currentQuestion: number;
}

// Subscription Slice
interface SubscriptionState {
  plan: SubscriptionDetails | null;
  examsRemaining: number;
  features: PlanFeatures;
}
```

**RTK Query API Endpoints:**
```typescript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.accessToken;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    }
  }),
  tagTypes: ['Exams', 'Evaluations', 'Analytics', 'Leaderboard'],
  endpoints: (builder) => ({
    startExam: builder.mutation<ExamInstance, { template_id: string }>({
      query: (body) => ({
        url: '/exams/start',
        method: 'POST',
        body
      }),
      invalidatesTags: ['Exams']
    }),

    getExamResults: builder.query<ExamResults, string>({
      query: (examId) => `/exams/${examId}/results`,
      providesTags: (result, error, examId) => [{ type: 'Exams', id: examId }]
    }),

    submitMCQAnswers: builder.mutation<any, { examId: string; answers: Answer[] }>({
      query: ({ examId, answers }) => ({
        url: `/exams/${examId}/submit-mcq`,
        method: 'POST',
        body: { answers }
      }),
      invalidatesTags: (result, error, { examId }) => [{ type: 'Exams', id: examId }]
    }),

    getEvaluationQueue: builder.query<EvaluationQueueResponse, void>({
      query: () => '/evaluations/queue',
      providesTags: ['Evaluations']
    }),

    getDashboard: builder.query<DashboardData, void>({
      query: () => '/analytics/dashboard',
      providesTags: ['Analytics']
    }),

    getLeaderboard: builder.query<LeaderboardData, { class: string }>({
      query: ({ class }) => `/leaderboard?class=${class}`,
      providesTags: ['Leaderboard']
    })
  })
});

export const {
  useStartExamMutation,
  useGetExamResultsQuery,
  useSubmitMCQAnswersMutation,
  useGetEvaluationQueueQuery,
  useGetDashboardQuery,
  useGetLeaderboardQuery
} = api;
```

### 7.4 Component Architecture Examples

**MCQ Question Component:**
```typescript
interface MCQQuestionProps {
  questionNumber: number;
  questionText: string;
  questionImageUrl?: string;
  choices: MCQChoice[];
  selectedChoices: string[];
  onAnswerChange: (choices: string[]) => void;
  multiSelect: boolean;
}

const MCQQuestion: React.FC<MCQQuestionProps> = ({
  questionNumber,
  questionText,
  questionImageUrl,
  choices,
  selectedChoices,
  onAnswerChange,
  multiSelect
}) => {
  const handleChoiceClick = (label: string) => {
    if (multiSelect) {
      const newSelection = selectedChoices.includes(label)
        ? selectedChoices.filter(c => c !== label)
        : [...selectedChoices, label];
      onAnswerChange(newSelection);
    } else {
      onAnswerChange([label]);
    }
  };

  return (
    <Box>
      <Typography variant="h6">Question {questionNumber}</Typography>

      {questionText && <MathRenderer content={questionText} />}
      {questionImageUrl && <img src={questionImageUrl} alt="Question" />}

      <FormControl component="fieldset">
        <RadioGroup value={selectedChoices[0] || ''}>
          {choices.map((choice) => (
            <FormControlLabel
              key={choice.label}
              value={choice.label}
              control={multiSelect ? <Checkbox /> : <Radio />}
              label={
                choice.text ? (
                  <MathRenderer content={choice.text} />
                ) : (
                  <img src={choice.image_url} alt={choice.label} />
                )
              }
              onChange={() => handleChoiceClick(choice.label)}
            />
          ))}
        </RadioGroup>
      </FormControl>
    </Box>
  );
};
```

**Image Annotator Component (for teachers):**
```typescript
import { Stage, Layer, Image as KonvaImage, Circle } from 'react-konva';

interface ImageAnnotatorProps {
  imageUrl: string;
  annotations: Annotation[];
  onAnnotationsChange: (annotations: Annotation[]) => void;
  readOnly?: boolean;
}

const ImageAnnotator: React.FC<ImageAnnotatorProps> = ({
  imageUrl,
  annotations,
  onAnnotationsChange,
  readOnly = false
}) => {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [selectedStamp, setSelectedStamp] = useState<'tick' | 'cross'>('tick');

  useEffect(() => {
    const img = new window.Image();
    img.src = imageUrl;
    img.onload = () => setImage(img);
  }, [imageUrl]);

  const handleStageClick = (e: any) => {
    if (readOnly) return;

    const stage = e.target.getStage();
    const point = stage.getPointerPosition();

    const newAnnotation: Annotation = {
      type: 'stamp',
      x: point.x,
      y: point.y,
      stamp: selectedStamp
    };

    onAnnotationsChange([...annotations, newAnnotation]);
  };

  return (
    <Box>
      <ButtonGroup>
        <Button
          variant={selectedStamp === 'tick' ? 'contained' : 'outlined'}
          onClick={() => setSelectedStamp('tick')}
        >
          ✓ Tick
        </Button>
        <Button
          variant={selectedStamp === 'cross' ? 'contained' : 'outlined'}
          onClick={() => setSelectedStamp('cross')}
        >
          ✗ Cross
        </Button>
      </ButtonGroup>

      <Stage width={800} height={1200} onClick={handleStageClick}>
        <Layer>
          {image && <KonvaImage image={image} />}

          {annotations.map((ann, idx) => (
            <Circle
              key={idx}
              x={ann.x}
              y={ann.y}
              radius={20}
              fill={ann.stamp === 'tick' ? 'green' : 'red'}
              opacity={0.6}
            />
          ))}
        </Layer>
      </Stage>
    </Box>
  );
};
```

**S3 Direct Upload Hook:**
```typescript
const useS3Upload = () => {
  const [uploadProgress, setUploadProgress] = useState<{ [page: number]: number }>({});
  const [errors, setErrors] = useState<{ [page: number]: string }>({});

  const uploadToS3 = async (presignedUrl: string, file: File, pageNumber: number) => {
    try {
      const response = await fetch(presignedUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type
        },
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(prev => ({ ...prev, [pageNumber]: percentCompleted }));
        }
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      setErrors(prev => ({ ...prev, [pageNumber]: error.message }));
      return false;
    }
  };

  return { uploadToS3, uploadProgress, errors };
};
```

### 7.5 Role-Based UI Rendering

```typescript
// ProtectedRoute component
interface ProtectedRouteProps {
  allowedRoles: string[];
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else if (!allowedRoles.includes(user.role)) {
      navigate('/unauthorized');
    }
  }, [isAuthenticated, user, allowedRoles, navigate]);

  if (!isAuthenticated || !allowedRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
};

// Route configuration
const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={['student', 'parent', 'teacher', 'admin']}>
          <DashboardRouter />
        </ProtectedRoute>
      } />

      <Route path="/exams/*" element={
        <ProtectedRoute allowedRoles={['student']}>
          <ExamsRouter />
        </ProtectedRoute>
      } />

      <Route path="/evaluations/*" element={
        <ProtectedRoute allowedRoles={['teacher']}>
          <EvaluationsRouter />
        </ProtectedRoute>
      } />

      <Route path="/admin/*" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <AdminRouter />
        </ProtectedRoute>
      } />
    </Routes>
  );
};

// Dashboard router based on role
const DashboardRouter = () => {
  const { user } = useAuth();

  switch (user.role) {
    case 'student':
      return <StudentDashboard />;
    case 'parent':
      return <ParentDashboard />;
    case 'teacher':
      return <TeacherDashboard />;
    case 'admin':
      return <AdminDashboard />;
    default:
      return <Navigate to="/login" />;
  }
};
```

---

## 8. ML-Readiness Design

### 8.1 ML Data Schema Extensions

**Training Dataset Table:**
```sql
CREATE TABLE ml_training_dataset (
    dataset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source exam data
    exam_instance_id UUID REFERENCES exam_instances(exam_instance_id),
    question_id UUID REFERENCES questions(question_id),
    question_number INTEGER,

    -- Student answer (raw)
    answer_image_s3_key TEXT NOT NULL,
    answer_image_hash VARCHAR(64), -- SHA-256 for deduplication

    -- Teacher evaluation (ground truth)
    marks_awarded DECIMAL(5,2),
    marks_possible DECIMAL(5,2),
    teacher_user_id UUID REFERENCES users(user_id),
    teacher_comment TEXT,

    -- Question metadata
    question_type VARCHAR(10),
    unit VARCHAR(100),
    topic VARCHAR(255),
    difficulty VARCHAR(20),

    -- Consent and privacy
    student_consent_ml BOOLEAN DEFAULT false,
    anonymization_applied BOOLEAN DEFAULT true,

    -- ML metadata
    included_in_training BOOLEAN DEFAULT false,
    training_split VARCHAR(20), -- 'train', 'validation', 'test'
    dataset_version VARCHAR(50),

    -- Quality flags
    is_clean_scan BOOLEAN, -- Manual QA flag
    has_ambiguous_handwriting BOOLEAN,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ml_dataset_question_type ON ml_training_dataset(question_type);
CREATE INDEX idx_ml_dataset_marks ON ml_training_dataset(marks_awarded, marks_possible);
CREATE INDEX idx_ml_dataset_consent ON ml_training_dataset(student_consent_ml) WHERE student_consent_ml = true;
```

**ML Model Predictions Table (future):**
```sql
CREATE TABLE ml_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Model metadata
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,

    -- Input
    exam_instance_id UUID REFERENCES exam_instances(exam_instance_id),
    question_number INTEGER,
    answer_image_s3_key TEXT,

    -- Prediction output
    predicted_marks DECIMAL(5,2),
    confidence_score DECIMAL(5,4), -- 0.0 to 1.0

    -- Detailed predictions (JSON)
    prediction_details JSONB,
    /* Example:
    {
      "step_detection": [
        {"step": "wrote_formula", "confidence": 0.95},
        {"step": "substituted_values", "confidence": 0.88},
        {"step": "calculated_result", "confidence": 0.92}
      ],
      "error_detection": [
        {"type": "calculation_error", "confidence": 0.65, "location": [x, y]}
      ],
      "partial_credit_breakdown": {
        "method": 1.0,
        "execution": 0.5,
        "final_answer": 0.0
      }
    }
    */

    -- Teacher override (if prediction used)
    teacher_accepted BOOLEAN,
    teacher_override_marks DECIMAL(5,2),

    -- Feedback loop
    prediction_error DECIMAL(5,2), -- abs(predicted - actual)

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ml_predictions_model ON ml_predictions(model_name, model_version);
CREATE INDEX idx_ml_predictions_exam ON ml_predictions(exam_instance_id);
```

### 8.2 ML Integration Points (Future)

**Phase 2: AI-Assisted Evaluation (Suggested Marks)**

```typescript
// API endpoint for AI suggestions (future)
app.get('/api/v1/evaluations/:id/ai-suggestions',
  authenticate(),
  requireRole('teacher'),
  async (req, res) => {
    const { id: evaluationId } = req.params;

    // Get evaluation details
    const evaluation = await getEvaluationDetails(evaluationId);

    // For each question with uploaded answer
    const suggestions = [];

    for (const question of evaluation.questions) {
      if (question.answer_image_url) {
        // Call ML service
        const prediction = await mlService.predictMarks({
          answer_image_url: question.answer_image_url,
          question_id: question.question_id,
          marks_possible: question.marks_possible,
          model_version: 'v2.1'
        });

        suggestions.push({
          question_number: question.question_number,
          suggested_marks: prediction.predicted_marks,
          confidence: prediction.confidence_score,
          explanation: prediction.prediction_details,
          show_warning: prediction.confidence_score < 0.7
        });
      }
    }

    res.json({ suggestions });
  }
);
```

**Teacher UI with AI Suggestions:**
```typescript
const EvaluateWithAI: React.FC<{ evaluationId: string }> = ({ evaluationId }) => {
  const { data: suggestions } = useGetAISuggestionsQuery(evaluationId);
  const [manualMarks, setManualMarks] = useState<{ [qNum: number]: number }>({});

  return (
    <Box>
      {suggestions?.map((suggestion) => (
        <Card key={suggestion.question_number}>
          <CardHeader title={`Question ${suggestion.question_number}`} />
          <CardContent>
            <Alert severity={suggestion.confidence > 0.7 ? 'info' : 'warning'}>
              AI Suggestion: {suggestion.suggested_marks} marks
              (Confidence: {(suggestion.confidence * 100).toFixed(1)}%)
            </Alert>

            <TextField
              label="Your Marks"
              type="number"
              value={manualMarks[suggestion.question_number] || suggestion.suggested_marks}
              onChange={(e) => setManualMarks({
                ...manualMarks,
                [suggestion.question_number]: parseFloat(e.target.value)
              })}
              helperText="You can accept, modify, or override the AI suggestion"
            />

            {suggestion.explanation && (
              <Accordion>
                <AccordionSummary>AI Reasoning</AccordionSummary>
                <AccordionDetails>
                  <pre>{JSON.stringify(suggestion.explanation, null, 2)}</pre>
                </AccordionDetails>
              </Accordion>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};
```

### 8.3 Data Collection Strategy for ML

**1. Student Consent Management:**
```sql
ALTER TABLE users ADD COLUMN ml_consent BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN ml_consent_date TIMESTAMP;

-- Update consent via API
POST /api/v1/users/me/ml-consent
{
  "consent": true
}
```

**2. Automated Dataset Builder (Nightly Job):**
```typescript
async function buildMLDataset() {
  // Get all evaluated exams with student consent
  const evaluations = await db.query(`
    SELECT
      ei.exam_instance_id,
      ei.student_user_id,
      q.question_id,
      q.question_type,
      q.unit,
      q.topic,
      q.difficulty,
      asu.s3_key as answer_image_s3_key,
      qm.marks_awarded,
      qm.marks_possible,
      qm.teacher_comment,
      e.teacher_user_id
    FROM exam_instances ei
    JOIN evaluations e ON e.exam_instance_id = ei.exam_instance_id
    JOIN answer_sheet_uploads asu ON asu.exam_instance_id = ei.exam_instance_id
    JOIN question_marks qm ON qm.exam_instance_id = ei.exam_instance_id
    JOIN questions q ON q.question_id = qm.question_id
    JOIN users u ON u.user_id = ei.student_user_id
    WHERE
      ei.status = 'evaluated'
      AND u.ml_consent = true
      AND qm.question_type IN ('VSA', 'SA')
      AND NOT EXISTS (
        SELECT 1 FROM ml_training_dataset
        WHERE exam_instance_id = ei.exam_instance_id
          AND question_number = qm.question_number
      )
  `);

  // Insert into training dataset
  for (const row of evaluations.rows) {
    await db.query(`
      INSERT INTO ml_training_dataset (
        exam_instance_id,
        question_id,
        question_number,
        answer_image_s3_key,
        marks_awarded,
        marks_possible,
        teacher_user_id,
        teacher_comment,
        question_type,
        unit,
        topic,
        difficulty,
        student_consent_ml,
        anonymization_applied
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, true, true)
    `, [
      row.exam_instance_id,
      row.question_id,
      row.question_number,
      row.answer_image_s3_key,
      row.marks_awarded,
      row.marks_possible,
      row.teacher_user_id,
      row.teacher_comment,
      row.question_type,
      row.unit,
      row.topic,
      row.difficulty
    ]);
  }

  console.log(`Added ${evaluations.rows.length} samples to ML dataset`);
}
```

**3. Dataset Versioning & Splits:**
```typescript
async function createDatasetVersion(versionName: string) {
  // Get all consented, clean data
  const allSamples = await db.query(`
    SELECT dataset_id
    FROM ml_training_dataset
    WHERE student_consent_ml = true
      AND is_clean_scan = true
    ORDER BY RANDOM()
  `);

  const total = allSamples.rows.length;
  const trainSize = Math.floor(total * 0.7);
  const valSize = Math.floor(total * 0.15);

  // Assign splits
  for (let i = 0; i < total; i++) {
    const split = i < trainSize ? 'train'
                : i < trainSize + valSize ? 'validation'
                : 'test';

    await db.query(`
      UPDATE ml_training_dataset
      SET
        training_split = $1,
        dataset_version = $2,
        included_in_training = true
      WHERE dataset_id = $3
    `, [split, versionName, allSamples.rows[i].dataset_id]);
  }

  console.log(`Created dataset version: ${versionName}`);
  console.log(`Train: ${trainSize}, Val: ${valSize}, Test: ${total - trainSize - valSize}`);
}
```

### 8.4 ML Model Deployment Architecture (Future)

```
┌──────────────────────────────────────────────────────────┐
│                    Mathvidya Backend                     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Evaluation Service (Node.js)              │ │
│  │                                                    │ │
│  │  ┌──────────────────────────────────────────┐    │ │
│  │  │  ML Integration Layer                    │    │ │
│  │  │  - Model version selection               │    │ │
│  │  │  - Fallback to human evaluation          │    │ │
│  │  │  - Confidence threshold checks            │    │ │
│  │  └──────────────────────────────────────────┘    │ │
│  │                        ▲                          │ │
│  │                        │ gRPC/REST                │ │
│  │                        ▼                          │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
                           │ API Gateway
                           ▼
┌──────────────────────────────────────────────────────────┐
│              ML Service (Separate Deployment)            │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │       Model Serving (TensorFlow Serving / FastAPI)│ │
│  │                                                    │ │
│  │  - Handwriting recognition model                  │ │
│  │  - Mathematical expression parser                 │ │
│  │  - Step detection model                           │ │
│  │  - Scoring model                                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │       Model Registry (MLflow / DVC)                │ │
│  │  - Version tracking                                │ │
│  │  - A/B testing support                             │ │
│  │  - Performance metrics                             │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 9. Assumptions

### 9.1 Technical Assumptions

1. **Internet Connectivity:** Students have reasonably stable internet (3G+) for exam-taking and uploads
2. **Device Capabilities:** Students have access to a smartphone or scanner for capturing answer sheets
3. **Image Quality:** Uploaded answer sheets are legible (minimum 300 DPI recommended)
4. **Browser Support:** Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
5. **AWS India Availability:** All required AWS services available in ap-south-1 region
6. **PostgreSQL Version:** PostgreSQL 14+ for advanced JSON functions and materialized views
7. **Redis Version:** Redis 6+ for sorted sets and atomic operations
8. **Peak Load:** Maximum 1000 concurrent exam takers, 100 concurrent evaluations
9. **Storage Growth:** ~2MB per exam (answer sheets + questions), ~50GB/year for 25,000 exams

### 9.2 Business Assumptions

1. **CBSE Pattern Stability:** Board exam patterns change infrequently (yearly at most)
2. **Teacher Availability:** Sufficient pool of qualified math teachers for 48-hour SLA
3. **Payment Gateway:** Razorpay or similar supports recurring billing for annual subscriptions
4. **Parent Registration:** Parents willing to create accounts for read-only access
5. **Student Age:** All students are minors (<18), requiring parental consent
6. **Leaderboard Participation:** Top-tier plan subscribers want public leaderboard visibility
7. **Evaluation Quality:** Single-teacher evaluation sufficient (no moderation needed in V1)
8. **Pricing Elasticity:** Students/parents willing to pay ₹999-₹1499/month for premium plans
9. **Market Size:** Minimum 10,000 active students in first year for business viability
10. **Churn Rate:** <20% monthly churn for subscription retention

### 9.3 User Behavior Assumptions

1. **Exam Frequency:** Average student takes 10-15 exams per month (well below 50 limit)
2. **Upload Reliability:** Students willing to retry uploads if initial attempt fails
3. **SLA Acceptance:** Students accept 24-48 hour wait for evaluations
4. **MCQ Honesty:** No strict proctoring needed (practice exams, not high-stakes)
5. **Answer Sheet Quality:** Students write clearly enough for teacher evaluation
6. **Parent Involvement:** Parents actively monitor student progress (not passive)
7. **Teacher Commitment:** Teachers complete evaluations within assigned SLA
8. **Device Usage:** 60% mobile, 40% desktop for exam-taking
9. **Time Commitment:** Students spend 2-3 hours per exam (taking + reviewing results)
10. **Feedback Loop:** Students review explanations and learn from mistakes

### 9.4 Data & Privacy Assumptions

1. **Student Consent:** Students/parents agree to store answer sheets for evaluation
2. **Data Retention:** Answer sheets retained indefinitely for ML training (with consent)
3. **Anonymization:** Removing student names/photos sufficient for ML dataset anonymization
4. **GDPR Compliance:** India-based users not subject to GDPR (domestic data only)
5. **Parent Rights:** Parents have full access to student data (no privacy from parents)
6. **Teacher Confidentiality:** Teachers do not share student answers externally
7. **Audit Retention:** Audit logs retained for 7 years (compliance requirement)
8. **Backup Frequency:** Daily database backups, 30-day retention for S3 objects

### 9.5 Operational Assumptions

1. **Holiday Calendar:** System admin updates holidays config before each year
2. **Teacher Onboarding:** Manual vetting process for teacher qualifications (offline)
3. **Question Bank Growth:** Question bank grows by ~500 questions/year via admin/teacher additions
4. **Support Availability:** Customer support available during working hours only (9 AM - 6 PM)
5. **Maintenance Window:** Weekly maintenance on Sundays 2-4 AM IST
6. **Scaling Timeline:** Manual infrastructure scaling (not auto-scaling in V1)
7. **Error Monitoring:** Manual review of error logs daily by engineering team
8. **SLA Breach Handling:** Admin manually reassigns breached evaluations to other teachers
9. **Payment Reconciliation:** Monthly manual reconciliation with payment gateway
10. **Content Moderation:** Inappropriate content flagged by teachers, reviewed by admin

---

## 10. Trade-offs

### 10.1 Technology Trade-offs

#### **Trade-off 1: RESTful API vs GraphQL**

**Decision:** RESTful API

**Pros:**
- Simpler to implement and debug
- Better caching with CloudFront
- Clearer RBAC enforcement per endpoint
- Easier rate limiting per resource type
- Standard HTTP semantics

**Cons:**
- Over-fetching data (e.g., full exam instance when only need status)
- Multiple round-trips for complex dashboards (exam list + subscription + analytics)
- Less flexible for frontend teams

**Why Chosen:** Simplicity and caching win for V1. Can add GraphQL in V2 for analytics queries.

---

#### **Trade-off 2: Direct S3 Upload vs Backend Proxy Upload**

**Decision:** Direct S3 upload with pre-signed URLs

**Pros:**
- Offloads upload traffic from backend servers
- Faster uploads (direct to S3)
- Reduces backend bandwidth costs
- Handles large files (5MB+ per page) without backend memory issues

**Cons:**
- More complex client-side logic
- Pre-signed URLs can expire during slow uploads
- Harder to track upload progress server-side
- CORS configuration required on S3

**Why Chosen:** Performance and cost savings outweigh complexity. Backend only generates URLs, not handles bytes.

---

#### **Trade-off 3: PostgreSQL Materialized Views vs Real-time Aggregation**

**Decision:** Materialized views for analytics/leaderboard

**Pros:**
- Fast read queries (pre-computed)
- Reduces database load during dashboard access
- Consistent performance even with large datasets

**Cons:**
- Data staleness (5-15 minute lag)
- Refresh overhead (blocks writes temporarily)
- Storage overhead (duplicate data)

**Why Chosen:** Analytics don't need real-time accuracy. Refreshing after each evaluation completion is acceptable.

---

#### **Trade-off 4: Redis vs PostgreSQL for Subscription Counters**

**Decision:** Redis for monthly exam counters

**Pros:**
- Atomic INCR/DECR operations
- Sub-millisecond latency
- Reduces database contention
- TTL-based auto-expiry for monthly resets

**Cons:**
- Data loss if Redis crashes (needs persistence)
- Eventual consistency with PostgreSQL source of truth
- Additional infrastructure to manage

**Why Chosen:** Exam start is a hot path. Redis ensures no race conditions when checking limits.

---

### 10.2 Architectural Trade-offs

#### **Trade-off 5: Monolith vs Microservices**

**Decision:** Modular monolith (single Node.js app with separate modules)

**Pros:**
- Simpler deployment (one ECS service)
- Easier transactions across modules (same database)
- Lower operational complexity
- Faster development iteration

**Cons:**
- Harder to scale individual modules independently
- All code deploys together (higher risk)
- Team coupling (one codebase)

**Why Chosen:** V1 team is small. Microservices overhead not justified. Can extract services later if needed.

---

#### **Trade-off 6: Immutable Exam Snapshots vs Question References**

**Decision:** Store full question content in exam snapshot (JSONB)

**Pros:**
- Student sees exact question even if original deleted/edited
- Reproducible scoring months later
- No foreign key dependency on questions table
- Enables question versioning without complex joins

**Cons:**
- Data duplication (same question stored in multiple exams)
- Larger database size (~10KB per exam)
- Harder to bulk-update questions (e.g., fix typo)

**Why Chosen:** Correctness and auditability > storage efficiency. Exams must be immutable.

---

#### **Trade-off 7: Single-Teacher Evaluation vs Multi-Teacher Moderation**

**Decision:** One teacher per exam, no re-evaluation (V1)

**Pros:**
- Simpler workflow (no moderation queue)
- Faster evaluation (no waiting for second opinion)
- Lower teacher costs (one evaluation, not two)
- Clearer accountability (one teacher's decision)

**Cons:**
- Potential marking inconsistency across teachers
- No appeals process for students
- Quality depends on individual teacher competence
- No checks for bias or errors

**Why Chosen:** Speed and cost win for practice exams (not high-stakes board exams). Can add moderation in V2 if quality issues arise.

---

### 10.3 UX Trade-offs

#### **Trade-off 8: Real-time Evaluation Queue vs Batch Assignment**

**Decision:** Real-time assignment to available teachers

**Pros:**
- Load balancing across teachers
- Teachers can pull next exam immediately
- Faster SLA compliance

**Cons:**
- No teacher specialization (e.g., specific units)
- No student-teacher continuity (different teacher each time)
- Cold-start problem (new teachers get fewer exams initially)

**Why Chosen:** SLA compliance is priority. Specialization can be added later via teacher tags.

---

#### **Trade-off 9: Inline Math Editor vs Image Upload for Student Answers**

**Decision:** Image upload (handwritten answers) for VSA/SA

**Pros:**
- Natural for students (write on paper as in real exams)
- No learning curve for math input
- Preserves student's working/steps
- Teachers see full solution process

**Cons:**
- Requires scanner/phone camera
- Upload reliability issues (network, file size)
- Slower than typing (for students with good devices)
- Not searchable/indexable

**Why Chosen:** Mimics real board exam experience. Students already comfortable with paper-based exams.

---

#### **Trade-off 10: Top 10 Leaderboard vs Full Ranking**

**Decision:** Show only top 10 students publicly

**Pros:**
- Privacy for lower-ranked students
- Reduces competition anxiety
- Smaller dataset to compute (faster)
- Encourages top performers

**Cons:**
- Students ranked 11-100 don't see their relative position
- Less motivation for mid-tier students
- Can't see friends' ranks (unless in top 10)

**Why Chosen:** Privacy and mental health concerns. Students still see their own rank in dashboard.

---

### 10.4 Business Trade-offs

#### **Trade-off 11: Monthly Exam Limits vs Unlimited Access**

**Decision:** Hard limits per plan (5/15/50 exams per month)

**Pros:**
- Predictable teacher workload
- Prevents abuse (taking 100 exams/month)
- Tiered pricing justification
- Easier capacity planning

**Cons:**
- Students may run out mid-month during exam season
- Friction if student wants "just one more"
- Unfair if student has unused exams (can't roll over)

**Why Chosen:** Sustainable teacher economics. Can add rollover or top-up packs in V2.

---

#### **Trade-off 12: Same-day SLA for Premium vs All Plans**

**Decision:** Same-day (24hr) only for Centum plan

**Pros:**
- Clear differentiation between plans
- Justifies 50% price premium for Centum
- Reduces teacher burnout (most exams have 48hr window)

**Cons:**
- Creates two-tier service quality
- Premium plan students may feel shortchanged
- Teachers need priority queue management

**Why Chosen:** Economics of teacher availability. Can't afford same-day for all without raising prices significantly.

---

### 10.5 ML-Readiness Trade-offs

#### **Trade-off 13: Opt-in ML Consent vs Automatic Collection**

**Decision:** Explicit opt-in consent for ML training data

**Pros:**
- Ethical and transparent
- Complies with future privacy regulations
- Builds user trust
- Avoids future legal issues

**Cons:**
- Lower dataset size (not all students opt in)
- Biased dataset (only privacy-unconcerned students)
- Slower ML development timeline

**Why Chosen:** Trust is critical for EdTech. Better to start with smaller, consented dataset.

---

#### **Trade-off 14: Human-only Evaluation (V1) vs Hybrid AI+Human**

**Decision:** No AI evaluation in V1, pure human teachers

**Pros:**
- Simpler to build and test
- Higher accuracy (teachers better than early AI models)
- No AI bias concerns
- Builds training dataset organically

**Cons:**
- Slower evaluation times
- Higher operational costs (teacher salaries)
- Less scalable (need to hire more teachers)
- Delayed ML product differentiation

**Why Chosen:** Get-to-market speed and quality. Use V1 to collect training data, launch AI in V2 when dataset is large.

---

**End of Engineering Specification Document**
