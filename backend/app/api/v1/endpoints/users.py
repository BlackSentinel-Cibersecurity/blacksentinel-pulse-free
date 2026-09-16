from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import RoleChecker
from app.core.security import hash_password
from app.models.user import User, UserRole

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    black_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    force_password_change: bool = False
    totp_enabled: bool = False
    temp_password_plain: Optional[str] = None
    current_password_plain: Optional[str] = None
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin"])),
):
    """List all users in the organization."""
    result = await db.execute(
        select(User).where(User.organization_id == current_user.organization_id)
    )
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin"])),
):
    """Create a new user. Auto-generates username, BlackID, and temporary password."""
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    username = User.generate_username(user_data.first_name, user_data.last_name)
    black_id = User.generate_black_id(user_data.first_name, user_data.last_name)

    while True:
        existing_id = await db.execute(select(User).where(User.black_id == black_id))
        if not existing_id.scalar_one_or_none():
            break
        black_id = User.generate_black_id(user_data.first_name, user_data.last_name)

    temp_password = User.generate_temp_password()
    full_name = f"{user_data.first_name} {user_data.last_name}"

    new_user = User(
        email=user_data.email,
        username=username,
        black_id=black_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        full_name=full_name,
        hashed_password=hash_password(temp_password),
        role=user_data.role,
        is_active=True,
        force_password_change=True,
        temp_password=hash_password(temp_password),
        temp_password_plain=temp_password,
        current_password_plain=temp_password,
        organization_id=current_user.organization_id,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    response = UserResponse.model_validate(new_user)
    response_dict = response.model_dump()
    response_dict["temp_password"] = temp_password
    return response_dict


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin"])),
):
    """Get user details."""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id,
            )
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin"])),
):
    """Update user details."""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id,
            )
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin"])),
):
    """Delete a user (super admin only)."""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == current_user.organization_id,
            )
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    await db.delete(user)
    await db.commit()
