"""
Seed Exam Templates

Creates default exam templates for Class X and Class XII.
Includes board exam, section-wise, and unit-wise practice templates.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from database import AsyncSessionLocal
from models.exam_template import ExamTemplate


# Class XII Units (CBSE Mathematics)
CLASS_XII_UNITS = [
    "Relations and Functions",
    "Inverse Trigonometric Functions",
    "Matrices",
    "Determinants",
    "Continuity and Differentiability",
    "Applications of Derivatives",
    "Integrals",
    "Applications of Integrals",
    "Differential Equations",
    "Vectors",
    "Three Dimensional Geometry",
    "Linear Programming",
    "Probability"
]

# Class X Units (CBSE Mathematics)
CLASS_X_UNITS = [
    "Number Systems",
    "Algebra",
    "Coordinate Geometry",
    "Geometry",
    "Trigonometry",
    "Mensuration",
    "Statistics and Probability"
]


def get_class_xii_board_config():
    """CBSE Class XII Board Exam pattern (80 marks, 3 hours)"""
    return {
        "total_marks": 80,
        "duration_minutes": 180,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Multiple Choice Questions",
                "question_type": "MCQ",
                "marks_per_question": 1,
                "question_count": 20,
                "instructions": "Each question carries 1 mark. Select the correct option.",
                "unit_weightage": {
                    "Relations and Functions": 0.10,
                    "Inverse Trigonometric Functions": 0.05,
                    "Matrices": 0.10,
                    "Determinants": 0.10,
                    "Continuity and Differentiability": 0.10,
                    "Applications of Derivatives": 0.10,
                    "Integrals": 0.15,
                    "Applications of Integrals": 0.05,
                    "Differential Equations": 0.05,
                    "Vectors": 0.05,
                    "Three Dimensional Geometry": 0.05,
                    "Linear Programming": 0.05,
                    "Probability": 0.05
                }
            },
            {
                "section_name": "B",
                "section_title": "Very Short Answer Questions",
                "question_type": "VSA",
                "marks_per_question": 2,
                "question_count": 5,
                "instructions": "Answer in 2-3 sentences. Each question carries 2 marks.",
                "unit_weightage": {
                    "Relations and Functions": 0.15,
                    "Matrices": 0.15,
                    "Continuity and Differentiability": 0.20,
                    "Integrals": 0.20,
                    "Vectors": 0.15,
                    "Probability": 0.15
                }
            },
            {
                "section_name": "C",
                "section_title": "Short Answer Questions",
                "question_type": "SA",
                "marks_per_question": 3,
                "question_count": 6,
                "instructions": "Answer with proper steps. Each question carries 3 marks.",
                "unit_weightage": {
                    "Relations and Functions": 0.10,
                    "Determinants": 0.15,
                    "Applications of Derivatives": 0.20,
                    "Integrals": 0.20,
                    "Differential Equations": 0.15,
                    "Three Dimensional Geometry": 0.10,
                    "Linear Programming": 0.10
                }
            },
            {
                "section_name": "D",
                "section_title": "Long Answer Questions",
                "question_type": "LA",
                "marks_per_question": 5,
                "question_count": 4,
                "instructions": "Answer with detailed steps and explanations. Each question carries 5 marks.",
                "unit_weightage": {
                    "Matrices": 0.15,
                    "Continuity and Differentiability": 0.20,
                    "Applications of Integrals": 0.20,
                    "Differential Equations": 0.15,
                    "Three Dimensional Geometry": 0.15,
                    "Probability": 0.15
                }
            },
            {
                "section_name": "E",
                "section_title": "Case Study Based Questions",
                "question_type": "SA",
                "marks_per_question": 4,
                "question_count": 3,
                "instructions": "Read the case study carefully and answer all parts.",
                "unit_weightage": {
                    "Applications of Derivatives": 0.30,
                    "Linear Programming": 0.35,
                    "Probability": 0.35
                }
            }
        ]
    }


def get_class_x_board_config():
    """CBSE Class X Board Exam pattern (80 marks, 3 hours)"""
    return {
        "total_marks": 80,
        "duration_minutes": 180,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Multiple Choice Questions",
                "question_type": "MCQ",
                "marks_per_question": 1,
                "question_count": 20,
                "instructions": "Each question carries 1 mark. Select the correct option.",
                "unit_weightage": {
                    "Number Systems": 0.10,
                    "Algebra": 0.25,
                    "Coordinate Geometry": 0.15,
                    "Geometry": 0.15,
                    "Trigonometry": 0.15,
                    "Mensuration": 0.10,
                    "Statistics and Probability": 0.10
                }
            },
            {
                "section_name": "B",
                "section_title": "Very Short Answer Questions",
                "question_type": "VSA",
                "marks_per_question": 2,
                "question_count": 5,
                "instructions": "Answer in 2-3 sentences. Each question carries 2 marks.",
                "unit_weightage": {
                    "Number Systems": 0.15,
                    "Algebra": 0.25,
                    "Geometry": 0.20,
                    "Trigonometry": 0.20,
                    "Statistics and Probability": 0.20
                }
            },
            {
                "section_name": "C",
                "section_title": "Short Answer Questions",
                "question_type": "SA",
                "marks_per_question": 3,
                "question_count": 6,
                "instructions": "Answer with proper steps. Each question carries 3 marks.",
                "unit_weightage": {
                    "Algebra": 0.25,
                    "Coordinate Geometry": 0.20,
                    "Geometry": 0.20,
                    "Trigonometry": 0.15,
                    "Mensuration": 0.20
                }
            },
            {
                "section_name": "D",
                "section_title": "Long Answer Questions",
                "question_type": "LA",
                "marks_per_question": 5,
                "question_count": 4,
                "instructions": "Answer with detailed steps and explanations. Each question carries 5 marks.",
                "unit_weightage": {
                    "Algebra": 0.30,
                    "Geometry": 0.25,
                    "Trigonometry": 0.20,
                    "Mensuration": 0.25
                }
            },
            {
                "section_name": "E",
                "section_title": "Case Study Based Questions",
                "question_type": "SA",
                "marks_per_question": 4,
                "question_count": 3,
                "instructions": "Read the case study carefully and answer all parts.",
                "unit_weightage": {
                    "Algebra": 0.30,
                    "Coordinate Geometry": 0.35,
                    "Statistics and Probability": 0.35
                }
            }
        ]
    }


def get_mcq_section_config(class_level):
    """MCQ-only practice (20 questions, 20 marks, 30 minutes)"""
    units = CLASS_XII_UNITS if class_level == "XII" else CLASS_X_UNITS
    weightage = {unit: 1.0 / len(units) for unit in units}

    return {
        "total_marks": 20,
        "duration_minutes": 30,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Multiple Choice Questions",
                "question_type": "MCQ",
                "marks_per_question": 1,
                "question_count": 20,
                "instructions": "Each question carries 1 mark. Select the correct option.",
                "unit_weightage": weightage
            }
        ]
    }


def get_vsa_section_config(class_level):
    """VSA-only practice (10 questions, 20 marks, 30 minutes)"""
    units = CLASS_XII_UNITS if class_level == "XII" else CLASS_X_UNITS
    weightage = {unit: 1.0 / len(units) for unit in units}

    return {
        "total_marks": 20,
        "duration_minutes": 30,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Very Short Answer Questions",
                "question_type": "VSA",
                "marks_per_question": 2,
                "question_count": 10,
                "instructions": "Answer in 2-3 sentences. Each question carries 2 marks.",
                "unit_weightage": weightage
            }
        ]
    }


def get_sa_section_config(class_level):
    """SA-only practice (6 questions, 18 marks, 45 minutes)"""
    units = CLASS_XII_UNITS if class_level == "XII" else CLASS_X_UNITS
    weightage = {unit: 1.0 / len(units) for unit in units}

    return {
        "total_marks": 18,
        "duration_minutes": 45,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Short Answer Questions",
                "question_type": "SA",
                "marks_per_question": 3,
                "question_count": 6,
                "instructions": "Answer with proper steps. Each question carries 3 marks.",
                "unit_weightage": weightage
            }
        ]
    }


def get_unit_practice_config(unit_name):
    """Unit-specific practice (mixed questions from one unit)"""
    return {
        "total_marks": 30,
        "duration_minutes": 45,
        "sections": [
            {
                "section_name": "A",
                "section_title": "Multiple Choice Questions",
                "question_type": "MCQ",
                "marks_per_question": 1,
                "question_count": 10,
                "instructions": "Each question carries 1 mark. Select the correct option.",
                "unit_weightage": {unit_name: 1.0}
            },
            {
                "section_name": "B",
                "section_title": "Very Short Answer Questions",
                "question_type": "VSA",
                "marks_per_question": 2,
                "question_count": 5,
                "instructions": "Answer in 2-3 sentences. Each question carries 2 marks.",
                "unit_weightage": {unit_name: 1.0}
            },
            {
                "section_name": "C",
                "section_title": "Short Answer Questions",
                "question_type": "SA",
                "marks_per_question": 3,
                "question_count": 3,
                "instructions": "Answer with proper steps. Each question carries 3 marks.",
                "unit_weightage": {unit_name: 1.0}
            }
        ]
    }


async def seed_templates():
    """Seed all exam templates"""
    async with AsyncSessionLocal() as session:
        # Check if templates already exist
        result = await session.execute(select(ExamTemplate).limit(1))
        if result.scalar_one_or_none():
            print("Exam templates already exist. Skipping seed.")
            return

        templates = []

        # Class XII Templates
        print("Creating Class XII templates...")

        # Board Exam
        templates.append(ExamTemplate(
            template_name="CBSE Class XII Board Exam Pattern",
            class_level="XII",
            exam_type="board_exam",
            config=get_class_xii_board_config(),
            is_active=True
        ))

        # Section-wise templates
        templates.append(ExamTemplate(
            template_name="Class XII MCQ Practice",
            class_level="XII",
            exam_type="section_mcq",
            config=get_mcq_section_config("XII"),
            is_active=True
        ))

        templates.append(ExamTemplate(
            template_name="Class XII VSA Practice",
            class_level="XII",
            exam_type="section_vsa",
            config=get_vsa_section_config("XII"),
            is_active=True
        ))

        templates.append(ExamTemplate(
            template_name="Class XII SA Practice",
            class_level="XII",
            exam_type="section_sa",
            config=get_sa_section_config("XII"),
            is_active=True
        ))

        # Unit-wise templates for Class XII
        for unit in CLASS_XII_UNITS:
            templates.append(ExamTemplate(
                template_name=f"Class XII - {unit} Practice",
                class_level="XII",
                exam_type="unit_practice",
                config=get_unit_practice_config(unit),
                specific_unit=unit,
                is_active=True
            ))

        # Class X Templates
        print("Creating Class X templates...")

        # Board Exam
        templates.append(ExamTemplate(
            template_name="CBSE Class X Board Exam Pattern",
            class_level="X",
            exam_type="board_exam",
            config=get_class_x_board_config(),
            is_active=True
        ))

        # Section-wise templates
        templates.append(ExamTemplate(
            template_name="Class X MCQ Practice",
            class_level="X",
            exam_type="section_mcq",
            config=get_mcq_section_config("X"),
            is_active=True
        ))

        templates.append(ExamTemplate(
            template_name="Class X VSA Practice",
            class_level="X",
            exam_type="section_vsa",
            config=get_vsa_section_config("X"),
            is_active=True
        ))

        templates.append(ExamTemplate(
            template_name="Class X SA Practice",
            class_level="X",
            exam_type="section_sa",
            config=get_sa_section_config("X"),
            is_active=True
        ))

        # Unit-wise templates for Class X
        for unit in CLASS_X_UNITS:
            templates.append(ExamTemplate(
                template_name=f"Class X - {unit} Practice",
                class_level="X",
                exam_type="unit_practice",
                config=get_unit_practice_config(unit),
                specific_unit=unit,
                is_active=True
            ))

        # Insert all templates
        session.add_all(templates)
        await session.commit()

        print(f"Successfully created {len(templates)} exam templates!")
        print(f"  - Class XII: 1 board exam + 3 section-wise + {len(CLASS_XII_UNITS)} unit-wise")
        print(f"  - Class X: 1 board exam + 3 section-wise + {len(CLASS_X_UNITS)} unit-wise")


async def main():
    print("Seeding Exam Templates...")
    print("=" * 50)
    await seed_templates()
    print("=" * 50)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
