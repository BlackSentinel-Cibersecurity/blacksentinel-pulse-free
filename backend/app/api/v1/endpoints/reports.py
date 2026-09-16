from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability, Severity
from app.models.scan import Scan
from app.models.alert import Alert, AlertStatus
from app.models.user import User

router = APIRouter()


class ExecutiveReport(BaseModel):
    report_date: str
    period: str
    executive_summary: str
    risk_overview: dict
    asset_overview: dict
    vulnerability_overview: dict
    compliance_overview: dict
    recommendations: list[str]
    trends: dict


class AssetReport(BaseModel):
    total_assets: int
    by_type: dict
    by_status: dict
    by_criticality: dict
    by_cloud_provider: dict
    top_risky: list[dict]
    recently_discovered: list[dict]


@router.get("/executive", response_model=ExecutiveReport)
async def get_executive_report(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate executive security report."""
    org_id = current_user.organization_id
    now = datetime.utcnow()

    # Asset stats
    total_assets = (
        await db.execute(select(func.count()).where(Asset.organization_id == org_id))
    ).scalar()

    # Vuln stats
    total_vulns = (
        await db.execute(
            select(func.count()).select_from(
                select(Vulnerability.id)
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(Asset.organization_id == org_id)
                .subquery()
            )
        )
    ).scalar()

    critical_vulns = (
        await db.execute(
            select(func.count()).select_from(
                select(Vulnerability.id)
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(
                    and_(
                        Asset.organization_id == org_id,
                        Vulnerability.severity == Severity.CRITICAL,
                    )
                )
                .subquery()
            )
        )
    ).scalar()

    # Scan stats
    total_scans = (
        await db.execute(select(func.count()).where(Scan.organization_id == org_id))
    ).scalar()

    # Alert stats
    open_alerts = (
        await db.execute(
            select(func.count()).where(
                and_(
                    Alert.organization_id == org_id,
                    Alert.status == AlertStatus.OPEN,
                )
            )
        )
    ).scalar()

    # Risk score
    avg_risk = (
        await db.execute(
            select(func.avg(Asset.risk_score)).where(Asset.organization_id == org_id)
        )
    ).scalar() or 0.0

    # Generate executive summary
    risk_level = (
        "LOW"
        if avg_risk < 30
        else "MEDIUM"
        if avg_risk < 60
        else "HIGH"
        if avg_risk < 80
        else "CRITICAL"
    )
    summary = f"""
    During the past {days} days, BlackSentinel Pulse monitored {total_assets} assets across your infrastructure.
    {total_vulns} vulnerabilities were identified, with {critical_vulns} rated as critical.
    {open_alerts} alerts remain open requiring attention.
    The average risk score is {avg_risk:.1f}/100 ({risk_level}).
    """

    recommendations = []
    if critical_vulns > 0:
        recommendations.append(
            f"Immediately remediate {critical_vulns} critical vulnerabilities"
        )
    if avg_risk > 60:
        recommendations.append(
            "Overall risk score is elevated - review high-risk assets"
        )
    if open_alerts > 10:
        recommendations.append(f"{open_alerts} open alerts need attention")

    return ExecutiveReport(
        report_date=now.strftime("%Y-%m-%d"),
        period=f"Last {days} days",
        executive_summary=summary,
        risk_overview={
            "average_risk_score": round(float(avg_risk), 2),
            "risk_level": risk_level,
            "critical_vulnerabilities": critical_vulns,
            "open_alerts": open_alerts,
        },
        asset_overview={
            "total": total_assets,
            "scans_performed": total_scans,
        },
        vulnerability_overview={
            "total": total_vulns,
            "critical": critical_vulns,
        },
        compliance_overview={
            "status": "needs_review",
        },
        recommendations=recommendations,
        trends={},
    )


@router.get("/assets", response_model=AssetReport)
async def get_asset_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate detailed asset report."""
    org_id = current_user.organization_id

    total = (
        await db.execute(select(func.count()).where(Asset.organization_id == org_id))
    ).scalar()

    # By type
    type_q = (
        select(Asset.asset_type, func.count())
        .where(Asset.organization_id == org_id)
        .group_by(Asset.asset_type)
    )
    type_result = await db.execute(type_q)
    by_type = {str(row[0].value): row[1] for row in type_result.all()}

    # By status
    status_q = (
        select(Asset.status, func.count())
        .where(Asset.organization_id == org_id)
        .group_by(Asset.status)
    )
    status_result = await db.execute(status_q)
    by_status = {str(row[0].value): row[1] for row in status_result.all()}

    # By criticality
    crit_q = (
        select(Asset.criticality, func.count())
        .where(Asset.organization_id == org_id)
        .group_by(Asset.criticality)
    )
    crit_result = await db.execute(crit_q)
    by_criticality = {str(row[0]): row[1] for row in crit_result.all()}

    # Top risky
    risky_q = (
        select(Asset)
        .where(Asset.organization_id == org_id)
        .order_by(Asset.risk_score.desc())
        .limit(10)
    )
    risky_result = await db.execute(risky_q)
    top_risky = [
        {"name": a.name, "type": str(a.asset_type.value), "risk_score": a.risk_score}
        for a in risky_result.scalars().all()
    ]

    # Recently discovered
    recent_q = (
        select(Asset)
        .where(Asset.organization_id == org_id)
        .order_by(Asset.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_q)
    recently = [
        {
            "name": a.name,
            "type": str(a.asset_type.value),
            "discovered_at": a.created_at.isoformat(),
        }
        for a in recent_result.scalars().all()
    ]

    return AssetReport(
        total_assets=total,
        by_type=by_type,
        by_status=by_status,
        by_criticality=by_criticality,
        by_cloud_provider={},
        top_risky=top_risky,
        recently_discovered=recently,
    )
