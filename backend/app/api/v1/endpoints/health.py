from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.core.cache import cache

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "BlackSentinel Pulse",
        "version": settings.VERSION,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifies all dependencies are accessible."""
    checks = {
        "database": False,
        "redis": False,
        "status": "ready",
    }

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["status"] = "not_ready"

    # Check Redis
    try:
        redis_ok = await cache.ping()
        checks["redis"] = redis_ok
        if not redis_ok:
            checks["status"] = "degraded"
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        checks["redis"] = False
        checks["status"] = "degraded"

    return checks


@router.get("/health/live")
async def liveness_check():
    """Liveness check - indicates the service is running."""
    return {"status": "alive"}


@router.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    from app.core.database import async_session_factory
    from app.models.asset import Asset
    from app.models.vulnerability import Vulnerability
    from app.models.alert import Alert
    from sqlalchemy import func

    async with async_session_factory() as db:
        assets = (await db.execute(select(func.count(Asset.id)))).scalar() or 0
        vulns = (await db.execute(select(func.count(Vulnerability.id)))).scalar() or 0
        alerts = (await db.execute(
            select(func.count(Alert.id)).where(Alert.status == "open")
        )).scalar() or 0

    metrics_text = f"""# HELP pulse_assets_total Total number of assets
# TYPE pulse_assets_total gauge
pulse_assets_total {assets}

# HELP pulse_vulnerabilities_total Total number of vulnerabilities
# TYPE pulse_vulnerabilities_total gauge
pulse_vulnerabilities_total {vulns}

# HELP pulse_alerts_open_total Total number of open alerts
# TYPE pulse_alerts_open_total gauge
pulse_alerts_open_total {alerts}

# HELP pulse_info Pulse platform info
# TYPE pulse_info gauge
pulse_info{{version="{settings.VERSION}"}} 1
"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=metrics_text, media_type="text/plain")
