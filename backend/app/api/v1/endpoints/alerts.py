from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.user import User

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    alert_id: str
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    alert_type: str
    source: Optional[str]
    ai_confidence: Optional[float]
    ai_explanation: Optional[str]
    ai_recommendation: Optional[str]
    auto_remediation_available: bool
    blast_radius: Optional[int] = 0
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    alert_type: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all alerts."""
    query = select(Alert).where(Alert.organization_id == current_user.organization_id)

    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if search:
        query = query.where(
            Alert.title.ilike(f"%{search}%") |
            Alert.description.ilike(f"%{search}%")
        )

    count = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar()

    query = query.order_by(Alert.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=count,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alert statistics."""
    org_id = current_user.organization_id

    # Open by severity
    open_query = select(Alert.severity, func.count()).where(
        and_(
            Alert.organization_id == org_id,
            Alert.status == AlertStatus.OPEN,
        )
    ).group_by(Alert.severity)
    open_result = await db.execute(open_query)
    open_by_severity = {str(row[0].value): row[1] for row in open_result.all()}

    # Total open
    total_open = (await db.execute(
        select(func.count()).where(
            and_(
                Alert.organization_id == org_id,
                Alert.status == AlertStatus.OPEN,
            )
        )
    )).scalar()

    # Auto-resolved
    auto_resolved = (await db.execute(
        select(func.count()).where(
            and_(
                Alert.organization_id == org_id,
                Alert.auto_resolved == True,
            )
        )
    )).scalar()

    # SLA breaches
    sla_breached = (await db.execute(
        select(func.count()).where(
            and_(
                Alert.organization_id == org_id,
                Alert.sla_breached == True,
            )
        )
    )).scalar()

    return {
        "open_by_severity": open_by_severity,
        "total_open": total_open,
        "auto_resolved": auto_resolved,
        "sla_breaches": sla_breached,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get alert details."""
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.alert_id == alert_id,
                Alert.organization_id == current_user.organization_id,
            )
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Acknowledge an alert."""
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.alert_id == alert_id,
                Alert.organization_id == current_user.organization_id,
            )
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()

    return {"message": "Alert acknowledged"}


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Resolve an alert."""
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.alert_id == alert_id,
                Alert.organization_id == current_user.organization_id,
            )
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = notes
    await db.commit()

    return {"message": "Alert resolved"}


@router.put("/{alert_id}/false-positive")
async def mark_false_positive(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Mark an alert as false positive."""
    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.alert_id == alert_id,
                Alert.organization_id == current_user.organization_id,
            )
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.FALSE_POSITIVE
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    await db.commit()

    return {"message": "Alert marked as false positive"}
