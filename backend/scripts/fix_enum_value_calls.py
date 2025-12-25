"""
Script to remove .value calls on enum columns since they now return strings directly
"""

import re
from pathlib import Path

def fix_value_calls(content: str, filename: str) -> str:
    """Remove .value calls on enum attributes"""

    # Map of model files to their enum column names
    enum_columns = {
        'user.py': ['role'],
        'mapping.py': ['relationship'],
        'subscription.py': ['plan_type', 'status'],
        'question.py': ['question_type', 'difficulty', 'status'],
        'exam_template.py': ['exam_type'],
        'exam_instance.py': ['exam_type', 'status'],
        'evaluation.py': ['status', 'question_type'],
        'system.py': ['actor_role']
    }

    if filename not in enum_columns:
        return content

    columns = enum_columns[filename]

    # For each enum column, remove .value calls
    for col in columns:
        # Pattern 1: self.column.value
        pattern1 = rf'self\.{col}\.value'
        replacement1 = f'self.{col}'
        content = re.sub(pattern1, replacement1, content)
        print(f"  Removed .value from self.{col}")

    return content

def process_file(file_path: Path):
    """Process a single model file"""
    print(f"\nProcessing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix .value calls
    content = fix_value_calls(content, file_path.name)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated {file_path.name}")
    else:
        print(f"  No changes needed")

def main():
    models_dir = Path(__file__).parent.parent / 'models'

    # Files that have .value calls
    files_to_process = [
        'user.py',
        'mapping.py',
        'subscription.py',
        'question.py',
        'exam_template.py',
        'exam_instance.py',
        'evaluation.py',
        'system.py'
    ]

    print("Removing .value calls from enum columns...\n")

    for filename in files_to_process:
        file_path = models_dir / filename
        if file_path.exists():
            process_file(file_path)
        else:
            print(f"Warning: {filename} not found")

    print("\nDone!")

if __name__ == '__main__':
    main()
