from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Account lockout tracking: {user_id: {"attempts": int, "locked_until": datetime}}
_lockout_store: dict[int, dict] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def validate_secret_key():
    """Reject the default secret key at startup."""
    if settings.SECRET_KEY == "change-me-in-production":
        raise RuntimeError(
            "CRITICAL: SECRET_KEY is set to the default value. "
            "Set a strong SECRET_KEY environment variable before starting. "
            "Example: export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
        )


def create_access_token(subject: Any, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate a secure API key."""
    import secrets

    return f"ps_{secrets.token_urlsafe(32)}"


def check_account_lockout(user_id: int) -> bool:
    """Check if account is locked. Returns True if locked."""
    if user_id not in _lockout_store:
        return False
    info = _lockout_store[user_id]
    if info["locked_until"] and datetime.now(timezone.utc) < info["locked_until"]:
        return True
    if info["locked_until"] and datetime.now(timezone.utc) >= info["locked_until"]:
        _lockout_store[user_id] = {"attempts": 0, "locked_until": None}
        return False
    return False


def record_failed_login(user_id: int) -> bool:
    """Record a failed login attempt. Returns True if account is now locked."""
    if user_id not in _lockout_store:
        _lockout_store[user_id] = {"attempts": 0, "locked_until": None}
    _lockout_store[user_id]["attempts"] += 1
    if _lockout_store[user_id]["attempts"] >= MAX_FAILED_ATTEMPTS:
        _lockout_store[user_id]["locked_until"] = datetime.now(
            timezone.utc
        ) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        return True
    return False


def record_successful_login(user_id: int):
    """Reset failed login attempts on success."""
    _lockout_store[user_id] = {"attempts": 0, "locked_until": None}
