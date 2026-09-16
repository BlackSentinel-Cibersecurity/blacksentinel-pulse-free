from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    decode_token,
    check_account_lockout,
    record_failed_login,
    record_successful_login,
)
from app.core.config import settings
from app.core.password_validator import validate_password_strength
from app.core.totp import totp_service
from app.models.user import User

router = APIRouter()


class UserInfo(BaseModel):
    id: int
    email: str
    username: str
    black_id: str | None = None
    full_name: str
    role: str
    is_active: bool
    organization_id: int
    force_password_change: bool = False
    totp_enabled: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForceChangePasswordRequest(BaseModel):
    new_password: str


class TOTPSetupResponse(BaseModel):
    secret: str
    qr_code: str
    provisioning_uri: str


class TOTPVerifyRequest(BaseModel):
    code: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with username (or BlackID) and password."""
    result = await db.execute(
        select(User).where(
            or_(
                User.username == request.username,
                User.black_id == request.username,
            )
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    if check_account_lockout(user.id):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed attempts. Try again later.",
        )

    if not verify_password(request.password, user.hashed_password):
        locked = record_failed_login(user.id)
        if locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed attempts. Try again in 15 minutes.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if user.totp_enabled and user.totp_secret:
        if not request.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code required",
            )
        if not totp_service.verify(user.totp_secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )

    record_successful_login(user.id)

    from datetime import datetime

    user.last_login = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    user_role = user.role.value if hasattr(user.role, "value") else user.role

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(
            id=user.id,
            email=user.email,
            username=user.username,
            black_id=user.black_id,
            full_name=user.full_name,
            role=user_role,
            is_active=user.is_active,
            organization_id=user.organization_id,
            force_password_change=user.force_password_change,
            totp_enabled=user.totp_enabled,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    user_role = user.role.value if hasattr(user.role, "value") else user.role

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(
            id=user.id,
            email=user.email,
            username=user.username,
            black_id=user.black_id,
            full_name=user.full_name,
            role=user_role,
            is_active=user.is_active,
            organization_id=user.organization_id,
            force_password_change=user.force_password_change,
            totp_enabled=user.totp_enabled,
        ),
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user info."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "black_id": current_user.black_id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "role": current_user.role.value
        if hasattr(current_user.role, "value")
        else current_user.role,
        "is_active": current_user.is_active,
        "organization_id": current_user.organization_id,
        "force_password_change": current_user.force_password_change,
        "totp_enabled": current_user.totp_enabled,
        "created_at": current_user.created_at.isoformat()
        if current_user.created_at
        else None,
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change current user password."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    valid, msg = validate_password_strength(request.new_password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    current_user.hashed_password = hash_password(request.new_password)
    current_user.current_password_plain = request.new_password
    current_user.force_password_change = False
    current_user.temp_password = None
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/force-change-password")
async def force_change_password(
    request: ForceChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Force change password after first login with temporary password."""
    valid, msg = validate_password_strength(request.new_password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    current_user.hashed_password = hash_password(request.new_password)
    current_user.current_password_plain = request.new_password
    current_user.force_password_change = False
    current_user.temp_password = None
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set up TOTP 2FA for current user. Returns QR code for Google Authenticator."""
    secret = totp_service.generate_secret()
    current_user.totp_secret = secret
    await db.commit()

    qr_code = totp_service.generate_qr_code_base64(secret, current_user.email)
    uri = totp_service.get_provisioning_uri(secret, current_user.email)

    return TOTPSetupResponse(
        secret=secret,
        qr_code=qr_code,
        provisioning_uri=uri,
    )


@router.post("/totp/verify")
async def verify_totp(
    request: TOTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify TOTP code and enable 2FA."""
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP not set up. Call /totp/setup first.",
        )

    if not totp_service.verify(current_user.totp_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )

    current_user.totp_enabled = True
    await db.commit()

    return {"message": "TOTP 2FA enabled successfully"}


@router.post("/totp/disable")
async def disable_totp(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable TOTP 2FA."""
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()

    return {"message": "TOTP 2FA disabled"}
