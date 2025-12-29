"""Placeholder for batch import MCQ questions for Class XII

Revision ID: 007
Revises: 006
Create Date: 2025-12-29

This migration is a placeholder documenting the batch import process.
The actual import is done via Python script for better error handling and progress tracking.

Data source: Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx
- 277 MCQ questions for Class XII
- All questions marked as is_verified=false for manual verification

To import questions, run:
    cd backend
    python scripts/batch_import_questions.py ../Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx

For dry run (no database changes):
    python scripts/batch_import_questions.py ../Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx --dry-run

In Docker:
    sudo docker-compose -f docker-compose.prod.yml exec backend python scripts/batch_import_questions.py /app/Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Placeholder migration - actual import done via scripts/batch_import_questions.py

    The script:
    1. Reads Excel file with columns: Class, Chapter/Unit, Question Type, Topic,
       Difficulty, Marks, Question Text in LaTeX, Option A-D text,
       Correct option and answer, Explanation or solution text in LaTeX, image
    2. Maps columns to database fields
    3. Inserts questions with is_verified=false
    4. Provides progress tracking and error reporting
    """
    pass


def downgrade() -> None:
    """
    To remove batch-imported questions:

    DELETE FROM questions
    WHERE is_verified = false
    AND created_at >= '2025-12-29'  -- Adjust date as needed
    AND question_type = 'MCQ'
    AND class = 'XII';
    """
    pass
