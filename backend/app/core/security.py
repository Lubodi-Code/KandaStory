from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject, "iat": datetime.now(tz=timezone.utc)}
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def verify_token(token: str) -> str:
    """Verify JWT token and return user_id"""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise jwt.InvalidTokenError("Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")
