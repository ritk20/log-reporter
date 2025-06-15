from fastapi import APIRouter, HTTPException, Form, Depends
from pydantic import BaseModel
from datetime import timedelta
from app.api.auth_jwt import create_access_token, create_refresh_token, verify_token, revoke_refresh_token, TokenPair,SECRET_KEY,ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

USERS_DB = {
    "admin@test.com": {"password": "admin123", "role": "admin"},
    "viewer@test.com": {"password": "viewer123", "role": "viewer"}
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
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

    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token, token_id = create_refresh_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh_token: str = Form(...)):
    try:
        payload = verify_token(refresh_token, token_type="refresh")
        token_id = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM]).get("jti")
        
        new_access_token = create_access_token(
            data={"sub": payload["username"], "role": payload["roles"][0]},
            expires_delta=timedelta(minutes=30)
        )
        new_refresh_token, new_token_id = create_refresh_token(
            data={"sub": payload["username"], "role": payload["roles"][0]}
        )
        
        # Revoke old refresh token
        revoke_refresh_token(token_id)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")