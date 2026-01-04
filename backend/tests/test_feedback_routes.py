"""
Integration Tests for Site Feedback Routes

These tests run against a real PostgreSQL database.
Set TEST_DATABASE_URL environment variable to run these tests.

Usage:
    set TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mvdb
    pytest tests/test_feedback_routes.py -v

Note: Some tests for feedback submission are skipped because the slowapi rate limiter
requires a proper starlette Request object which is not available in test client.
Tests focus on validation and admin route security.
"""

import pytest
import os

# Skip all tests if no database URL is configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", "")),
    reason="TEST_DATABASE_URL not set - skipping integration tests"
)


class TestFeedbackValidation:
    """Tests for feedback input validation.

    Note: These tests check that invalid input is rejected at the validation layer
    before hitting the rate limiter.
    """

    @pytest.mark.asyncio
    async def test_submit_feedback_message_too_short(self, client):
        """Test feedback with message shorter than minimum length fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "message": "Short"  # Less than 10 characters
            }
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_empty_message(self, client):
        """Test feedback with empty message fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "message": ""
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_missing_message(self, client):
        """Test feedback without message field fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "rating": 5,
                "type": "suggestion"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_rating_too_high(self, client):
        """Test feedback with rating > 5 fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "rating": 6,
                "message": "This is a valid feedback message."
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_rating_too_low(self, client):
        """Test feedback with rating < 1 fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "rating": 0,
                "message": "This is a valid feedback message."
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_negative_rating(self, client):
        """Test feedback with negative rating fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "rating": -1,
                "message": "This is a valid feedback message."
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_email(self, client):
        """Test feedback with invalid email format fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "message": "This is a valid feedback message.",
                "email": "not-a-valid-email"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_email_no_domain(self, client):
        """Test feedback with email missing domain fails."""
        response = await client.post(
            "/api/v1/feedback/",
            json={
                "message": "This is a valid feedback message.",
                "email": "user@"
            }
        )

        assert response.status_code == 422


class TestFeedbackAdminRoutesNoAuth:
    """Tests for admin feedback endpoints without authentication."""

    @pytest.mark.asyncio
    async def test_list_feedback_no_auth(self, client):
        """Test listing feedback without authentication fails."""
        response = await client.get("/api/v1/feedback/")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_list_feedback_invalid_token(self, client):
        """Test listing feedback with invalid token fails."""
        response = await client.get(
            "/api/v1/feedback/",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_feedback_stats_no_auth(self, client):
        """Test getting feedback stats without authentication fails."""
        response = await client.get("/api/v1/feedback/stats")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_feedback_stats_invalid_token(self, client):
        """Test getting feedback stats with invalid token fails."""
        response = await client.get(
            "/api/v1/feedback/stats",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_feedback_no_auth(self, client):
        """Test updating feedback without authentication fails."""
        response = await client.patch(
            "/api/v1/feedback/00000000-0000-0000-0000-000000000001",
            json={"status": "reviewed"}
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_feedback_invalid_token(self, client):
        """Test updating feedback with invalid token fails."""
        response = await client.patch(
            "/api/v1/feedback/00000000-0000-0000-0000-000000000001",
            json={"status": "reviewed"},
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_feedback_no_auth(self, client):
        """Test deleting feedback without authentication fails."""
        response = await client.delete(
            "/api/v1/feedback/00000000-0000-0000-0000-000000000001"
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_feedback_invalid_token(self, client):
        """Test deleting feedback with invalid token fails."""
        response = await client.delete(
            "/api/v1/feedback/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_feedback_malformed_auth_header(self, client):
        """Test listing feedback with malformed auth header fails."""
        response = await client.get(
            "/api/v1/feedback/",
            headers={"Authorization": "NotBearer sometoken"}
        )

        assert response.status_code in [401, 403]
