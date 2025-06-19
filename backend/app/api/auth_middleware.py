from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from app.api.auth_jwt import SECRET_KEY, ALGORITHM

class JWTMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks for a valid JWT access token on each protected request.
    If valid, attaches the user info to request.state.user.
    """
    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)
        # Define paths to skip (e.g., login, refresh, docs)
        skip_paths = [
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/logout",
    "/docs",
    "/openapi.json"
]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        # Try to read Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            # Attach user info to request
            request.state.user = {"email": payload.get("sub"), "role": payload.get("role")}

        except JWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        # Proceed to route handler
        response = await call_next(request)
        return response

# Usage in your main FastAPI app:
#
# from fastapi import FastAPI
# from app.api.auth_middleware import JWTMiddleware
#
# app = FastAPI()
# app.add_middleware(JWTMiddleware)
#
# @app.get("/protected")
# async def protected_endpoint(request: Request):
#     user = request.state.user
#     return {"message": f"Hello, {user['email']}!"}
