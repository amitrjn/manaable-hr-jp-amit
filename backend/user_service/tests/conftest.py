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
    
    # Initialize mock data store with test users
    mock_data = {
        "users": [test_user.copy(), test_manager.copy()],  # Start with test users
        "relations": []
    }
    user_id_counter = 2  # Start after initial test users
    
    # Configure mock table operations
    mock_table = MagicMock()
    
    def select_side_effect(*args, **kwargs):
        mock_select = MagicMock()
        
        def eq_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            if args[0] == "email":
                # Check if email exists in mock data
                matching_users = [u for u in mock_data["users"] if u["email"] == args[1]]
                mock_eq.execute.return_value.data = matching_users
            elif args[0] == "id":
                if args[1] == "non-existent-id":
                    mock_eq.execute.return_value.data = []
                else:
                    # Return user if it exists in mock data
                    matching_users = [u for u in mock_data["users"] if u["id"] == args[1]]
                    mock_eq.execute.return_value.data = matching_users
            elif args[0] == "manager_id":
                # Return team members for this manager
                team_relations = [r for r in mock_data["relations"] if r["manager_id"] == args[1]]
                result_data = []
                for relation in team_relations:
                    member = next((u for u in mock_data["users"] if u["id"] == relation["member_id"]), None)
                    if member:
                        result_data.append({
                            **relation,
                            "users": member
                        })
                mock_eq.execute.return_value.data = result_data
            return mock_eq
        
        mock_select.eq = eq_side_effect
        
        # If no args, return all users
        if not args and not kwargs:
            mock_select.execute.return_value.data = mock_data["users"]
        return mock_select
    mock_table.select = select_side_effect
    
    # Configure insert operations
    def insert_side_effect(data):
        nonlocal user_id_counter, mock_data
        mock_insert = MagicMock()
        
        # Generate unique ID for new user or relation
        if "email" in data:  # This is a user
            user_id_counter += 1
            new_id = f"user-{user_id_counter}"
            now = datetime.now().isoformat()
            inserted_data = {
                "id": new_id,
                **data,
                "created_at": now,
                "updated_at": now
            }
            mock_data["users"].append(inserted_data)
        else:  # This is a manager-member relation
            relation_id = f"relation-{len(mock_data['relations']) + 1}"
            now = datetime.now().isoformat()
            inserted_data = {
                "id": relation_id,
                **data,
                "created_at": now
            }
            mock_data["relations"].append(inserted_data)
            
        mock_insert.execute.return_value.data = [inserted_data]
        return mock_insert
    mock_table.insert = insert_side_effect
    
    # Configure update operations
    def update_side_effect(data):
        mock_update = MagicMock()
        def eq_side_effect(*args, **kwargs):
            mock_eq = MagicMock()
            user_id = args[1]
            matching_users = [u for u in mock_data["users"] if u["id"] == user_id]
            if matching_users:
                now = datetime.now().isoformat()
                updated_data = {
                    **matching_users[0],
                    **data,
                    "updated_at": now
                }
                # Update user in mock data
                for i, user in enumerate(mock_data["users"]):
                    if user["id"] == user_id:
                        mock_data["users"][i] = updated_data
                        break
                mock_eq.execute.return_value.data = [updated_data]
            else:
                mock_eq.execute.return_value.data = []
            return mock_eq
        mock_update.eq = eq_side_effect
        return mock_update
    mock_table.update = update_side_effect
    
    # Configure manager-specific operations
    def table_side_effect(table_name):
        if table_name == "users":
            return mock_table
        elif table_name == "manager_member_relations":
            mock_relations = MagicMock()
            
            def relations_select(*args, **kwargs):
                mock_select = MagicMock()
                
                def relations_eq(*args, **kwargs):
                    mock_eq = MagicMock()
                    if args[0] == "manager_id":
                        team_relations = [r for r in mock_data["relations"] if r["manager_id"] == args[1]]
                        result_data = []
                        for relation in team_relations:
                            member = next((u for u in mock_data["users"] if u["id"] == relation["member_id"]), None)
                            if member:
                                result_data.append({
                                    **relation,
                                    "users": member
                                })
                        mock_eq.execute.return_value.data = result_data
                    else:
                        mock_eq.execute.return_value.data = []
                    return mock_eq
                
                mock_select.eq = relations_eq
                mock_select.execute.return_value.data = mock_data["relations"]
                return mock_select
            
            def relations_insert(data):
                mock_insert = MagicMock()
                relation_id = f"relation-{len(mock_data['relations']) + 1}"
                now = datetime.now().isoformat()
                relation_data = {
                    "id": relation_id,
                    **data,
                    "created_at": now
                }
                mock_data["relations"].append(relation_data)
                mock_insert.execute.return_value.data = [relation_data]
                return mock_insert
            
            mock_relations.select = relations_select
            mock_relations.insert = relations_insert
            return mock_relations
        
        return mock_table
    
    mock_client.table = table_side_effect
    
    with patch('main.get_supabase_client', return_value=mock_client):
        yield mock_client

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test."""
    os.environ["SUPABASE_URL"] = "https://example.com"
    os.environ["SUPABASE_KEY"] = "dummy-key-for-testing"
    os.environ["JWT_SECRET"] = "test-secret-key"  # Add JWT secret for consistency
