"""
Update PgEnum implementation in all model files to use the working version
"""

import re
from pathlib import Path

CORRECT_PGENUM = '''class PgEnum(TypeDecorator):
    """Custom type to handle PostgreSQL ENUMs as strings

    This decorator wraps String columns to properly cast values to PostgreSQL enum types.
    It generates SQL like: CAST(:param AS enum_type_name)
    """
    impl = String
    cache_ok = True

    def __init__(self, enum_type_name, *args, **kwargs):
        self.enum_type_name = enum_type_name
        super().__init__(*args, **kwargs)

    def bind_expression(self, bindvalue):
        #  Use text() to create a custom type reference for casting
        from sqlalchemy import text
        # Create a type clause that can be used in CAST
        from sqlalchemy.dialects.postgresql import ENUM
        # Create an anonymous enum type just for the cast
        enum_type = ENUM(name=self.enum_type_name, create_type=False)
        from sqlalchemy import cast
        return cast(bindvalue, enum_type)

'''

def update_pgenum_class(content: str) -> tuple[str, bool]:
    """Replace PgEnum class with the correct implementation"""

    # Pattern to match the entire PgEnum class definition
    pattern = r'class PgEnum\(TypeDecorator\):.*?(?=\n(?:class|\Z))'

    # Find the class
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content, False

    # Replace it
    content = re.sub(pattern, CORRECT_PGENUM.rstrip() + '\n', content, flags=re.DOTALL)
    return content, True

def process_file(file_path: Path):
    """Process a single model file"""
    print(f"\nProcessing {file_path.name}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Update PgEnum class
    content, updated = update_pgenum_class(content)

    if updated:
        print(f"  Updated PgEnum implementation")
    else:
        print(f"  No PgEnum class found")

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Saved {file_path.name}")
    else:
        print(f"  No changes needed")

def main():
    models_dir = Path(__file__).parent.parent / 'models'

    # Files that have enum columns and PgEnum class
    files_to_process = [
        'mapping.py',
        'subscription.py',
        'question.py',
        'exam_template.py',
        'exam_instance.py',
        'evaluation.py',
        'system.py'
    ]

    print("Updating PgEnum implementation in model files...\n")

    for filename in files_to_process:
        file_path = models_dir / filename
        if file_path.exists():
            process_file(file_path)
        else:
            print(f"Warning: {filename} not found")

    print("\nDone!")

if __name__ == '__main__':
    main()
