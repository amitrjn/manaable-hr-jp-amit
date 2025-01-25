import pytest
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the service root directory to Python path
service_root = Path(__file__).parent.parent
sys.path.append(str(service_root))

with patch('main.get_supabase_client'):
    from main import app, User

client = TestClient(app)

def test_read_users_me_unauthorized():
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_token_endpoint():
    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_token_endpoint_invalid_credentials():
    response = client.post(
        "/token",
        data={
            "username": "invalid@example.com",
            "password": "wrongpass",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    # Test with invalid JWT token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.asyncio
async def test_get_current_user_success():
    # First get a valid token
    token_response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert token_response.status_code == 200
    token_data = token_response.json()
    
    # Use token to get current user
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "test@example.com"
    assert user_data["first_name"] == "Test"
    assert user_data["last_name"] == "User"
    assert user_data["role"] == "MEMBER"
