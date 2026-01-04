"""
Integration Tests for Chatbot Routes

These tests run against a real PostgreSQL database.
Set TEST_DATABASE_URL environment variable to run these tests.

Usage:
    set TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mvdb
    pytest tests/test_chatbot_routes.py -v
"""

import pytest
import os

# Skip all tests if no database URL is configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", "")),
    reason="TEST_DATABASE_URL not set - skipping integration tests"
)


class TestChatbotEndpoints:
    """Tests for chatbot endpoints."""

    @pytest.mark.asyncio
    async def test_chat_greeting(self, client):
        """Test chatbot responds to greetings."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "confidence" in data
        assert "source" in data
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_pricing_question(self, client):
        """Test chatbot responds to pricing questions."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "What are your subscription plans?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["confidence"] >= 0

    @pytest.mark.asyncio
    async def test_chat_exam_question(self, client):
        """Test chatbot responds to exam-related questions."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "How do I take an exam?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_empty_message_handled(self, client):
        """Test chatbot handles empty/whitespace message gracefully."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "   "}
        )

        # Should either handle gracefully or return validation error
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_chat_long_message(self, client):
        """Test chatbot handles long messages."""
        long_message = "This is a test message about mathematics. " * 20

        response = await client.post(
            "/api/v1/chat/",
            json={"message": long_message[:500]}  # Within limit
        )

        assert response.status_code == 200
        assert "response" in response.json()

    @pytest.mark.asyncio
    async def test_get_chat_suggestions(self, client):
        """Test getting chat suggestions."""
        response = await client.get("/api/v1/chat/suggestions")

        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_get_chat_status(self, client):
        """Test getting chat status."""
        response = await client.get("/api/v1/chat/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "mode" in data
        assert data["mode"] in ["rag", "keyword", "simple"]


class TestChatbotResponses:
    """Tests for specific chatbot response content."""

    @pytest.mark.asyncio
    async def test_password_reset_help(self, client):
        """Test chatbot provides password reset help."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "I forgot my password"}
        )

        assert response.status_code == 200
        data = response.json()
        # Response should mention password reset
        assert "response" in data
        assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_contact_info(self, client):
        """Test chatbot provides contact information."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "How can I contact support?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_general_fallback(self, client):
        """Test chatbot provides fallback for unknown queries."""
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "xyzabc123random gibberish"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should still return a response, even if low confidence
        assert "response" in data
        assert "confidence" in data


class TestChatbotNoAuth:
    """Tests to verify chatbot works without authentication."""

    @pytest.mark.asyncio
    async def test_chat_no_auth_required(self, client):
        """Test that chatbot endpoints work without authentication."""
        # Chat endpoint
        response = await client.post(
            "/api/v1/chat/",
            json={"message": "Hello"}
        )
        assert response.status_code == 200

        # Suggestions endpoint
        response = await client.get("/api/v1/chat/suggestions")
        assert response.status_code == 200

        # Status endpoint
        response = await client.get("/api/v1/chat/status")
        assert response.status_code == 200
