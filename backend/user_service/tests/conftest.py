import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock table operations
    # Create base test data
    test_user = {
        "id": "test-id",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "MEMBER",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    test_manager = {
        "id": "manager-id",
        "email": "manager@example.com",
        "first_name": "Test",
        "last_name": "Manager",
        "role": "MANAGER",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Configure mock table operations
    mock_table = MagicMock()
    
    # Configure select operations for different scenarios
    mock_select = MagicMock()
    def select_side_effect(*args, **kwargs):
        mock_result = MagicMock()
        # Default behavior for listing users
        mock_result.execute.return_value.data = [test_user]
        # For user existence check in create_user
        mock_result.eq.return_value.execute.return_value.data = []
        return mock_result
    mock_table.select.side_effect = select_side_effect
    
    # Configure insert operations
    mock_insert = MagicMock()
    def insert_side_effect(data):
        mock_result = MagicMock()
        inserted_user = {
            "id": "test-id",
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "role": data["role"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        mock_result.execute.return_value.data = [inserted_user]
        return mock_result
    mock_table.insert.side_effect = insert_side_effect
    
    # Configure update operations
    mock_update = MagicMock()
    def update_side_effect(data):
        mock_result = MagicMock()
        updated_user = dict(test_user)
        updated_user.update(data)
        mock_result.eq.return_value.execute.return_value.data = [updated_user]
        return mock_result
    mock_table.update.side_effect = update_side_effect
    
    # Configure manager-specific operations
    def table_select_side_effect(table_name):
        if table_name == "users":
            return mock_table
        elif table_name == "manager_member_relations":
            mock_relations = MagicMock()
            mock_relations.select.return_value.eq.return_value.execute.return_value.data = []
            return mock_relations
        return mock_table
    
    mock_client.table.side_effect = table_select_side_effect
    
    with patch('main.get_supabase_client', return_value=mock_client):
        yield mock_client

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test."""
    os.environ["SUPABASE_URL"] = "https://example.com"
    os.environ["SUPABASE_KEY"] = "dummy-key-for-testing"
    os.environ["JWT_SECRET"] = "test-secret-key"  # Add JWT secret for consistency
