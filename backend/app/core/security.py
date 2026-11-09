"""Password hashing and access-token helpers."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()
ALGORITHM = "HS256"

# Used to spend roughly the same time when a username does not exist.
_DUMMY_HASH = _hasher.hash("infradesk-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Check a password. When there is no hash, a dummy check keeps timing similar."""
    target = password_hash or _DUMMY_HASH
    try:
        ok = _hasher.verify(target, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return ok and password_hash is not None


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(user_id: int) -> tuple[str, int]:
    """Return (token, lifetime_in_seconds)."""
    settings = get_settings()
    now = datetime.now(UTC)
    lifetime = timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user_id), "iat": now, "exp": now + lifetime}
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> int | None:
    """Return the user id from a valid token, or None if it is invalid or expired."""
    try:
        payload = jwt.decode(
            token,
            get_settings().secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
