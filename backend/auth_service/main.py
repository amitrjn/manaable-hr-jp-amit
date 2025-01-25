from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    global supabase
    if supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        jwt_secret = os.getenv("JWT_SECRET")

        if not all([url, key, jwt_secret]):
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY, JWT_SECRET")

        supabase = create_client(url, key)
    return supabase

# Initialize client lazily to allow mocking in tests
supabase: Client = None

app = FastAPI(title="Auth Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        jwt_secret = os.getenv("JWT_SECRET", "test-secret-key")  # Use default for tests
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        
        # Get user from Supabase
        client = get_supabase_client()
        user = client.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return User(
            email=user.email,
            first_name=user.user_metadata.get("first_name", ""),
            last_name=user.user_metadata.get("last_name", ""),
            role=user.user_metadata.get("role", "MEMBER")
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        client = get_supabase_client()
        response = client.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = jwt.encode(
            {
                "sub": response.user.id,
                "email": form_data.username,
                "exp": datetime.utcnow() + timedelta(minutes=30)
            },
            os.getenv("JWT_SECRET", ""),
            algorithm="HS256"
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
