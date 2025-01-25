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
test_user_data = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "role": "MEMBER"
}

test_manager_data = {
    "email": "manager@example.com",
    "first_name": "Test",
    "last_name": "Manager",
    "role": "MANAGER"
}

def test_create_user():
    response = client.post("/users", json=test_user_data)
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
    invalid_user_data = test_user_data.copy()
    invalid_user_data["role"] = "INVALID_ROLE"
    response = client.post("/users", json=invalid_user_data)
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]

def test_get_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_user():
    # First create a user
    create_response = client.post("/users", json=test_user_data)
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

def test_update_user_not_found():
    response = client.put("/users/non-existent-id", json={"first_name": "Test"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_get_user_team():
    # First create a manager
    manager_response = client.post("/users", json=test_manager_data)
    manager_id = manager_response.json()["id"]
    
    response = client.get(f"/users/{manager_id}/team")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user_team_not_manager():
    # Create a regular user
    user_response = client.post("/users", json=test_user_data)
    user_id = user_response.json()["id"]
    
    response = client.get(f"/users/{user_id}/team")
    assert response.status_code == 403
    assert "User is not a manager" in response.json()["detail"]

def test_assign_manager():
    # Create a manager and a member
    manager_response = client.post("/users", json=test_manager_data)
    manager_id = manager_response.json()["id"]
    
    member_response = client.post("/users", json=test_user_data)
    member_id = member_response.json()["id"]
    
    # Assign manager
    relation_data = {
        "manager_id": manager_id,
        "member_id": member_id
    }
    response = client.post("/users/manager-assignment", json=relation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == manager_id
    assert data["member_id"] == member_id

def test_assign_manager_invalid_manager():
    # Create two regular users
    user1_response = client.post("/users", json=test_user_data)
    user1_id = user1_response.json()["id"]
    
    user2_response = client.post("/users", json=test_user_data)
    user2_id = user2_response.json()["id"]
    
    # Try to assign non-manager as manager
    relation_data = {
        "manager_id": user1_id,
        "member_id": user2_id
    }
    response = client.post("/users/manager-assignment", json=relation_data)
    assert response.status_code == 400
    assert "does not have MANAGER role" in response.json()["detail"]
