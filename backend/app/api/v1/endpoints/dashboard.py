from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.vulnerability import Vulnerability, Severity
from app.models.scan import Scan, ScanStatus
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.user import User

router = APIRouter()


class OverviewStats(BaseModel):
    total_assets: int
    total_vulnerabilities: int
    total_scans: int
    open_alerts: int
    risk_score_avg: float
    critical_assets: int
    assets_discovered_today: int
    vulnerabilities_resolved_today: int


class RiskDistribution(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    info: int


class TimelinePoint(BaseModel):
    timestamp: str
    assets: int
    vulnerabilities: int
    alerts: int


class TopRiskyAsset(BaseModel):
    id: int
    name: str
    asset_type: str
    risk_score: float
    vulnerability_count: int
    status: str


class DiscoveryTrend(BaseModel):
    date: str
    new_assets: int
    total_assets: int


class DashboardData(BaseModel):
    overview: OverviewStats
    risk_distribution: RiskDistribution
    timeline: list[TimelinePoint]
    top_risky_assets: list[TopRiskyAsset]
    discovery_trends: list[DiscoveryTrend]
    recent_alerts: list[dict]
    scan_status: dict
    asset_type_distribution: dict


@router.get("/", response_model=DashboardData)
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive dashboard data."""
    org_id = current_user.organization_id
    now = datetime.utcnow()

    # Overview stats
    total_assets = (await db.execute(
        select(func.count()).where(Asset.organization_id == org_id)
    )).scalar()

    total_vulns = (await db.execute(
        select(func.count()).select_from(
            select(Vulnerability.id)
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .where(Asset.organization_id == org_id)
            .subquery()
        )
    )).scalar()

    total_scans = (await db.execute(
        select(func.count()).where(Scan.organization_id == org_id)
    )).scalar()

    open_alerts = (await db.execute(
        select(func.count()).where(
            and_(
                Alert.organization_id == org_id,
                Alert.status == AlertStatus.OPEN,
            )
        )
    )).scalar()

    avg_risk = (await db.execute(
        select(func.avg(Asset.risk_score)).where(Asset.organization_id == org_id)
    )).scalar() or 0.0

    critical_assets = (await db.execute(
        select(func.count()).where(
            and_(
                Asset.organization_id == org_id,
                Asset.risk_score >= 90,
            )
        )
    )).scalar()

    assets_today = (await db.execute(
        select(func.count()).where(
            and_(
                Asset.organization_id == org_id,
                Asset.created_at >= now - timedelta(hours=24),
            )
        )
    )).scalar()

    vulns_resolved = (await db.execute(
        select(func.count()).select_from(
            select(Vulnerability.id)
            .join(Asset, Vulnerability.asset_id == Asset.id)
            .where(
                and_(
                    Asset.organization_id == org_id,
                    Vulnerability.status == "remediated",
                    Vulnerability.remediated_at >= now - timedelta(hours=24),
                )
            )
            .subquery()
        )
    )).scalar()

    overview = OverviewStats(
        total_assets=total_assets,
        total_vulnerabilities=total_vulns,
        total_scans=total_scans,
        open_alerts=open_alerts,
        risk_score_avg=round(float(avg_risk), 2),
        critical_assets=critical_assets,
        assets_discovered_today=assets_today,
        vulnerabilities_resolved_today=vulns_resolved,
    )

    # Risk distribution
    risk_dist_query = select(
        Vulnerability.severity, func.count()
    ).join(Asset).where(Asset.organization_id == org_id).group_by(Vulnerability.severity)
    risk_result = await db.execute(risk_dist_query)
    risk_counts = {str(row[0]): row[1] for row in risk_result.all()}
    risk_distribution = RiskDistribution(
        critical=risk_counts.get("critical", 0),
        high=risk_counts.get("high", 0),
        medium=risk_counts.get("medium", 0),
        low=risk_counts.get("low", 0),
        info=risk_counts.get("info", 0),
    )

    # Timeline (daily aggregation)
    timeline = []
    for i in range(days):
        date = now - timedelta(days=days - 1 - i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_assets = (await db.execute(
            select(func.count()).where(
                and_(
                    Asset.organization_id == org_id,
                    Asset.created_at >= day_start,
                    Asset.created_at < day_end,
                )
            )
        )).scalar()

        day_vulns = (await db.execute(
            select(func.count()).select_from(
                select(Vulnerability.id)
                .join(Asset, Vulnerability.asset_id == Asset.id)
                .where(
                    and_(
                        Asset.organization_id == org_id,
                        Vulnerability.discovered_at >= day_start,
                        Vulnerability.discovered_at < day_end,
                    )
                )
                .subquery()
            )
        )).scalar()

        day_alerts = (await db.execute(
            select(func.count()).where(
                and_(
                    Alert.organization_id == org_id,
                    Alert.created_at >= day_start,
                    Alert.created_at < day_end,
                )
            )
        )).scalar()

        timeline.append(TimelinePoint(
            timestamp=date.strftime("%Y-%m-%d"),
            assets=day_assets,
            vulnerabilities=day_vulns,
            alerts=day_alerts,
        ))

    # Top risky assets
    risky_query = (
        select(Asset)
        .where(Asset.organization_id == org_id)
        .order_by(Asset.risk_score.desc())
        .limit(10)
    )
    risky_result = await db.execute(risky_query)
    risky_assets = risky_result.scalars().all()

    top_risky = []
    for a in risky_assets:
        vuln_count = (await db.execute(
            select(func.count()).where(
                and_(
                    Vulnerability.asset_id == a.id,
                    Vulnerability.status != "remediated",
                )
            )
        )).scalar()
        top_risky.append(TopRiskyAsset(
            id=a.id,
            name=a.name,
            asset_type=str(a.asset_type.value),
            risk_score=a.risk_score,
            vulnerability_count=vuln_count,
            status=str(a.status.value),
        ))

    # Discovery trends
    trends = []
    cumulative = total_assets - assets_today
    for i in range(min(days, 30)):
        date = now - timedelta(days=29 - i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        new = (await db.execute(
            select(func.count()).where(
                and_(
                    Asset.organization_id == org_id,
                    Asset.created_at >= day_start,
                    Asset.created_at < day_end,
                )
            )
        )).scalar()
        cumulative += new
        trends.append(DiscoveryTrend(
            date=date.strftime("%Y-%m-%d"),
            new_assets=new,
            total_assets=cumulative,
        ))

    # Recent alerts
    recent_alerts_q = (
        select(Alert)
        .where(Alert.organization_id == org_id)
        .order_by(Alert.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_alerts_q)
    recent_alerts = [
        {
            "id": a.id,
            "title": a.title,
            "severity": a.severity.value,
            "status": a.status.value,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent_result.scalars().all()
    ]

    # Scan status
    scan_status_q = select(Scan.status, func.count()).where(
        Scan.organization_id == org_id
    ).group_by(Scan.status)
    scan_result = await db.execute(scan_status_q)
    scan_status = {str(row[0].value): row[1] for row in scan_result.all()}

    # Asset type distribution
    type_q = select(Asset.asset_type, func.count()).where(
        Asset.organization_id == org_id
    ).group_by(Asset.asset_type)
    type_result = await db.execute(type_q)
    asset_type_dist = {str(row[0].value): row[1] for row in type_result.all()}

    return DashboardData(
        overview=overview,
        risk_distribution=risk_distribution,
        timeline=timeline,
        top_risky_assets=top_risky,
        discovery_trends=trends,
        recent_alerts=recent_alerts,
        scan_status=scan_status,
        asset_type_distribution=asset_type_dist,
    )


@router.get("/realtime")
async def get_realtime_data(
    current_user: User = Depends(get_current_user),
):
    """Get real-time dashboard updates via SSE-ready endpoint."""
    from app.core.cache import cache

    org_id = current_user.organization_id
    key = f"dashboard:realtime:{org_id}"

    cached = await cache.get(key)
    if cached:
        import orjson
        return orjson.loads(cached)

    return {"status": "no_data", "message": "Real-time data will appear after first scan"}
