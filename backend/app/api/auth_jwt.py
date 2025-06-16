from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import uuid
from app.core.config import settings

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# In-memory storage for refresh tokens (replace with database in production)
REFRESH_TOKEN_STORE = {}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": token_id})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    REFRESH_TOKEN_STORE[token_id] = {"email": data["sub"], "exp": expire}
    return token, token_id

def verify_token(token: str = Depends(oauth2_scheme), token_type: str = "access"):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None or payload.get("type") != token_type:
            raise credentials_exception
        if token_type == "refresh":
            token_id = payload.get("jti")
            if token_id not in REFRESH_TOKEN_STORE or REFRESH_TOKEN_STORE[token_id]["email"] != email:
                raise credentials_exception
        return {
            "username": email,
            "roles": [payload.get("role")],
            "auth_method": "bearer",
            "user_id": payload.get("user_id", "unknown")
        }
    except JWTError:
        raise credentials_exception

def revoke_refresh_token(token_id: str):
    REFRESH_TOKEN_STORE.pop(token_id, None)