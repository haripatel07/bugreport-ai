"""Password hashing and JWT utility helpers."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me_to_a_long_random_string")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    """Hash plain password."""

    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify plain password against hash."""

    return pwd_context.verify(password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_minutes: int | None = None) -> str:
    """Create signed JWT token."""

    expire_delta = timedelta(minutes=expires_minutes or JWT_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + expire_delta})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token."""

    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
