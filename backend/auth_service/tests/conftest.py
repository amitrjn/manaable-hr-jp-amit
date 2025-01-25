import pytest
import os
from unittest.mock import patch, MagicMock

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
    mock_client.auth = mock_auth
    
    with patch('main.supabase', mock_client):
        yield mock_client

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test."""
    os.environ["SUPABASE_URL"] = "https://example.com"
    os.environ["SUPABASE_KEY"] = "dummy-key-for-testing"
    os.environ["JWT_SECRET"] = "test-secret-key"
