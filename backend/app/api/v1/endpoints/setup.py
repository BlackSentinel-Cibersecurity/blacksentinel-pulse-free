"""First-time setup endpoint. Forces password creation on initial system start."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.models.organization import Organization

router = APIRouter()


class SetupStatus(BaseModel):
    is_configured: bool
    requires_setup: bool


class SetupRequest(BaseModel):
    admin_email: str
    admin_password: str
    organization_name: str = "Default Organization"


class SetupResponse(BaseModel):
    message: str
    organization: str
    admin_user: str


@router.get("/status", response_model=SetupStatus)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """Check if system requires initial setup. No auth required."""
    result = await db.execute(select(func.count(User.id)))
    count = result.scalar()
    return SetupStatus(
        is_configured=count > 0,
        requires_setup=count == 0,
    )


@router.post("/initialize", response_model=SetupResponse)
async def initialize_system(
    request: SetupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Initialize the system with admin credentials. Only works once.
    No auth required - this is the first-time setup endpoint.
    """
    # Check if already initialized
    result = await db.execute(select(func.count(User.id)))
    count = result.scalar()
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail="System already initialized. Use the regular login.",
        )

    # Validate password strength
    if len(request.admin_password) < 12:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 12 characters with uppercase, lowercase, number, and symbol.",
        )
    if not any(c.isupper() for c in request.admin_password):
        raise HTTPException(status_code=400, detail="Password must contain uppercase letters.")
    if not any(c.islower() for c in request.admin_password):
        raise HTTPException(status_code=400, detail="Password must contain lowercase letters.")
    if not any(c.isdigit() for c in request.admin_password):
        raise HTTPException(status_code=400, detail="Password must contain numbers.")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in request.admin_password):
        raise HTTPException(status_code=400, detail="Password must contain special characters.")

    # Create organization
    org = Organization(
        name=request.organization_name,
        slug=request.organization_name.lower().replace(" ", "-"),
        description="Organization created during initial setup",
        plan="enterprise",
        max_assets=100000,
        max_users=100,
        max_scans_per_day=1000,
    )
    db.add(org)
    await db.flush()

    # Create admin user
    admin = User(
        email=request.admin_email,
        username="admin",
        hashed_password=hash_password(request.admin_password),
        full_name="System Administrator",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        is_verified=True,
        organization_id=org.id,
    )
    db.add(admin)
    await db.commit()

    return SetupResponse(
        message="System initialized successfully. You can now log in.",
        organization=org.name,
        admin_user=admin.username,
    )
