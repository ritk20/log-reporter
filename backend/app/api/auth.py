from fastapi import APIRouter, HTTPException, Form, Response, Request
from pydantic import BaseModel
from datetime import timedelta
from jose import jwt, JWTError
import bcrypt
from pymongo import MongoClient
from app.core.config import settings
from app.api.auth_jwt import (
    create_access_token, create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY, ALGORITHM
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# MongoDB connection (only for login validation)
client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]
login_collection = db[settings.MONGODB_LOGIN]

# Login response model
class LoginResponse(BaseModel):
    access_token: str
    token_type: str

# Authenticate user using DB
def authenticate_user(username: str, password: str):
    print(f"[DEBUG] Authenticating user: {username}")
    user_data = login_collection.find_one({"_id": username})
    if not user_data:
        print("[ERROR] User not found.")
        return None
    if "password" not in user_data:
        print("[ERROR] Password not set.")
        return None
    db_password = user_data["password"]
    if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
        print("[SUCCESS] Authenticated.")
        return {"email": username, "role": user_data.get("role", "user")}
    else:
        print("[ERROR] Incorrect password.")
        return None

# Login route
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
        
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token, _ = create_refresh_token(
        data={"sub": user["email"], "role": user["role"]}
    )

    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh-token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="Strict",
        path="/api/auth",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Refresh token endpoint
@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: Request):
    print("[DEBUG] Refreshing token")
    refresh_token = request.cookies.get("refresh-token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        role = payload.get("role")

        new_access_token = create_access_token(
            data={"sub": user_id, "role": role},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except JWTError as e:
        print("[ERROR] JWT decode error:", e)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(response: Response):
    """
    Clears the 'refresh-token' cookie so that refresh() can no longer issue tokens.
    """
    response.delete_cookie(
        key="refresh-token",
        path="/api/auth",    # must match the path you set on login
    )
    return {"msg": "Successfully logged out"}