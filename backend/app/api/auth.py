import re
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.database import create_user, get_user_by_email
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


def user_response(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    name = request.name.strip()
    email = str(request.email).strip().lower()

    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must contain at least 2 characters.")

    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password is too long.")

    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    password_hash = hash_password(request.password)
    user_id = str(uuid4())

    try:
        create_user(user_id, name, email, password_hash)
    except Exception:
        if get_user_by_email(email):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        raise HTTPException(status_code=500, detail="Could not create account.")

    user = get_user_by_email(email)

    return {
        "message": "Account created successfully.",
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
        "user": user_response(user),
    }


@router.post("/login")
def login(request: LoginRequest):
    email = str(request.email).strip().lower()
    user = get_user_by_email(email)

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user["id"]),
        "token_type": "bearer",
        "user": user_response(user),
    }


@router.get("/me")
def get_me(current_user: dict = __import__("fastapi").Depends(get_current_user)):
    return user_response(current_user)
