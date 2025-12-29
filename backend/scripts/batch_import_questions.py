#!/usr/bin/env python3
"""
Batch Import Questions from Excel

This script imports questions from Excel files into the Mathvidya database.
All imported questions are marked as is_verified=false for manual verification.

Usage:
    python scripts/batch_import_questions.py <excel_file_path>

Example:
    python scripts/batch_import_questions.py ../Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx
"""

import sys
import os
import asyncio
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.settings import settings


def parse_correct_option(value: str) -> tuple:
    """Parse the 'Correct option and answer' column to extract option letter and answer text.

    Format examples:
        'A, Reflexive and Symmetric' -> ('A', 'Reflexive and Symmetric')
        'B, $\\pi/4$' -> ('B', '$\\pi/4$')
    """
    if pd.isna(value) or not value:
        return None, None

    value = str(value).strip()
    if ',' in value:
        parts = value.split(',', 1)
        option_letter = parts[0].strip().upper()
        answer_text = parts[1].strip() if len(parts) > 1 else None
        # Validate option letter
        if option_letter in ['A', 'B', 'C', 'D']:
            return option_letter, answer_text

    # If no comma, try to extract just the letter
    if value and value[0].upper() in ['A', 'B', 'C', 'D']:
        return value[0].upper(), value[1:].strip() if len(value) > 1 else None

    return None, None


def map_difficulty(value: str) -> str:
    """Map difficulty values to database enum values."""
    if pd.isna(value):
        return 'medium'

    value = str(value).lower().strip()
    mapping = {
        'easy': 'easy',
        'medium': 'medium',
        'hard': 'hard',
        'difficult': 'hard',
        'simple': 'easy',
    }
    return mapping.get(value, 'medium')


def map_question_type(value: str) -> str:
    """Map question type values to database enum values."""
    if pd.isna(value):
        return 'MCQ'

    value = str(value).upper().strip()
    mapping = {
        'MCQ': 'MCQ',
        'VSA': 'VSA',
        'SA': 'SA',
        'LA': 'LA',
        'MULTIPLE CHOICE': 'MCQ',
        'VERY SHORT ANSWER': 'VSA',
        'SHORT ANSWER': 'SA',
        'LONG ANSWER': 'LA',
    }
    return mapping.get(value, 'MCQ')


def clean_text(value) -> str:
    """Clean and normalize text values."""
    if pd.isna(value):
        return None
    return str(value).strip()


def process_excel_row(row: pd.Series) -> dict:
    """Convert an Excel row to a question dictionary for database insertion."""
    # Extract correct option letter and answer text
    correct_option, model_answer = parse_correct_option(row.get('Correct option and answer'))

    # Build options array (A, B, C, D)
    options = []
    for opt in ['Option A text', 'Option B text', 'Option C text', 'Option D text']:
        opt_text = clean_text(row.get(opt))
        options.append(opt_text if opt_text else '')

    # Map class level
    class_level = str(row.get('Class', 'XII')).strip().upper()
    if class_level not in ['X', 'XII']:
        class_level = 'XII'  # Default to XII

    # Get marks (default 1 for MCQ)
    marks = int(row.get('Marks', 1)) if pd.notna(row.get('Marks')) else 1

    question = {
        'question_id': str(uuid.uuid4()),
        'version': 1,
        'class_level': class_level,
        'unit': clean_text(row.get('Chapter/Unit')) or 'General',
        'chapter': None,  # Excel doesn't have separate chapter
        'topic': clean_text(row.get('Topic')),
        'question_type': map_question_type(row.get('Question Type')),
        'marks': marks,
        'difficulty': map_difficulty(row.get('Difficulty')),
        'question_text': clean_text(row.get('Question Text in LaTeX')),
        'question_image_url': clean_text(row.get('image')),
        'diagram_image_url': None,
        'options': options,
        'correct_option': correct_option,
        'model_answer': model_answer,
        'marking_scheme': clean_text(row.get('Explanation or solution text in LaTeX')),
        'cbse_year': None,
        'tags': [],
        'status': 'active',
        'is_verified': False,
        'verified_by_user_id': None,
        'verified_at': None,
        'created_by_user_id': None,  # System import
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }

    return question


async def import_questions(excel_path: str, dry_run: bool = False):
    """Import questions from Excel file to database."""

    # Read Excel file
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"Found {len(df)} rows in Excel file")

    # Process rows
    questions = []
    errors = []

    for idx, row in df.iterrows():
        try:
            question = process_excel_row(row)

            # Validate required fields
            if not question['question_text']:
                errors.append(f"Row {idx + 2}: Missing question text")
                continue

            if question['question_type'] == 'MCQ':
                if not question['correct_option']:
                    errors.append(f"Row {idx + 2}: Missing correct option for MCQ")
                    continue
                if not all(question['options']):
                    errors.append(f"Row {idx + 2}: Missing one or more options for MCQ")
                    continue

            questions.append(question)

        except Exception as e:
            errors.append(f"Row {idx + 2}: Error processing - {str(e)}")

    print(f"\nProcessed {len(questions)} valid questions")
    if errors:
        print(f"Skipped {len(errors)} rows with errors:")
        for err in errors[:10]:  # Show first 10 errors
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

    if dry_run:
        print("\n[DRY RUN] No changes made to database")
        print("\nSample question data:")
        if questions:
            sample = questions[0].copy()
            sample['created_at'] = str(sample['created_at'])
            sample['updated_at'] = str(sample['updated_at'])
            print(json.dumps(sample, indent=2))
        return

    # Connect to database
    print(f"\nConnecting to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Insert questions in batches
        batch_size = 50
        inserted_count = 0

        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]

            for q in batch:
                # Build INSERT statement
                insert_sql = text("""
                    INSERT INTO questions (
                        question_id, version, class, unit, chapter, topic,
                        question_type, marks, difficulty, question_text,
                        question_image_url, diagram_image_url, options, correct_option,
                        model_answer, marking_scheme, cbse_year, tags, status,
                        is_verified, verified_by_user_id, verified_at,
                        created_by_user_id, created_at, updated_at
                    ) VALUES (
                        :question_id, :version, :class_level, :unit, :chapter, :topic,
                        CAST(:question_type AS mv_question_type),
                        :marks,
                        CAST(:difficulty AS mv_question_difficulty),
                        :question_text,
                        :question_image_url, :diagram_image_url,
                        :options,
                        :correct_option,
                        :model_answer, :marking_scheme, :cbse_year, :tags,
                        CAST(:status AS mv_question_status),
                        :is_verified, :verified_by_user_id, :verified_at,
                        :created_by_user_id, :created_at, :updated_at
                    )
                """)

                await session.execute(insert_sql, {
                    'question_id': q['question_id'],
                    'version': q['version'],
                    'class_level': q['class_level'],
                    'unit': q['unit'],
                    'chapter': q['chapter'],
                    'topic': q['topic'],
                    'question_type': q['question_type'],
                    'marks': q['marks'],
                    'difficulty': q['difficulty'],
                    'question_text': q['question_text'],
                    'question_image_url': q['question_image_url'],
                    'diagram_image_url': q['diagram_image_url'],
                    'options': json.dumps(q['options']),  # JSON serialize for JSONB
                    'correct_option': q['correct_option'],
                    'model_answer': q['model_answer'],
                    'marking_scheme': q['marking_scheme'],
                    'cbse_year': q['cbse_year'],
                    'tags': q['tags'],  # ARRAY type handles list directly
                    'status': q['status'],
                    'is_verified': q['is_verified'],
                    'verified_by_user_id': q['verified_by_user_id'],
                    'verified_at': q['verified_at'],
                    'created_by_user_id': q['created_by_user_id'],
                    'created_at': q['created_at'],
                    'updated_at': q['updated_at'],
                })
                inserted_count += 1

            await session.commit()
            print(f"Inserted batch {i // batch_size + 1}: {inserted_count} / {len(questions)} questions")

        print(f"\n✓ Successfully imported {inserted_count} questions")
        print(f"  All questions marked as is_verified=false")
        print(f"  Use the Verify Questions page to review and verify them")


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_import_questions.py <excel_file_path> [--dry-run]")
        print("\nExample:")
        print("  python batch_import_questions.py ../Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx")
        print("  python batch_import_questions.py ../Data-BatchUpload/MCQ-ClassXII-Batch1.xlsx --dry-run")
        sys.exit(1)

    excel_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    if not os.path.exists(excel_path):
        print(f"Error: File not found: {excel_path}")
        sys.exit(1)

    asyncio.run(import_questions(excel_path, dry_run))


if __name__ == '__main__':
    main()
