"""
Authentication Service
Handles user registration, login, and JWT token management
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from services import user_service

# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Password functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Token functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Register user
async def register_user(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # Check if user exists
    existing = user_service.get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    existing_email = user_service.get_user_by_email(db, email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = user_service.create_user(db, username, email, password)
    
    # Create token
    token = create_access_token({"sub": user.username})
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

# Login user
async def login_user(email: str, password: str, response: Response, db: Session = Depends(get_db)):
    # Find user
    user = user_service.get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token({"sub": user.username})

    # Set cookie (HTTP-only)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    );

    return {
        "message": "Login successful",
    };

    # return {
    #     "token": token,
    #     "user": {
    #         "id": user.id,
    #         "username": user.username,
    #         "email": user.email,
    #         "role": user.role
    #     }
    # }

# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ):
#     token = credentials.credentials
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")
#
#     user = user_service.get_user_by_username(db, username)
#     if user is None:
#         raise HTTPException(status_code=401, detail="User not found")
#
#     return {
#         "id": user.id,
#         "username": user.username,
#         "email": user.email,
#         "role": user.role
#     }

# Get current user from token
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token found")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # get user from database
    user = user_service.get_user_by_username(db, username)
    return user

# Optional: Get current user (returns None if no token)
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
