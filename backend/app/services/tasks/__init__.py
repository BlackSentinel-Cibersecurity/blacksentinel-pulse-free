from celery import Celery
from datetime import datetime

from app.core.config import settings

celery_app = Celery(
    "pulse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "update-risk-scores-every-hour": {
            "task": "update_risk_scores",
            "schedule": 3600.0,
        },
        "scheduled-discovery-every-6-hours": {
            "task": "scheduled_discovery",
            "schedule": 21600.0,
        },
    },
)


@celery_app.task(bind=True, name="run_scan_task")
def run_scan_task(self, scan_id: int):
    """Execute a scan asynchronously."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from app.models.scan import Scan, ScanStatus

    async def _run():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = result.scalar_one_or_none()

            if not scan:
                return

            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            await db.commit()

            try:
                from app.services.discovery.domain_scanner import DomainDiscoveryEngine
                from app.services.discovery.network_scanner import NetworkDiscoveryEngine
                from app.services.discovery.cloud_scanner import CloudDiscoveryEngine

                engine_map = {
                    "full_discovery": DomainDiscoveryEngine,
                    "dns_enumeration": DomainDiscoveryEngine,
                    "port_scan": NetworkDiscoveryEngine,
                    "cloud_scan": CloudDiscoveryEngine,
                }

                scan_engine_class = engine_map.get(scan.scan_type.value, DomainDiscoveryEngine)
                scan_engine = scan_engine_class()

                for target in scan.targets:
                    result = await scan_engine.run(target)
                    scan.assets_found += result.get("assets_found", 0)

                scan.status = ScanStatus.COMPLETED
                scan.progress = 100

            except Exception as e:
                scan.status = ScanStatus.FAILED
                scan.error_message = str(e)

            scan.completed_at = datetime.utcnow()
            if scan.started_at:
                scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())
            await db.commit()

        await engine.dispose()

    asyncio.run(_run())


@celery_app.task(bind=True, name="run_discovery_task")
def run_discovery_task(
    self,
    discovery_id: str,
    target: str,
    discovery_type: str,
    options: dict,
    organization_id: int,
):
    """Execute a full discovery operation asynchronously."""
    import asyncio

    async def _run():
        import orjson
        from app.core.cache import cache
        from app.services.discovery.domain_scanner import DomainDiscoveryEngine
        from app.services.discovery.network_scanner import NetworkDiscoveryEngine
        from app.services.discovery.cloud_scanner import CloudDiscoveryEngine
        from app.services.discovery.github_scanner import GitHubDiscoveryEngine

        engines = {
            "domain": DomainDiscoveryEngine,
            "network": NetworkDiscoveryEngine,
            "cloud": CloudDiscoveryEngine,
            "github": GitHubDiscoveryEngine,
            "full": DomainDiscoveryEngine,
        }

        engine_class = engines.get(discovery_type, DomainDiscoveryEngine)
        engine = engine_class()

        try:
            await cache.set(
                f"discovery:{discovery_id}:status",
                orjson.dumps({
                    "discovery_id": discovery_id,
                    "status": "running",
                    "progress": 10,
                    "assets_found": 0,
                    "started_at": datetime.utcnow().isoformat(),
                    "current_phase": "Initializing discovery engine",
                }).decode(),
            )

            result = await engine.run(target, **options)

            await cache.set(
                f"discovery:{discovery_id}:status",
                orjson.dumps({
                    "discovery_id": discovery_id,
                    "status": "completed",
                    "progress": 100,
                    "assets_found": result.get("assets_found", 0),
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "current_phase": "Discovery complete",
                }).decode(),
            )

            await cache.set(
                f"discovery:{discovery_id}:results",
                orjson.dumps(result).decode(),
                ttl=3600,
            )

        except Exception as e:
            await cache.set(
                f"discovery:{discovery_id}:status",
                orjson.dumps({
                    "discovery_id": discovery_id,
                    "status": "failed",
                    "error": str(e),
                }).decode(),
            )

    asyncio.run(_run())


@celery_app.task(bind=True, name="sync_integration_task")
def sync_integration_task(self, org_id: int, provider: str):
    """Sync data from an external integration."""
    import asyncio

    async def _run():
        from app.services.integration_manager import IntegrationManager
        manager = IntegrationManager()
        await manager.sync(org_id=org_id, provider=provider)

    asyncio.run(_run())


@celery_app.task(name="scheduled_discovery")
def scheduled_discovery():
    """Periodic discovery task for all organizations."""
    import asyncio

    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.models.organization import Organization

        engine = create_async_engine(settings.DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            result = await db.execute(select(Organization).where(Organization.is_active == True))
            orgs = result.scalars().all()

            for org in orgs:
                pass

        await engine.dispose()

    asyncio.run(_run())


@celery_app.task(name="update_risk_scores")
def update_risk_scores():
    """Periodically recalculate risk scores for all assets."""
    import asyncio

    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy import select
        from app.models.asset import Asset
        from app.services.ml.risk_engine import RiskScoringEngine

        engine = create_async_engine(settings.DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        risk_engine = RiskScoringEngine()

        async with async_session() as db:
            result = await db.execute(select(Asset))
            assets = result.scalars().all()

            for asset in assets:
                scores = risk_engine.calculate_risk_score(asset.raw_data or {})
                asset.risk_score = scores["risk_score"]
                asset.risk_factors = scores["factors"]

            await db.commit()

        await engine.dispose()

    asyncio.run(_run())
