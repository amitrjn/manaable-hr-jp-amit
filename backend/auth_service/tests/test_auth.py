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

def test_token_endpoint_exists():
    response = client.post("/token")
    # Should return 422 as it requires body parameters
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    # Test with invalid JWT token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
