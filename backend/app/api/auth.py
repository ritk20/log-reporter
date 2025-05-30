from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from datetime import timedelta
from app.api.auth_jwt import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

USERS_DB = {
    "admin@test.com": {"password": "admin123", "role": "admin"},
    "viewer@test.com": {"password": "viewer123", "role": "viewer"}
}

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

def authenticate_user(username: str, password: str):
    user_data = USERS_DB.get(username)
    if user_data and user_data["password"] == password:
        return {"email": username, "role": user_data["role"]}
    return None

@router.post("/login", response_model=LoginResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": token, "token_type": "bearer"}
