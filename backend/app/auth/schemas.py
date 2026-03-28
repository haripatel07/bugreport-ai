"""Pydantic schemas for authentication payloads."""

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    """Public user info."""

    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token claims."""

    user_id: int
    email: EmailStr
