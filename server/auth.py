from __future__ import annotations

import datetime as dt
import os

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=True)


def get_secret_key() -> str:
    return os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    now = dt.datetime.now(dt.UTC)
    expire = now + dt.timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(expire.timestamp())}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")
    return token


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        # Preserve the previous decoder's rejection: this API supplies neither
        # an audience nor the separate OIDC access token required by at_hash.
        if "aud" in payload:
            raise jwt.InvalidAudienceError("Invalid audience")
        if "at_hash" in payload:
            raise jwt.InvalidTokenError(
                "No access_token provided to compare against at_hash claim."
            )
        sub = payload.get("sub")
        return str(sub) if sub else None
    except PyJWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)
