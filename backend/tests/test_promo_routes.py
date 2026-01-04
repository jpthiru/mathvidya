"""
Integration Tests for Promo Code Routes

These tests run against a real PostgreSQL database.
Set TEST_DATABASE_URL environment variable to run these tests.

Usage:
    set TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mvdb
    pytest tests/test_promo_routes.py -v
"""

import pytest
import os

# Skip all tests if no database URL is configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", "")),
    reason="TEST_DATABASE_URL not set - skipping integration tests"
)


class TestPromoCodeValidation:
    """Tests for promo code validation endpoint.

    Note: Tests that involve database queries have been moved to unit tests
    to avoid async session conflicts in integration tests.
    """
    pass  # Database-dependent validation tests moved to test_models.py


class TestPromoCodeAdminRoutes:
    """Tests for admin promo code management."""

    @pytest.mark.asyncio
    async def test_list_promo_codes_no_auth(self, client):
        """Test listing promo codes without auth fails."""
        response = await client.get("/api/v1/promo/")

        # 401 Unauthorized (no token) or 403 Forbidden
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_promo_no_auth(self, client):
        """Test creating promo code without auth fails."""
        response = await client.post(
            "/api/v1/promo/",
            json={
                "code": "TESTCODE",
                "promo_type": "percentage",
                "discount_percentage": 10.0
            }
        )

        # 401 Unauthorized (no token) or 403 Forbidden
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_promo_invalid_token(self, client):
        """Test creating promo code with invalid token fails."""
        response = await client.post(
            "/api/v1/promo/",
            json={
                "code": "TESTCODE",
                "promo_type": "percentage",
                "discount_percentage": 10.0
            },
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401
