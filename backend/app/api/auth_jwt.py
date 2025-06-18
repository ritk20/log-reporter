from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.database.database import get_refresh_token_collection
import logging
import uuid
from app.core.config import settings

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    logger.info(f"Creating access token for {data.get('sub')}")
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_id = str(uuid.uuid4())

    email = data.get("sub")
    if not email:
        raise ValueError("Missing 'sub' in refresh token payload")

    to_encode.update({"exp": expire, "type": "refresh", "jti": token_id})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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

        # if token_type == "refresh":
        #     token_id = payload.get("jti")
        #     coll = get_refresh_token_collection()
        #     token_doc = coll.find_one({"jti": token_id, "email": email})
        #     if not token_doc:
        #         raise credentials_exception
        #     if datetime.now(timezone.utc) > token_doc["exp"]:
        #         raise credentials_exception

        return {
            "username": email,
            "roles": [payload.get("role")],
            "auth_method": "bearer"
        }
    except JWTError:
        logger.warning(f"JWT error during token verification for token_type={token_type}")
        raise credentials_exception

# def revoke_refresh_token(token_id: str):
#     coll = get_refresh_token_collection()
#     result = coll.delete_one({"jti": token_id})
#     if result.deleted_count:
#         logger.info(f"Revoked refresh token with jti {token_id} from MongoDB")
#     else:
#         logger.warning(f"Attempt to revoke nonexistent refresh token jti {token_id}")
