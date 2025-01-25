from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not all([url, key]):
        raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY")

    return create_client(url, key)

# Initialize client lazily to allow mocking in tests
supabase: Client = None

app = FastAPI(title="User Service")

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str = "MEMBER"

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ManagerMemberRelation(BaseModel):
    manager_id: str
    member_id: str

@app.get("/users", response_model=List[User])
async def get_users():
    try:
        response = supabase.table("users").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    try:
        # Validate role
        if user.role not in ["MEMBER", "MANAGER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: MEMBER, MANAGER, ADMIN"
            )
        
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", user.email).execute()
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        response = supabase.table("users").insert({
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }).execute()
        
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserUpdate):
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare update data
        update_data = {}
        if user.first_name is not None:
            update_data["first_name"] = user.first_name
        if user.last_name is not None:
            update_data["last_name"] = user.last_name
        if user.role is not None:
            if user.role not in ["MEMBER", "MANAGER", "ADMIN"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role. Must be one of: MEMBER, MANAGER, ADMIN"
                )
            update_data["role"] = user.role
        
        # Update user
        response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/users/{user_id}/team", response_model=List[User])
async def get_user_team(user_id: str):
    try:
        # Check if user exists and is a manager
        user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if user.data[0]["role"] != "MANAGER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a manager"
            )
        
        # Get team members
        team = supabase.table("manager_member_relations") \
            .select("users!member_id(*)") \
            .eq("manager_id", user_id) \
            .execute()
        
        return [member["users"] for member in team.data]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/users/manager-assignment", response_model=ManagerMemberRelation)
async def assign_manager(relation: ManagerMemberRelation):
    try:
        # Check if both users exist
        manager = supabase.table("users").select("*").eq("id", relation.manager_id).execute()
        member = supabase.table("users").select("*").eq("id", relation.member_id).execute()
        
        if not manager.data or not member.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager or member not found"
            )
        
        # Verify manager role
        if manager.data[0]["role"] != "MANAGER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified manager user does not have MANAGER role"
            )
        
        # Check if assignment already exists
        existing = supabase.table("manager_member_relations") \
            .select("*") \
            .eq("manager_id", relation.manager_id) \
            .eq("member_id", relation.member_id) \
            .execute()
            
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This manager-member relationship already exists"
            )
        
        # Create assignment
        response = supabase.table("manager_member_relations").insert({
            "manager_id": relation.manager_id,
            "member_id": relation.member_id
        }).execute()
        
        return response.data[0]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
