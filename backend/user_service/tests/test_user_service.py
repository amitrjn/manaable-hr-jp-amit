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
    from main import app, User, UserCreate, UserUpdate, ManagerMemberRelation

client = TestClient(app)

# Test data
def generate_unique_email(prefix="test"):
    """Generate a unique email for testing."""
    import time
    return f"{prefix}_{int(time.time())}@example.com"

def get_test_user_data(role="MEMBER", email=None):
    """Get test user data with unique email."""
    return {
        "email": email or generate_unique_email(),
        "first_name": "Test",
        "last_name": "User",
        "role": role
    }

def get_fresh_test_data():
    """Get fresh test data for each test to avoid conflicts."""
    return {
        "user": get_test_user_data(),
        "manager": get_test_user_data("MANAGER", generate_unique_email("manager"))
    }

# Initialize test data (will be refreshed in each test)
test_data = get_fresh_test_data()

def test_create_user():
    test_data = get_fresh_test_data()
    response = client.post("/users", json=test_data["user"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["first_name"] == test_user_data["first_name"]
    assert data["last_name"] == test_user_data["last_name"]
    assert data["role"] == test_user_data["role"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_user_invalid_role():
    test_data = get_fresh_test_data()
    invalid_user_data = test_data["user"].copy()
    invalid_user_data["role"] = "INVALID_ROLE"
    response = client.post("/users", json=invalid_user_data)
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "email" in data[0]
    assert "role" in data[0]

def test_update_user():
    # Create a user first
    create_response = client.post("/users", json=test_user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]
    
    # Update user data
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    assert data["id"] == user_id  # Verify ID is preserved

def test_update_user_not_found():
    response = client.put("/users/non-existent-id", json={"first_name": "Test"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_get_user_team():
    # Use unique email for manager
    manager_data = get_test_user_data("MANAGER", generate_unique_email("manager"))
    manager_response = client.post("/users", json=manager_data)
    assert manager_response.status_code == 200
    manager_id = manager_response.json()["id"]
    
    # Create a member with unique email
    member_data = get_test_user_data(email=generate_unique_email("team_member"))
    member_response = client.post("/users", json=member_data)
    assert member_response.status_code == 200
    member_id = member_response.json()["id"]
    
    # Assign member to manager
    relation_data = {
        "manager_id": manager_id,
        "member_id": member_id
    }
    assign_response = client.post("/users/manager-assignment", json=relation_data)
    assert assign_response.status_code == 200
    
    # Get team members
    response = client.get(f"/users/{manager_id}/team")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_team_not_manager():
    test_data = get_fresh_test_data()
    # Create a regular user
    user_response = client.post("/users", json=test_data["user"])
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]
    
    # Try to get team as non-manager
    response = client.get(f"/users/{user_id}/team")
    assert response.status_code == 403
    assert "User is not a manager" in response.json()["detail"]

def test_assign_manager():
    # Use unique emails for both manager and member
    manager_data = get_test_user_data("MANAGER", generate_unique_email("manager"))
    manager_response = client.post("/users", json=manager_data)
    assert manager_response.status_code == 200
    manager_id = manager_response.json()["id"]
    
    # Create a member with unique email
    member_data = {
        "email": "member1@example.com",
        "first_name": "Test",
        "last_name": "Member",
        "role": "MEMBER"
    }
    member_response = client.post("/users", json=member_data)
    assert member_response.status_code == 200
    member_id = member_response.json()["id"]
    
    # Assign member to manager
    relation_data = {
        "manager_id": manager_id,
        "member_id": member_id
    }
    response = client.post("/users/manager-assignment", json=relation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == relation_data["manager_id"]
    assert data["member_id"] == relation_data["member_id"]
    assert "created_at" in data

def test_assign_manager_invalid_manager():
    # Use unique emails for both users
    user_data = get_test_user_data(email=generate_unique_email("user"))
    user_response = client.post("/users", json=user_data)
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]
    
    # Create another user with different email
    member_data = get_test_user_data(email=generate_unique_email("member2"))
    member_response = client.post("/users", json=member_data)
    assert member_response.status_code == 200
    member_id = member_response.json()["id"]
    
    # Try to assign regular user as manager
    relation_data = {
        "manager_id": user_id,
        "member_id": member_id
    }
    response = client.post("/users/manager-assignment", json=relation_data)
    assert response.status_code == 400
    assert "does not have MANAGER role" in response.json()["detail"]
    
    # Test with non-existent manager
    relation_data["manager_id"] = "non-existent-id"
    response = client.post("/users/manager-assignment", json=relation_data)
    assert response.status_code == 404
    assert "Manager or member not found" in response.json()["detail"]
