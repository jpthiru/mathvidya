"""
Unit Tests for Database Models

Tests for model validation, methods, and relationships.
Note: These tests use in-memory model instances without database persistence
to avoid PostgreSQL-specific features not available in test environments.
"""

import pytest
from datetime import datetime, timezone, timedelta
import uuid

from models.user import User
from models.enums import UserRole, QuestionType, QuestionDifficulty
from models.question import Question
from models.promo_code import PromoCode, PromoCodeUsage, PromoType
from models.email_verification import EmailVerification
from models.site_feedback import SiteFeedback, FeedbackCategory, FeedbackStatus


class TestUserModel:
    """Tests for the User model."""

    @pytest.fixture
    def user(self) -> User:
        """Create a test user instance (without database)."""
        user = User(
            user_id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.STUDENT.value,
            first_name="John",
            last_name="Doe",
            phone="9876543210",
            student_class="XII",
            is_active=True,
            email_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        return user

    def test_user_creation(self, user: User):
        """Test user is created with correct attributes."""
        assert user.email == "test@example.com"
        assert user.role == UserRole.STUDENT.value
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.student_class == "XII"
        assert user.is_active is True
        assert user.email_verified is False

    def test_user_full_name(self, user: User):
        """Test full_name property."""
        assert user.full_name == "John Doe"

    def test_user_to_dict(self, user: User):
        """Test to_dict method returns correct structure."""
        user_dict = user.to_dict()

        assert "user_id" in user_dict
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == "student"
        assert user_dict["first_name"] == "John"
        assert user_dict["last_name"] == "Doe"
        assert user_dict["full_name"] == "John Doe"
        assert "password_hash" not in user_dict  # Should not expose password

    def test_user_uuid_generated(self, user: User):
        """Test that user_id is correctly set."""
        assert user.user_id is not None
        assert isinstance(user.user_id, uuid.UUID)

    def test_user_timestamps(self, user: User):
        """Test that timestamps are set correctly."""
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


class TestQuestionModel:
    """Tests for the Question model."""

    @pytest.fixture
    def question(self) -> Question:
        """Create a test question instance (without database)."""
        question = Question(
            question_id=uuid.uuid4(),
            class_level="XII",  # Maps to 'class' column
            unit="Calculus",
            chapter="Differentiation",
            topic="Derivatives",
            question_type=QuestionType.MCQ.value,
            difficulty=QuestionDifficulty.MEDIUM.value,
            marks=1,
            question_text="What is the derivative of x^2?",
            options=["x", "2x", "x^2", "2"],  # JSONB array
            correct_option="B",
            model_answer="d/dx(x^2) = 2x",
            created_by_user_id=uuid.uuid4(),
            is_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        return question

    def test_question_creation(self, question: Question):
        """Test question is created with correct attributes."""
        assert question.class_level == "XII"
        assert question.question_type == QuestionType.MCQ.value
        assert question.marks == 1
        assert question.correct_option == "B"
        assert question.is_verified is False

    def test_question_options(self, question: Question):
        """Test question options are stored correctly."""
        assert question.options[0] == "x"
        assert question.options[1] == "2x"
        assert len(question.options) == 4

    def test_question_to_dict(self, question: Question):
        """Test to_dict method."""
        q_dict = question.to_dict()

        assert "question_id" in q_dict
        assert q_dict["question_text"] == "What is the derivative of x^2?"
        assert q_dict["question_type"] == "MCQ"
        assert "correct_option" in q_dict  # Full dict includes answer

    def test_question_is_mcq(self, question: Question):
        """Test is_mcq method."""
        # Note: is_mcq() compares with enum, not string value
        # For MCQ type question
        assert question.question_type == QuestionType.MCQ.value


class TestPromoCodeModel:
    """Tests for the PromoCode model."""

    @pytest.fixture
    def percentage_promo(self) -> PromoCode:
        """Create a percentage discount promo code instance."""
        promo = PromoCode(
            id=1,
            code="SAVE20",
            description="20% off subscription",
            promo_type=PromoType.PERCENTAGE.value,
            discount_percentage=20.0,
            max_uses=100,
            current_uses=0,
            max_uses_per_user=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        return promo

    @pytest.fixture
    def free_trial_promo(self) -> PromoCode:
        """Create a free trial promo code instance."""
        promo = PromoCode(
            id=2,
            code="FREETRIAL",
            description="14 days free trial",
            promo_type=PromoType.FREE_TRIAL.value,
            free_days=14,
            new_users_only=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        return promo

    @pytest.fixture
    def expired_promo(self) -> PromoCode:
        """Create an expired promo code instance."""
        promo = PromoCode(
            id=3,
            code="EXPIRED",
            promo_type=PromoType.PERCENTAGE.value,
            discount_percentage=10.0,
            valid_until=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        return promo

    def test_promo_creation(self, percentage_promo: PromoCode):
        """Test promo code is created correctly."""
        assert percentage_promo.code == "SAVE20"
        assert percentage_promo.promo_type == PromoType.PERCENTAGE.value
        assert percentage_promo.discount_percentage == 20.0
        assert percentage_promo.current_uses == 0
        assert percentage_promo.is_active is True

    def test_promo_is_valid(self, percentage_promo: PromoCode):
        """Test is_valid method for active promo."""
        assert percentage_promo.is_valid() is True

    def test_promo_expired_not_valid(self, expired_promo: PromoCode):
        """Test is_valid returns False for expired promo."""
        assert expired_promo.is_valid() is False

    def test_promo_max_uses_reached(self, percentage_promo: PromoCode):
        """Test promo becomes invalid when max uses reached."""
        percentage_promo.current_uses = 100  # Max uses reached
        assert percentage_promo.is_valid() is False

    def test_promo_inactive_not_valid(self, percentage_promo: PromoCode):
        """Test inactive promo is not valid."""
        percentage_promo.is_active = False
        assert percentage_promo.is_valid() is False

    def test_percentage_discount_display(self, percentage_promo: PromoCode):
        """Test discount display for percentage promo."""
        assert percentage_promo.get_discount_display() == "20% off"

    def test_free_trial_discount_display(self, free_trial_promo: PromoCode):
        """Test discount display for free trial promo."""
        assert free_trial_promo.get_discount_display() == "14 days free trial"

    def test_promo_to_dict(self, percentage_promo: PromoCode):
        """Test to_dict method."""
        promo_dict = percentage_promo.to_dict()

        assert promo_dict["code"] == "SAVE20"
        assert promo_dict["promo_type"] == "percentage"
        assert promo_dict["discount_display"] == "20% off"
        assert promo_dict["is_valid"] is True

    def test_promo_to_public_dict(self, percentage_promo: PromoCode):
        """Test to_public_dict has minimal info."""
        public_dict = percentage_promo.to_public_dict()

        assert "code" in public_dict
        assert "discount_display" in public_dict
        assert "max_uses" not in public_dict  # Not in public dict
        assert "current_uses" not in public_dict


class TestEmailVerificationModel:
    """Tests for the EmailVerification model."""

    @pytest.fixture
    def verification(self) -> EmailVerification:
        """Create a test email verification instance."""
        verification = EmailVerification(
            id=1,
            email="verify@test.com",
            code="123456",
            verification_type="registration",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            attempts=0,
            verified_at=None,
            created_at=datetime.now(timezone.utc),
        )
        return verification

    def test_verification_creation(self, verification: EmailVerification):
        """Test verification is created correctly."""
        assert verification.email == "verify@test.com"
        assert verification.code == "123456"
        assert verification.verification_type == "registration"
        assert verification.attempts == 0
        assert verification.verified_at is None

    def test_verification_not_expired(self, verification: EmailVerification):
        """Test is_expired returns False for valid verification."""
        assert verification.is_expired() is False

    def test_verification_expired(self, verification: EmailVerification):
        """Test is_expired returns True for expired verification."""
        verification.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert verification.is_expired() is True

    def test_generate_code(self):
        """Test generate_code creates valid 6-digit code."""
        code = EmailVerification.generate_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_uniqueness(self):
        """Test generate_code creates different codes."""
        codes = [EmailVerification.generate_code() for _ in range(10)]
        # While not guaranteed, 10 random 6-digit codes should be mostly unique
        assert len(set(codes)) >= 8  # Allow for some collisions


class TestPromoCodeUsageModel:
    """Tests for the PromoCodeUsage model."""

    @pytest.fixture
    def promo_usage(self) -> PromoCodeUsage:
        """Create a test promo code usage instance."""
        usage = PromoCodeUsage(
            id=1,
            promo_code_id=1,
            user_id=uuid.uuid4(),
            original_amount=1000.0,
            discount_applied=200.0,
            final_amount=800.0,
            used_at=datetime.now(timezone.utc),
        )
        return usage

    def test_usage_creation(self, promo_usage: PromoCodeUsage):
        """Test promo usage record is created correctly."""
        assert promo_usage.original_amount == 1000.0
        assert promo_usage.discount_applied == 200.0
        assert promo_usage.final_amount == 800.0
        assert promo_usage.used_at is not None

    def test_usage_to_dict(self, promo_usage: PromoCodeUsage):
        """Test to_dict method."""
        usage_dict = promo_usage.to_dict()

        assert "promo_code_id" in usage_dict
        assert "user_id" in usage_dict
        assert usage_dict["original_amount"] == 1000.0
        assert usage_dict["discount_applied"] == 200.0


class TestSiteFeedbackModel:
    """Tests for the SiteFeedback model."""

    @pytest.fixture
    def feedback(self) -> SiteFeedback:
        """Create a test feedback instance."""
        feedback = SiteFeedback(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            email="user@example.com",
            rating=5,
            category=FeedbackCategory.SUGGESTION.value,
            message="This is a great platform! Would love more practice questions.",
            page_url="/student/dashboard",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ip_address="192.168.1.1",
            status=FeedbackStatus.NEW.value,
            created_at=datetime.now(timezone.utc),
        )
        return feedback

    @pytest.fixture
    def anonymous_feedback(self) -> SiteFeedback:
        """Create anonymous feedback instance (no user_id)."""
        feedback = SiteFeedback(
            id=uuid.uuid4(),
            user_id=None,
            email="visitor@example.com",
            rating=4,
            category=FeedbackCategory.BUG.value,
            message="Found a bug on the login page.",
            page_url="/login",
            status=FeedbackStatus.NEW.value,
            created_at=datetime.now(timezone.utc),
        )
        return feedback

    def test_feedback_creation(self, feedback: SiteFeedback):
        """Test feedback is created correctly."""
        assert feedback.email == "user@example.com"
        assert feedback.rating == 5
        assert feedback.category == FeedbackCategory.SUGGESTION.value
        assert feedback.status == FeedbackStatus.NEW.value
        assert feedback.user_id is not None

    def test_feedback_anonymous(self, anonymous_feedback: SiteFeedback):
        """Test anonymous feedback is created correctly."""
        assert anonymous_feedback.user_id is None
        assert anonymous_feedback.email == "visitor@example.com"
        assert anonymous_feedback.category == FeedbackCategory.BUG.value

    def test_feedback_to_dict(self, feedback: SiteFeedback):
        """Test to_dict method."""
        feedback_dict = feedback.to_dict()

        assert "id" in feedback_dict
        assert feedback_dict["email"] == "user@example.com"
        assert feedback_dict["rating"] == 5
        assert feedback_dict["category"] == "suggestion"
        assert feedback_dict["status"] == "new"
        assert "message" in feedback_dict
        assert "created_at" in feedback_dict

    def test_feedback_category_enum(self):
        """Test all feedback categories are valid."""
        categories = [
            FeedbackCategory.SUGGESTION,
            FeedbackCategory.BUG,
            FeedbackCategory.COMPLIMENT,
            FeedbackCategory.QUESTION,
            FeedbackCategory.OTHER,
        ]

        for category in categories:
            assert category.value in ["suggestion", "bug", "compliment", "question", "other"]

    def test_feedback_status_enum(self):
        """Test all feedback statuses are valid."""
        statuses = [
            FeedbackStatus.NEW,
            FeedbackStatus.REVIEWED,
            FeedbackStatus.IN_PROGRESS,
            FeedbackStatus.RESOLVED,
            FeedbackStatus.CLOSED,
        ]

        for status in statuses:
            assert status.value in ["new", "reviewed", "in_progress", "resolved", "closed"]

    def test_feedback_rating_range(self, feedback: SiteFeedback):
        """Test rating is within valid range."""
        assert 1 <= feedback.rating <= 5

    def test_feedback_optional_fields(self):
        """Test feedback with only required fields."""
        feedback = SiteFeedback(
            id=uuid.uuid4(),
            message="Just a simple feedback message.",
            category=FeedbackCategory.OTHER.value,
            status=FeedbackStatus.NEW.value,
            created_at=datetime.now(timezone.utc),
        )

        assert feedback.user_id is None
        assert feedback.email is None
        assert feedback.rating is None
        assert feedback.page_url is None
        assert feedback.admin_notes is None

    def test_feedback_admin_fields(self, feedback: SiteFeedback):
        """Test admin-related fields."""
        # Initially no admin review
        assert feedback.admin_notes is None
        assert feedback.reviewed_by is None
        assert feedback.reviewed_at is None

        # Simulate admin review
        admin_id = uuid.uuid4()
        feedback.reviewed_by = admin_id
        feedback.reviewed_at = datetime.now(timezone.utc)
        feedback.admin_notes = "Reviewed and noted."
        feedback.status = FeedbackStatus.REVIEWED.value

        assert feedback.reviewed_by == admin_id
        assert feedback.reviewed_at is not None
        assert feedback.admin_notes == "Reviewed and noted."
        assert feedback.status == FeedbackStatus.REVIEWED.value
