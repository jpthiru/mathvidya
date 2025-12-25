# Phase 2: Exam Management - Implementation Complete

**Date**: December 24, 2025
**Status**: ✅ Complete

---

## Overview

Phase 2 adds complete exam management functionality to the Mathvidya backend, allowing students to:
- Browse available exam templates
- Start exams with dynamically generated questions
- Submit MCQ answers with auto-evaluation
- Upload answer sheets to S3
- View exam history and status

---

## ✅ Components Implemented

### 1. **Exam Schemas** ([schemas/exam.py](schemas/exam.py))

**Request Models:**
- `StartExamRequest` - Start a new exam
- `SubmitMCQRequest` - Submit MCQ answers with validation
- `UploadAnswerSheetRequest` - Request upload URL
- `ConfirmUploadRequest` - Confirm upload completion
- `DeclareUnansweredRequest` - Declare questions unanswered
- `SubmitExamRequest` - Final exam submission

**Response Models:**
- `AvailableTemplatesResponse` - List of exam templates
- `ExamTemplateResponse` - Template details
- `ExamInstanceResponse` - Active exam with questions
- `QuestionResponse` - Individual question
- `MCQResultResponse` - MCQ score and feedback
- `UploadAnswerSheetResponse` - S3 presigned URL
- `ExamHistoryResponse` - Past exam summary
- `ExamStatusResponse` - Current exam progress

### 2. **S3 Service** ([services/s3_service.py](services/s3_service.py))

**Features:**
- Generate presigned upload URLs (15 min expiry)
- Generate presigned download URLs (1 hour expiry)
- Structured S3 key generation:
  - Answer sheets: `answer-sheets/{exam_id}/{question_id}/page_{n}_{timestamp}_{uuid}.{ext}`
  - Question images: `question-images/{question_id}_{timestamp}_{uuid}.{ext}`
- File existence checking
- File deletion
- Configurable bucket and region

**Methods:**
- `generate_presigned_upload_url()` - Client uploads directly to S3
- `generate_presigned_download_url()` - Secure file access
- `generate_answer_sheet_key()` - Structured naming
- `generate_question_image_key()` - Question image paths
- `file_exists()` - Check file presence
- `delete_file()` - Remove files

### 3. **Exam Service** ([services/exam_service.py](services/exam_service.py))

**Business Logic:**
- `get_available_templates()` - Filter by class level
- `start_exam()` - Create instance + generate questions
- `_generate_exam_questions()` - Random selection by section config
- `submit_mcq_answers()` - Auto-evaluation and scoring
- `get_exam_status()` - Current progress
- `get_student_exam_history()` - Paginated history

**Key Features:**
- Prevents multiple active exams
- Random question selection based on template config
- Automatic MCQ scoring
- Exam state management
- Transaction handling

### 4. **Exam Routes** ([routes/exams.py](routes/exams.py))

**Endpoints Implemented:**

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/exams/templates` | Get available templates | Student |
| POST | `/api/v1/exams/start` | Start new exam | Student |
| POST | `/api/v1/exams/submit-mcq` | Submit MCQ answers | Student |
| POST | `/api/v1/exams/upload-answer-sheet` | Get S3 upload URL | Student |
| GET | `/api/v1/exams/{id}/status` | Get exam progress | Student |
| GET | `/api/v1/exams/history` | Get exam history | Student |

---

## 📊 API Endpoint Details

### GET /api/v1/exams/templates

**Purpose**: Get available exam templates for student's class

**Request**: None (uses current user's class)

**Response**:
```json
{
  "templates": [
    {
      "template_id": "uuid",
      "template_name": "CBSE Class XII Board Exam",
      "exam_type": "board_exam",
      "class_level": "XII",
      "total_marks": 80,
      "duration_minutes": 180,
      "section_config": {...},
      "is_active": true
    }
  ],
  "total": 3
}
```

---

### POST /api/v1/exams/start

**Purpose**: Start a new exam instance with generated questions

**Request**:
```json
{
  "template_id": "uuid",
  "exam_type": "board_exam"  // optional override
}
```

**Response**:
```json
{
  "exam_instance_id": "uuid",
  "student_user_id": "uuid",
  "exam_type": "board_exam",
  "status": "in_progress",
  "total_marks": 80,
  "duration_minutes": 180,
  "start_time": "2025-12-24T10:00:00Z",
  "questions": [
    {
      "question_id": "uuid",
      "question_number": 1,
      "question_type": "MCQ",
      "marks": 1,
      "unit": "Relations and Functions",
      "question_text": "If f(x) = x² + 2x, then f'(x) = ?",
      "options": ["A) 2x", "B) 2x + 2", "C) x + 2", "D) 2"],
      "difficulty": "medium"
    }
  ],
  "mcq_score": null,
  "total_score": null
}
```

**Business Logic**:
1. Check for active exams → reject if found
2. Validate template exists and is active
3. Generate random questions per section config
4. Create exam instance record
5. Return questions to student

---

### POST /api/v1/exams/submit-mcq

**Purpose**: Submit MCQ answers and get instant score

**Request**:
```json
{
  "exam_instance_id": "uuid",
  "answers": [
    {"question_id": "uuid1", "selected_option": "B"},
    {"question_id": "uuid2", "selected_option": "A"}
  ]
}
```

**Response**:
```json
{
  "exam_instance_id": "uuid",
  "total_mcq_questions": 20,
  "correct_answers": 17,
  "mcq_score": 17.0,
  "mcq_percentage": 85.0,
  "status": "submitted_mcq"
}
```

**Business Logic**:
1. Verify exam belongs to student
2. Check exam status is "in_progress"
3. For each answer:
   - Fetch question
   - Compare with correct answer
   - Calculate marks
4. Save all answers to `student_mcq_answers`
5. Update exam status to "submitted_mcq"
6. Return score breakdown

---

### POST /api/v1/exams/upload-answer-sheet

**Purpose**: Get S3 presigned URL for answer sheet upload

**Request**:
```json
{
  "exam_instance_id": "uuid",
  "question_id": "uuid",
  "page_number": 1,
  "file_name": "answer_page1.jpg"
}
```

**Response**:
```json
{
  "upload_id": "uuid",
  "presigned_url": "https://s3.amazonaws.com/...",
  "expires_in": 900
}
```

**Upload Flow**:
1. Student requests upload URL from backend
2. Backend generates S3 presigned URL (15 min expiry)
3. Backend creates `AnswerSheetUpload` record
4. Student uploads directly to S3 using presigned URL
5. S3 confirms upload
6. Student can repeat for multiple pages

**S3 Key Format**:
```
answer-sheets/{exam_id}/{question_id}/page_1_20251224103045_a1b2c3d4.jpg
```

---

### GET /api/v1/exams/{exam_instance_id}/status

**Purpose**: Get current status and progress of an exam

**Response**:
```json
{
  "exam_instance_id": "uuid",
  "status": "submitted_mcq",
  "start_time": "2025-12-24T10:00:00Z",
  "time_remaining_minutes": 120,
  "mcq_submitted": true,
  "answer_sheets_uploaded": 5,
  "total_answer_sheets_expected": 6,
  "is_submitted": false,
  "can_submit": false
}
```

**Use Cases**:
- Check time remaining
- Verify MCQ submission
- Count uploaded answer sheets
- Determine if ready for final submission

---

### GET /api/v1/exams/history

**Purpose**: Get student's exam history with pagination

**Query Parameters**:
- `limit`: Results per page (default: 20)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
[
  {
    "exam_instance_id": "uuid",
    "exam_type": "board_exam",
    "status": "evaluated",
    "start_time": "2025-12-20T10:00:00Z",
    "end_time": "2025-12-20T13:00:00Z",
    "total_marks": 80,
    "mcq_score": 18.0,
    "total_score": 72.5,
    "percentage": 90.63,
    "evaluated_at": "2025-12-21T10:00:00Z"
  }
]
```

---

## 🔐 Security Features

1. **Role-Based Access**: All exam endpoints require `student` role
2. **User Isolation**: Students can only access their own exams
3. **Presigned URLs**: Direct S3 upload without exposing credentials
4. **Time-Limited URLs**: Upload URLs expire in 15 minutes
5. **Validation**: Pydantic validates all request data
6. **SQL Injection Protection**: SQLAlchemy parameterized queries

---

## 🎯 Workflow Example

### Complete Exam Flow

```python
# 1. Student browses available templates
GET /api/v1/exams/templates
→ Returns list of templates for student's class

# 2. Student starts an exam
POST /api/v1/exams/start
Body: {"template_id": "uuid"}
→ Returns exam with 38 questions

# 3. Student answers MCQ section on-screen
POST /api/v1/exams/submit-mcq
Body: {
  "exam_instance_id": "uuid",
  "answers": [{"question_id": "...", "selected_option": "B"}, ...]
}
→ Returns instant score: 17/20 (85%)

# 4. Student writes VSA/SA on paper and scans

# 5. For each answer page, student requests upload URL
POST /api/v1/exams/upload-answer-sheet
Body: {
  "exam_instance_id": "uuid",
  "question_id": "uuid",
  "page_number": 1,
  "file_name": "answer1.jpg"
}
→ Returns presigned S3 URL

# 6. Student uploads directly to S3 (not through backend)
PUT https://s3.amazonaws.com/...?signature=...
Body: <image binary>

# 7. Repeat step 5-6 for all answer pages

# 8. Student checks status
GET /api/v1/exams/{id}/status
→ Shows 5/6 pages uploaded

# 9. After all uploads, backend automatically assigns to teacher
# (Background job - to be implemented in Phase 5)

# 10. Student can view history
GET /api/v1/exams/history
→ Returns all past exams
```

---

## 📦 Database Tables Used

| Table | Purpose |
|-------|---------|
| `exam_templates` | Exam configurations |
| `exam_instances` | Active and past exams |
| `questions` | Question bank |
| `student_mcq_answers` | MCQ submissions |
| `answer_sheet_uploads` | S3 upload tracking |
| `unanswered_questions` | Questions student didn't attempt |

---

## 🧪 Testing the Endpoints

### Using Swagger UI

1. Start server: `uvicorn main:app --reload`
2. Login at: `POST /api/v1/auth/login`
   - Email: `student@mathvidya.com`
   - Password: `student123`
3. Copy the `access_token` from response
4. Click "Authorize" button in Swagger UI (http://localhost:8000/api/docs)
5. Paste token with "Bearer " prefix
6. Test exam endpoints

### Using curl

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@mathvidya.com","password":"student123"}' \
  | jq -r '.access_token')

# Get templates
curl -X GET http://localhost:8000/api/v1/exams/templates \
  -H "Authorization: Bearer $TOKEN"

# Note: Templates need to be created in database first!
```

---

## ⚠️ Known Limitations

1. **No Exam Templates Yet**: Database has tables but no seed templates
   - Need to add exam templates via admin interface or SQL
   - Template structure defined but not populated

2. **Question Bank Empty**: No questions in database
   - Auto-generated exams will fail without questions
   - Need to populate question bank

3. **S3 Not Configured**: AWS credentials not set
   - Upload URLs will fail without valid AWS config
   - Set in `.env`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

4. **Final Submission Not Implemented**:
   - `SubmitExamRequest` schema ready but no endpoint yet
   - Need to add final submission logic

5. **Teacher Assignment Not Implemented**:
   - After upload, exam should go to teacher queue
   - Will be added in Phase 3 (Evaluation)

---

## 🚀 Next Steps (Phase 3: Evaluation)

1. **Teacher Routes**:
   - Get evaluation queue
   - Claim exam for evaluation
   - Submit marks and feedback
   - View evaluation history

2. **Evaluation Service**:
   - SLA tracking
   - Teacher workload distribution
   - Mark calculation
   - Status updates

3. **Evaluation Schemas**:
   - Question mark input
   - Teacher comments
   - Evaluation submission

---

## 📊 Current API Status

**Total Endpoints**: 18
- Authentication: 5 endpoints
- Exams: 6 endpoints
- Health: 3 endpoints
- Root: 1 endpoint

**Next Phase**: +8 endpoints (Evaluation)

---

## ✅ Phase 2 Checklist

- [x] Exam schemas created
- [x] S3 service implemented
- [x] Exam service with business logic
- [x] Exam routes and endpoints
- [x] Integration with main app
- [x] Role-based access control
- [x] Pydantic validation
- [x] Error handling
- [x] Documentation

**Status**: ✅ **Phase 2 Complete - Ready for Testing with Data**

---

**Note**: To fully test exam functionality, you need to:
1. Add exam templates to database
2. Populate question bank
3. Configure AWS S3 credentials
4. Create test exams via API
