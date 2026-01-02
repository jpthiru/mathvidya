"""
Create User Script

Creates users (admin, teacher, student) in the database.

Usage:
    # Create admin user
    python scripts/create_user.py --role admin --email admin@mathvidya.com --password Admin@123 --first-name Admin --last-name User

    # Create teacher user
    python scripts/create_user.py --role teacher --email teacher@mathvidya.com --password Teacher@123 --first-name Math --last-name Teacher

    # Create student user
    python scripts/create_user.py --role student --email student@mathvidya.com --password Student@123 --first-name Test --last-name Student --class XII
"""

import argparse
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy import select
from database import AsyncSessionLocal
from models import User


async def create_user(
    email: str,
    password: str,
    role: str,
    first_name: str,
    last_name: str,
    student_class: str = None,
    phone: str = None
) -> bool:
    """
    Create a new user in the database.

    Args:
        email: User's email address
        password: Plain text password (will be hashed)
        role: User role (admin, teacher, student)
        first_name: User's first name
        last_name: User's last name
        student_class: Class level for students (X or XII)
        phone: Optional phone number

    Returns:
        True if user created, False if user already exists
    """
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).filter(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User with email '{email}' already exists (role: {existing_user.role})")
            return False

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            student_class=student_class if role == 'student' else None,
            is_active=True,
            email_verified=True  # Pre-verified for script-created users
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"Successfully created {role} user:")
        print(f"  Email: {email}")
        print(f"  Name: {first_name} {last_name}")
        print(f"  Role: {role}")
        if student_class and role == 'student':
            print(f"  Class: {student_class}")
        print(f"  User ID: {user.user_id}")

        return True


async def list_users(role: str = None):
    """List all users, optionally filtered by role."""
    async with AsyncSessionLocal() as db:
        query = select(User)
        if role:
            query = query.filter(User.role == role)
        query = query.order_by(User.role, User.email)

        result = await db.execute(query)
        users = result.scalars().all()

        if not users:
            print(f"No users found" + (f" with role '{role}'" if role else ""))
            return

        print(f"\n{'Email':<35} {'Name':<25} {'Role':<10} {'Verified':<10}")
        print("-" * 80)
        for user in users:
            name = f"{user.first_name} {user.last_name}"
            verified = "Yes" if user.email_verified else "No"
            print(f"{user.email:<35} {name:<25} {user.role:<10} {verified:<10}")
        print(f"\nTotal: {len(users)} user(s)")


async def reset_password(email: str, new_password: str):
    """Reset a user's password."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"User with email '{email}' not found")
            return False

        # Hash new password
        user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.email_verified = True  # Also verify email when resetting password
        await db.commit()

        print(f"Password reset successfully for {email}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Create or manage users in Mathvidya")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--email", "-e", required=True, help="User's email address")
    create_parser.add_argument("--password", "-p", required=True, help="User's password")
    create_parser.add_argument("--role", "-r", required=True, choices=["admin", "teacher", "student"], help="User role")
    create_parser.add_argument("--first-name", "-f", required=True, help="First name")
    create_parser.add_argument("--last-name", "-l", required=True, help="Last name")
    create_parser.add_argument("--class", dest="student_class", choices=["X", "XII"], help="Class level (for students)")
    create_parser.add_argument("--phone", help="Phone number")

    # List users command
    list_parser = subparsers.add_parser("list", help="List users")
    list_parser.add_argument("--role", "-r", choices=["admin", "teacher", "student"], help="Filter by role")

    # Reset password command
    reset_parser = subparsers.add_parser("reset-password", help="Reset user password")
    reset_parser.add_argument("--email", "-e", required=True, help="User's email address")
    reset_parser.add_argument("--password", "-p", required=True, help="New password")

    # Quick create commands for convenience
    admin_parser = subparsers.add_parser("admin", help="Quick create admin user")
    admin_parser.add_argument("--email", "-e", default="admin@mathvidya.com", help="Email (default: admin@mathvidya.com)")
    admin_parser.add_argument("--password", "-p", default="Admin@123", help="Password (default: Admin@123)")

    teacher_parser = subparsers.add_parser("teacher", help="Quick create teacher user")
    teacher_parser.add_argument("--email", "-e", default="teacher@mathvidya.com", help="Email")
    teacher_parser.add_argument("--password", "-p", default="Teacher@123", help="Password")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "create":
        if args.role == "student" and not args.student_class:
            print("Error: --class is required for student users")
            return
        asyncio.run(create_user(
            email=args.email,
            password=args.password,
            role=args.role,
            first_name=args.first_name,
            last_name=args.last_name,
            student_class=args.student_class,
            phone=args.phone
        ))

    elif args.command == "list":
        asyncio.run(list_users(role=args.role))

    elif args.command == "reset-password":
        asyncio.run(reset_password(email=args.email, new_password=args.password))

    elif args.command == "admin":
        asyncio.run(create_user(
            email=args.email,
            password=args.password,
            role="admin",
            first_name="Admin",
            last_name="User"
        ))

    elif args.command == "teacher":
        asyncio.run(create_user(
            email=args.email,
            password=args.password,
            role="teacher",
            first_name="Math",
            last_name="Teacher"
        ))


if __name__ == "__main__":
    main()
