"""
Test FastAPI endpoints

Simple script to test authentication and basic endpoints.
"""

import asyncio
import httpx


async def test_api():
    """Test FastAPI endpoints"""

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        print("Testing FastAPI Endpoints...\n")

        # Test 1: Root endpoint
        print("1. Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test 2: Health check
        print("2. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test 3: Database health
        print("3. Testing database health...")
        response = await client.get(f"{base_url}/health/db")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test 4: Register a new user
        print("4. Testing user registration...")
        register_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "role": "student",
            "first_name": "Test",
            "last_name": "User",
            "student_class": "XII"
        }
        response = await client.post(f"{base_url}/api/v1/auth/register", json=register_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   Response: User created successfully")
            print(f"   User ID: {response.json().get('user_id')}\n")
        else:
            print(f"   Response: {response.json()}\n")

        # Test 5: Login with the registered user
        print("5. Testing user login...")
        login_data = {
            "email": "admin@mathvidya.com",  # Use existing admin user
            "password": "admin123"
        }
        response = await client.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user")
            print(f"   Login successful!")
            print(f"   User: {user.get('full_name')} ({user.get('role')})")
            print(f"   Token: {token[:50]}...\n")

            # Test 6: Get current user info with token
            print("6. Testing /auth/me with valid token...")
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{base_url}/api/v1/auth/me", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_info = response.json()
                print(f"   User Info: {user_info.get('full_name')} - {user_info.get('email')}\n")
            else:
                print(f"   Response: {response.json()}\n")

            # Test 7: Test protected endpoint without token
            print("7. Testing /auth/me without token...")
            response = await client.get(f"{base_url}/api/v1/auth/me")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}\n")

        else:
            print(f"   Login failed: {response.json()}\n")

        print("All tests completed!")


if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000\n")
    print("Start it with: uvicorn main:app --reload\n")
    input("Press Enter to start tests...")

    asyncio.run(test_api())
