import asyncio
import bcrypt
from database import AsyncSessionLocal
from models import User, UserRole

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Bcrypt requires bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')

async def create_test_users():
    async with AsyncSessionLocal() as session:
        # Create admin user
        admin = User(
            email="admin@mathvidya.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN.value,  # Use .value to get the string
            first_name="Admin",
            last_name="User"
        )
        session.add(admin)

        # Create teacher
        teacher = User(
            email="teacher@mathvidya.com",
            password_hash=hash_password("teacher123"),
            role=UserRole.TEACHER.value,  # Use .value to get the string
            first_name="Math",
            last_name="Teacher"
        )
        session.add(teacher)

        # Create student
        student = User(
            email="student@mathvidya.com",
            password_hash=hash_password("student123"),
            role=UserRole.STUDENT.value,  # Use .value to get the string
            first_name="Test",
            last_name="Student",
            student_class="XII"
        )
        session.add(student)
        
        await session.commit()
        print("Created 3 test users:")
        print(f"  - Admin: admin@mathvidya.com / admin123")
        print(f"  - Teacher: teacher@mathvidya.com / teacher123")
        print(f"  - Student: student@mathvidya.com / student123")

if __name__ == "__main__":
    asyncio.run(create_test_users())