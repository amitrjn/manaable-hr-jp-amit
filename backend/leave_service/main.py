from fastapi import FastAPI, Depends, HTTPException
from typing import List
from datetime import date
from pydantic import BaseModel
from ..auth_service.config import supabase

app = FastAPI(title="Leave Service")

class LeaveRequest(BaseModel):
    user_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str = None

class LeaveBalance(BaseModel):
    user_id: str
    vacation_balance: float
    sick_balance: float
    last_vacation_accrual_date: date
    last_sick_accrual_date: date

@app.post("/requests")
async def create_leave_request(request: LeaveRequest):
    # Implementation will be added in the leave management phase
    pass

@app.get("/balance/{user_id}")
async def get_leave_balance(user_id: str):
    # Implementation will be added in the leave management phase
    pass
