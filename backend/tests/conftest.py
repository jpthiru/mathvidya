"""
Test Configuration and Fixtures

This module contains pytest fixtures and configuration for testing the Mathvidya backend.

Unit tests: Run without database using mock objects
Integration tests: Run against PostgreSQL using TEST_DATABASE_URL environment variable

Usage:
    # Run unit tests only (no database required)
    pytest tests/test_models.py tests/test_services.py -v

    # Run all tests including integration tests (requires database)
    set TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mvdb_test
    pytest tests/ -v
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
import uuid
import sys
from pathlib import Path

# Add the backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dependencies.auth import create_access_token
from models.enums import UserRole


# ============================================
# Database Configuration
# ============================================

# Get test database URL from environment or use the main database
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", "")
)

# Check if we have a valid database URL for integration tests
HAS_DATABASE = bool(TEST_DATABASE_URL and "postgresql" in TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# Database Fixtures (for integration tests)
# ============================================

if HAS_DATABASE:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from httpx import AsyncClient, ASGITransport
    from database import Base
    from main import app
    from models.user import User
    from models.promo_code import PromoCode, PromoType
    from models.email_verification import EmailVerification
    from routes.auth import hash_password

    @pytest_asyncio.fixture(scope="session")
    async def test_engine():
        """Create a test database engine."""
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        yield engine
        await engine.dispose()

    @pytest_asyncio.fixture(scope="function")
    async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
        """Create a database session for each test."""
        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session() as session:
            yield session
            # Rollback any uncommitted changes after each test
            await session.rollback()

    @pytest_asyncio.fixture(scope="function")
    async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
        """Create an async HTTP client for testing API endpoints."""
        # Override the database dependency
        from database import get_session
        from config.settings import settings

        async def override_get_session():
            yield db_session

        app.dependency_overrides[get_session] = override_get_session

        # Disable reCAPTCHA for testing
        original_recaptcha_enabled = settings.RECAPTCHA_ENABLED
        settings.RECAPTCHA_ENABLED = False

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac
        finally:
            # Restore settings and clear overrides
            settings.RECAPTCHA_ENABLED = original_recaptcha_enabled
            app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def test_student(db_session: AsyncSession) -> User:
        """Create a test student user in the database."""
        from sqlalchemy import select

        # Check if user already exists
        result = await db_session.execute(
            select(User).where(User.email == "teststudent@test.com")
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        user = User(
            email="teststudent@test.com",
            password_hash=hash_password("testpass123"),
            role=UserRole.STUDENT.value,
            first_name="Test",
            last_name="Student",
            phone="9876543210",
            student_class="XII",
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_teacher(db_session: AsyncSession) -> User:
        """Create a test teacher user in the database."""
        from sqlalchemy import select

        result = await db_session.execute(
            select(User).where(User.email == "testteacher@test.com")
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        user = User(
            email="testteacher@test.com",
            password_hash=hash_password("testpass123"),
            role=UserRole.TEACHER.value,
            first_name="Test",
            last_name="Teacher",
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def test_admin(db_session: AsyncSession) -> User:
        """Create a test admin user in the database."""
        from sqlalchemy import select

        result = await db_session.execute(
            select(User).where(User.email == "testadmin@test.com")
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        user = User(
            email="testadmin@test.com",
            password_hash=hash_password("testpass123"),
            role=UserRole.ADMIN.value,
            first_name="Test",
            last_name="Admin",
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def student_auth_token(test_student: User) -> str:
        """Create a JWT token for the test student."""
        return create_access_token(
            data={"sub": str(test_student.user_id), "role": test_student.role},
            expires_delta=timedelta(hours=1)
        )

    @pytest_asyncio.fixture
    async def teacher_auth_token(test_teacher: User) -> str:
        """Create a JWT token for the test teacher."""
        return create_access_token(
            data={"sub": str(test_teacher.user_id), "role": test_teacher.role},
            expires_delta=timedelta(hours=1)
        )

    @pytest_asyncio.fixture
    async def admin_auth_token(test_admin: User) -> str:
        """Create a JWT token for the test admin."""
        return create_access_token(
            data={"sub": str(test_admin.user_id), "role": test_admin.role},
            expires_delta=timedelta(hours=1)
        )

    @pytest_asyncio.fixture
    async def test_promo_code(db_session: AsyncSession) -> PromoCode:
        """Create a test promo code in the database."""
        from sqlalchemy import select

        result = await db_session.execute(
            select(PromoCode).where(PromoCode.code == "TESTPROMO20")
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        promo = PromoCode(
            code="TESTPROMO20",
            description="Test 20% discount",
            promo_type=PromoType.PERCENTAGE.value,
            discount_percentage=20.0,
            max_uses=100,
            max_uses_per_user=1,
            is_active=True,
        )
        db_session.add(promo)
        await db_session.commit()
        await db_session.refresh(promo)
        return promo


# ============================================
# Mock User Objects (no database required)
# ============================================

class MockUser:
    """Mock user object for testing without database."""

    def __init__(
        self,
        user_id=None,
        email="test@example.com",
        role=UserRole.STUDENT.value,
        first_name="Test",
        last_name="User",
        phone="9876543210",
        student_class="XII",
        is_active=True,
        email_verified=True,
    ):
        self.user_id = user_id or uuid.uuid4()
        self.email = email
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.student_class = student_class
        self.is_active = is_active
        self.email_verified = email_verified
        self.password_hash = "$2b$12$mock_hash"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "student_class": self.student_class,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
        }


@pytest.fixture
def mock_student() -> MockUser:
    """Create a mock student user."""
    return MockUser(
        email="student@test.com",
        role=UserRole.STUDENT.value,
        first_name="Test",
        last_name="Student",
    )


@pytest.fixture
def mock_teacher() -> MockUser:
    """Create a mock teacher user."""
    return MockUser(
        email="teacher@test.com",
        role=UserRole.TEACHER.value,
        first_name="Test",
        last_name="Teacher",
        student_class=None,
    )


@pytest.fixture
def mock_admin() -> MockUser:
    """Create a mock admin user."""
    return MockUser(
        email="admin@test.com",
        role=UserRole.ADMIN.value,
        first_name="Test",
        last_name="Admin",
        student_class=None,
    )


# ============================================
# Token Fixtures (for unit tests)
# ============================================

@pytest.fixture
def student_token(mock_student: MockUser) -> str:
    """Create a JWT token for the mock student."""
    return create_access_token(
        data={"sub": str(mock_student.user_id), "role": mock_student.role},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def teacher_token(mock_teacher: MockUser) -> str:
    """Create a JWT token for the mock teacher."""
    return create_access_token(
        data={"sub": str(mock_teacher.user_id), "role": mock_teacher.role},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def admin_token(mock_admin: MockUser) -> str:
    """Create a JWT token for the mock admin."""
    return create_access_token(
        data={"sub": str(mock_admin.user_id), "role": mock_admin.role},
        expires_delta=timedelta(hours=1)
    )


def get_auth_headers(token: str) -> dict:
    """Helper to create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Mock Fixtures for External Services
# ============================================

@pytest.fixture
def mock_email_service():
    """Mock email service to prevent actual email sending during tests."""
    with patch("services.email_service.email_service") as mock:
        mock.send_verification_email = MagicMock(return_value=True)
        mock.send_password_reset_email = MagicMock(return_value=True)
        mock.send_welcome_email = MagicMock(return_value=True)
        yield mock


@pytest.fixture
def mock_recaptcha():
    """Mock reCAPTCHA verification to always pass during tests."""
    with patch("services.recaptcha_service.verify_recaptcha") as mock:
        async def mock_verify(*args, **kwargs):
            return (True, 0.9, None)
        mock.side_effect = mock_verify
        yield mock


@pytest.fixture
def mock_s3_service():
    """Mock S3 service to prevent actual S3 operations during tests."""
    with patch("services.s3_service.s3_service") as mock:
        mock.generate_presigned_url = MagicMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
        mock.upload_file = AsyncMock(return_value=True)
        mock.delete_file = AsyncMock(return_value=True)
        yield mock
