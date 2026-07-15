import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(
    subject: str, role: str, token_type: str, expires: timedelta, token_id: str | None = None
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    if token_id:
        payload["jti"] = token_id
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str) -> str:
    return create_token(
        user_id, role, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str, role: str, token_id: str) -> str:
    return create_token(
        user_id, role, "refresh", timedelta(days=settings.refresh_token_expire_days), token_id
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Incorrect token type")
    return payload


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token_id() -> str:
    return secrets.token_urlsafe(24)
