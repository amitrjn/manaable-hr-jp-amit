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
    
    # Configure select operations
    mock_select = MagicMock()
    mock_select.execute.return_value.data = [test_user]
    mock_select.eq.return_value.execute.return_value.data = [test_user]
    mock_table.select.return_value = mock_select
    
    # Configure insert operations
    mock_insert = MagicMock()
    mock_insert.execute.return_value.data = [test_user]
    mock_table.insert.return_value = mock_insert
    
    # Configure update operations
    mock_update = MagicMock()
    updated_user = dict(test_user)
    updated_user.update({"first_name": "Updated", "last_name": "Name"})
    mock_update.eq.return_value.execute.return_value.data = [updated_user]
    mock_table.update.return_value = mock_update
    
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
