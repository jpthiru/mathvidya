"""
Script to add PgEnum TypeDecorator to all model files with enum columns
"""

import re
from pathlib import Path

# PgEnum class definition to add to each file
PGENUM_CLASS = '''
class PgEnum(TypeDecorator):
    """Custom type to handle PostgreSQL ENUMs as strings"""
    impl = String
    cache_ok = True

    def __init__(self, enum_type_name, *args, **kwargs):
        self.enum_type_name = enum_type_name
        super().__init__(*args, **kwargs)

    def column_expression(self, col):
        # Cast the column to text when reading
        from sqlalchemy import cast, Text
        return cast(col, Text)

    def bind_expression(self, bindvalue):
        # Cast the value to the enum type when writing
        from sqlalchemy import cast, text
        return cast(bindvalue, text(self.enum_type_name))

'''

# Mapping of enum type names to their string lengths
ENUM_MAPPINGS = {
    'mv_user_role': 20,
    'mv_relationship_type': 20,
    'mv_plan_type': 20,
    'mv_subscription_status': 20,
    'mv_question_type': 10,
    'mv_question_difficulty': 20,
    'mv_question_status': 20,
    'mv_exam_type': 30,
    'mv_exam_status': 30,
    'mv_evaluation_status': 20
}

def add_pgenum_class(content: str) -> str:
    """Add PgEnum class after TypeDecorator import if not already present"""
    if 'class PgEnum(TypeDecorator):' in content:
        print("  OK PgEnum class already present")
        return content

    # Find the import section and add TypeDecorator if needed
    if 'from sqlalchemy import TypeDecorator' not in content:
        # Add TypeDecorator to sqlalchemy imports
        content = re.sub(
            r'(from sqlalchemy import [^)]+)',
            r'\1, TypeDecorator',
            content,
            count=1
        )
        print("  + Added TypeDecorator to imports")

    # Find a good place to insert the class (after imports, before first class definition)
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_idx = i + 1
        elif line.startswith('class ') and insert_idx > 0:
            break

    lines.insert(insert_idx, PGENUM_CLASS)
    print("  + Added PgEnum class definition")
    return '\n'.join(lines)

def fix_enum_column(match):
    """Replace Enum(...) with PgEnum(...) in Column definition"""
    full_match = match.group(0)

    # Extract the enum type name from name='...'
    name_match = re.search(r"name='(mv_[^']+)'", full_match)
    if not name_match:
        return full_match

    enum_name = name_match.group(1)
    string_length = ENUM_MAPPINGS.get(enum_name, 50)

    # Replace Enum(...) with PgEnum('enum_name', length)
    # Pattern: Enum(EnumClass, name='mv_...', create_type=False)
    # Replace with: PgEnum('mv_...', length)

    result = re.sub(
        r'Enum\([^,]+,\s*name=' + f"'{enum_name}'" + r',\s*create_type=False\)',
        f"PgEnum('{enum_name}', {string_length})",
        full_match
    )

    return result

def process_file(file_path: Path):
    """Process a single model file"""
    print(f"\nProcessing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Add PgEnum class
    content = add_pgenum_class(content)

    # Fix all enum columns
    pattern = r'Column\(Enum\([^)]+, name=\'mv_[^\']+\', create_type=False\)[^)]*\)'
    matches = list(re.finditer(pattern, content))

    if matches:
        print(f"  Found {len(matches)} enum column(s) to fix")
        content = re.sub(pattern, fix_enum_column, content)
        print("  OK Updated enum columns to use PgEnum")
    else:
        print("  No enum columns found")

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated Updated {file_path.name}")
    else:
        print(f"  Info  No changes needed")

def main():
    models_dir = Path(__file__).parent.parent / 'models'

    # Files that have enum columns
    files_to_process = [
        'mapping.py',
        'subscription.py',
        'question.py',
        'exam_template.py',
        'exam_instance.py',
        'evaluation.py',
        'system.py'
    ]

    print("Fixing enum columns in model files...\n")

    for filename in files_to_process:
        file_path = models_dir / filename
        if file_path.exists():
            process_file(file_path)
        else:
            print(f"Warning: {filename} not found")

    print("\nDone!")

if __name__ == '__main__':
    main()
