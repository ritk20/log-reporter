from fastapi import APIRouter, HTTPException, Form, Response, Request
from pydantic import BaseModel
from datetime import timedelta
from app.api.auth_jwt import create_access_token, create_refresh_token, verify_token, TokenPair
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from app.core.config import settings
from pymongo import MongoClient
import bcrypt

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
collection = db[settings.MONGODB_LOGIN] 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

def authenticate_user(username: str, password: str):
    user_data = collection.find_one({"_id": username})  

    if not user_data:
        print("[ERROR] User not found in DB.")
        return None

    print(f"[DEBUG] Found user: {user_data['_id']}, Role: {user_data.get('role')}")

    if "password" not in user_data:
        print("[ERROR] Password field missing in DB entry.")
        return None

    db_password = user_data["password"]
    print(f"[DEBUG] Comparing password...")

    if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
        print("[SUCCESS] Password match.")
        return {"email": username, "role": user_data.get("role", "user")}
    else:
        print("[ERROR] Password mismatch.")
        return None

@router.post("/login", response_model=LoginResponse)
async def login(    
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    # Set HTTP-only cookie for refresh token
    response.set_cookie(
        key="refresh-token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True with HTTPS
        samesite="strict",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/"
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh-token")
    if not refresh_token:
        print("[ERROR] No refresh token found in cookies.")
        raise HTTPException(status_code=401, detail="Refresh token not found")

    try:
        payload = verify_token(refresh_token, token_type="refresh")
        
        new_access_token = create_access_token(
            data={"sub": payload["username"], "role": payload["roles"][0]},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        new_refresh_token = create_refresh_token(
            data={"sub": payload["username"], "role": payload["roles"][0]}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")