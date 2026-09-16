from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.models.vulnerability import Vulnerability, Severity, VulnerabilityStatus
from app.models.asset import Asset
from app.models.user import User

router = APIRouter()


class VulnResponse(BaseModel):
    id: int
    external_id: Optional[str]
    title: str
    description: Optional[str]
    severity: Severity
    cvss_score: Optional[float]
    status: VulnerabilityStatus
    exploit_available: bool
    exploit_in_wild: bool
    patch_available: bool
    asset_id: int
    asset_name: Optional[str]
    discovered_at: datetime
    risk_score: float

    class Config:
        from_attributes = True


class VulnListResponse(BaseModel):
    items: list[VulnResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=VulnListResponse)
async def list_vulnerabilities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[Severity] = None,
    status: Optional[VulnerabilityStatus] = None,
    asset_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all vulnerabilities."""
    query = (
        select(Vulnerability)
        .join(Asset, Vulnerability.asset_id == Asset.id)
        .where(Asset.organization_id == current_user.organization_id)
    )

    if severity:
        query = query.where(Vulnerability.severity == severity)
    if status:
        query = query.where(Vulnerability.status == status)
    if asset_id:
        query = query.where(Vulnerability.asset_id == asset_id)
    if search:
        query = query.where(
            Vulnerability.title.ilike(f"%{search}%")
            | Vulnerability.external_id.ilike(f"%{search}%")
        )

    count = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar()

    query = query.order_by(Vulnerability.cvss_score.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    vulns = result.scalars().all()

    items = []
    for v in vulns:
        asset_result = await db.execute(
            select(Asset.name).where(Asset.id == v.asset_id)
        )
        asset_name = asset_result.scalar_one_or_none()

        items.append(
            VulnResponse(
                id=v.id,
                external_id=v.external_id,
                title=v.title,
                description=v.description,
                severity=v.severity,
                cvss_score=v.cvss_score,
                status=v.status,
                exploit_available=v.exploit_available,
                exploit_in_wild=v.exploit_in_wild,
                patch_available=v.patch_available,
                asset_id=v.asset_id,
                asset_name=asset_name,
                discovered_at=v.discovered_at,
                risk_score=v.risk_score,
            )
        )

    return VulnListResponse(items=items, total=count, page=page, page_size=page_size)


@router.get("/stats")
async def get_vuln_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability statistics."""
    # By severity
    sev_query = (
        select(Vulnerability.severity, func.count())
        .join(Asset)
        .where(Asset.organization_id == current_user.organization_id)
        .group_by(Vulnerability.severity)
    )
    sev_result = await db.execute(sev_query)
    by_severity = {str(row[0].value): row[1] for row in sev_result.all()}

    # By status
    status_query = (
        select(Vulnerability.status, func.count())
        .join(Asset)
        .where(Asset.organization_id == current_user.organization_id)
        .group_by(Vulnerability.status)
    )
    status_result = await db.execute(status_query)
    by_status = {str(row[0].value): row[1] for row in status_result.all()}

    # Exploitable
    exploitable = (
        await db.execute(
            select(func.count()).select_from(
                select(Vulnerability.id)
                .join(Asset)
                .where(
                    and_(
                        Asset.organization_id == current_user.organization_id,
                        Vulnerability.exploit_available == True,
                    )
                )
                .subquery()
            )
        )
    ).scalar()

    # Average CVSS
    avg_cvss = (
        await db.execute(
            select(func.avg(Vulnerability.cvss_score))
            .join(Asset)
            .where(Asset.organization_id == current_user.organization_id)
        )
    ).scalar() or 0.0

    # MTTR (Mean Time to Remediate)
    mttr = (
        await db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        Vulnerability.remediated_at - Vulnerability.discovered_at,
                    )
                    / 86400
                )
            )
            .join(Asset)
            .where(
                and_(
                    Asset.organization_id == current_user.organization_id,
                    Vulnerability.status == VulnerabilityStatus.REMEDIATED,
                    Vulnerability.remediated_at.isnot(None),
                )
            )
        )
    ).scalar() or 0.0

    return {
        "by_severity": by_severity,
        "by_status": by_status,
        "exploitable_count": exploitable,
        "avg_cvss": round(float(avg_cvss), 2),
        "mttr_days": round(float(mttr), 1),
    }


@router.get("/{vuln_id}", response_model=VulnResponse)
async def get_vulnerability(
    vuln_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability details."""
    result = await db.execute(
        select(Vulnerability)
        .join(Asset, Vulnerability.asset_id == Asset.id)
        .where(
            and_(
                Vulnerability.id == vuln_id,
                Asset.organization_id == current_user.organization_id,
            )
        )
    )
    vuln = result.scalar_one_or_none()

    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    asset_result = await db.execute(select(Asset.name).where(Asset.id == vuln.asset_id))
    asset_name = asset_result.scalar_one_or_none()

    return VulnResponse(
        id=vuln.id,
        external_id=vuln.external_id,
        title=vuln.title,
        description=vuln.description,
        severity=vuln.severity,
        cvss_score=vuln.cvss_score,
        status=vuln.status,
        exploit_available=vuln.exploit_available,
        exploit_in_wild=vuln.exploit_in_wild,
        patch_available=vuln.patch_available,
        asset_id=vuln.asset_id,
        asset_name=asset_name,
        discovered_at=vuln.discovered_at,
        risk_score=vuln.risk_score,
    )


@router.put("/{vuln_id}/status")
async def update_vuln_status(
    vuln_id: int,
    new_status: VulnerabilityStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["super_admin", "admin", "analyst"])),
):
    """Update vulnerability status."""
    result = await db.execute(
        select(Vulnerability)
        .join(Asset, Vulnerability.asset_id == Asset.id)
        .where(
            and_(
                Vulnerability.id == vuln_id,
                Asset.organization_id == current_user.organization_id,
            )
        )
    )
    vuln = result.scalar_one_or_none()

    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    vuln.status = new_status
    if new_status == VulnerabilityStatus.REMEDIATED:
        vuln.remediated_at = datetime.utcnow()

    await db.commit()

    return {"message": f"Vulnerability status updated to {new_status.value}"}
