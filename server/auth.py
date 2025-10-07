from __future__ import annotations

import datetime as dt
import os
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_secret_key() -> str:
    return os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    now = dt.datetime.utcnow()
    expire = now + dt.timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(expire.timestamp())}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")
    return token


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

