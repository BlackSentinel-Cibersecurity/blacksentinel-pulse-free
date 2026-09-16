import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.scan import Scan, ScanType, ScanStatus
from app.models.user import User

router = APIRouter()


class ScanCreate(BaseModel):
    name: Optional[str] = None
    scan_type: ScanType
    targets: list[str] = []
    config: dict = {}
    options: dict = {}


class ScanResponse(BaseModel):
    id: int
    scan_id: str
    name: Optional[str]
    scan_type: ScanType
    status: ScanStatus
    progress: int
    current_step: Optional[str]
    assets_found: int
    vulnerabilities_found: int
    critical_findings: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    triggered_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ScanStatus] = None,
    scan_type: Optional[ScanType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all scans with filtering and pagination."""
    query = select(Scan).where(Scan.organization_id == current_user.organization_id)

    if status:
        query = query.where(Scan.status == status)
    if scan_type:
        query = query.where(Scan.scan_type == scan_type)

    count = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar()

    query = query.order_by(Scan.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    scans = result.scalars().all()

    return ScanListResponse(
        items=[ScanResponse.model_validate(s) for s in scans],
        total=count,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=ScanResponse, status_code=201)
async def create_scan(
    scan_data: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin", "analyst"])),
):
    """Create and start a new scan."""
    scan = Scan(
        scan_id=str(uuid.uuid4()),
        name=scan_data.name or f"Scan {datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        scan_type=scan_data.scan_type,
        config=scan_data.config,
        targets=scan_data.targets,
        options=scan_data.options,
        organization_id=current_user.organization_id,
        triggered_by="manual",
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Trigger async scan via Celery (optional - scan still created if Celery unavailable)
    try:
        from app.services.tasks import run_scan_task

        run_scan_task.delay(scan.id)
    except Exception:
        pass

    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get scan details by ID."""
    result = await db.execute(
        select(Scan).where(
            and_(
                Scan.scan_id == scan_id,
                Scan.organization_id == current_user.organization_id,
            )
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanResponse.model_validate(scan)


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin", "analyst"])),
):
    """Cancel a running scan."""
    result = await db.execute(
        select(Scan).where(
            and_(
                Scan.scan_id == scan_id,
                Scan.organization_id == current_user.organization_id,
            )
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != ScanStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Scan is not running")

    scan.status = ScanStatus.CANCELLED
    scan.completed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Scan cancelled"}


@router.get("/{scan_id}/results")
async def get_scan_results(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed scan results."""
    from app.models.scan import ScanResult

    result = await db.execute(
        select(Scan).where(
            and_(
                Scan.scan_id == scan_id,
                Scan.organization_id == current_user.organization_id,
            )
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    results = await db.execute(select(ScanResult).where(ScanResult.scan_id == scan.id))

    return {
        "scan_id": scan_id,
        "status": scan.status.value,
        "summary": {
            "assets_found": scan.assets_found,
            "vulnerabilities_found": scan.vulnerabilities_found,
            "critical": scan.critical_findings,
            "high": scan.high_findings,
            "medium": scan.medium_findings,
            "low": scan.low_findings,
        },
        "results": [r.data for r in results.scalars().all()],
    }
