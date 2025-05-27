from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBasic()

# Test credentials
USERS_DB = {
    "admin@test.com": {"password": "admin123", "role": "admin"},
    "viewer@test.com": {"password": "viewer123", "role": "viewer"}
}

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

def authenticate_user(email: str, password: str):
    """Simple authentication function"""
    user_data = USERS_DB.get(email)
    if user_data and user_data["password"] == password:
        return {
            "id": email,
            "email": email,
            "role": user_data["role"]
        }
    return None

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Generate simple token (for testing only)
    token = f"test_token_{user['email']}_{user['role']}"
    
    return LoginResponse(
        token=token,
        user=user
    )

@router.get("/me")
async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
