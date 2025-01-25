import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock auth operations
    mock_auth = MagicMock()
    mock_auth.get_user.return_value = MagicMock(
        email="test@example.com",
        user_metadata={
            "first_name": "Test",
            "last_name": "User",
            "role": "MEMBER"
        }
    )
    def sign_in_with_password_side_effect(credentials):
        if credentials["email"] == "test@example.com" and credentials["password"] == "testpass":
            return MagicMock(
                user=MagicMock(
                    id="test-user-id",
                    email="test@example.com",
                    user_metadata={
                        "first_name": "Test",
                        "last_name": "User",
                        "role": "MEMBER"
                    }
                )
            )
        return MagicMock(user=None)
    
    mock_auth.sign_in_with_password.side_effect = sign_in_with_password_side_effect
    mock_client.auth = mock_auth
    
    # Mock table operations
    mock_table = MagicMock()
    mock_table.select.return_value.execute.return_value.data = []
    mock_table.insert.return_value.execute.return_value.data = [{
        "id": "test-id",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "MEMBER",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }]
    mock_client.table.return_value = mock_table
    
    with patch('main.get_supabase_client', return_value=mock_client):
        yield mock_client

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test."""
    os.environ["SUPABASE_URL"] = "https://example.com"
    os.environ["SUPABASE_KEY"] = "dummy-key-for-testing"
    os.environ["JWT_SECRET"] = "test-secret-key"
