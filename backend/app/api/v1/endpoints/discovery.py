import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.deps import get_current_user, RoleChecker
from app.core.edition import LIMITS, EDITION, FREE_DISCOVERY_TYPES
from app.models.user import User
from app.models.asset import Asset

router = APIRouter()


class DiscoveryRequest(BaseModel):
    target: str  # domain, IP range, cloud account, etc.
    discovery_type: str  # full, passive, active, cloud, saas, dns, etc.
    options: dict = {}


class DiscoveryStatus(BaseModel):
    discovery_id: str
    status: str
    progress: int
    assets_found: int
    started_at: str
    current_phase: Optional[str]


class DiscoveryResult(BaseModel):
    discovery_id: str
    status: str
    assets: list[dict]
    summary: dict
    duration_seconds: float


@router.post("/start")
async def start_discovery(
    request: DiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Start a new discovery operation."""
    import uuid
    from app.core.cache import cache

    if EDITION == "free" and request.discovery_type not in FREE_DISCOVERY_TYPES:
        raise HTTPException(
            status_code=403,
            detail=f"Discovery type '{request.discovery_type}' is not available on the free plan. Upgrade to enable it.",
        )

    if LIMITS.max_assets != float("inf"):
        current_count = await db.scalar(
            select(func.count()).select_from(Asset).where(Asset.organization_id == current_user.organization_id)
        )
        if (current_count or 0) >= LIMITS.max_assets:
            raise HTTPException(
                status_code=403,
                detail=f"Free plan is limited to {LIMITS.max_assets} assets. Upgrade to add more.",
            )

    discovery_id = str(uuid.uuid4())

    # Store discovery state (Redis optional)
    try:
        from app.core.cache import cache
        await cache.set(
            f"discovery:{discovery_id}:status",
            json.dumps({
                "discovery_id": discovery_id,
                "status": "initializing",
                "progress": 0,
                "assets_found": 0,
                "started_at": datetime.utcnow().isoformat(),
                "current_phase": "Queued for execution",
            }),
        )
    except Exception:
        pass

    # Trigger async discovery (Celery optional)
    try:
        from app.services.tasks import run_discovery_task
        run_discovery_task.delay(
            discovery_id=discovery_id,
            target=request.target,
            discovery_type=request.discovery_type,
            options=request.options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        pass

    return {
        "discovery_id": discovery_id,
        "status": "started",
        "message": f"Discovery started for target: {request.target}",
    }


@router.get("/status/{discovery_id}")
async def get_discovery_status(
    discovery_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the status of a running discovery."""
    try:
        from app.core.cache import cache
        import orjson
        cached = await cache.get(f"discovery:{discovery_id}:status")
        if cached:
            return orjson.loads(cached)
    except Exception:
        pass

    return {"status": "not_found", "message": "Discovery not found or expired"}


@router.get("/results/{discovery_id}")
async def get_discovery_results(
    discovery_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get results of a completed discovery."""
    try:
        from app.core.cache import cache
        import orjson
        cached = await cache.get(f"discovery:{discovery_id}:results")
        if cached:
            return orjson.loads(cached)
    except Exception:
        pass

    return {"status": "not_ready", "message": "Results not available yet"}


@router.post("/scan-domain")
async def scan_domain(
    domain: str,
    deep: bool = Query(False, description="Enable deep scanning"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Quick domain scan - discover subdomains, DNS records, certificates."""
    try:
        from app.services.discovery.domain_scanner import DomainDiscoveryEngine
        engine = DomainDiscoveryEngine()
        results = await engine.discover(domain, deep=deep)
    except Exception:
        results = {"subdomains": [], "error": "Discovery engine not available"}

    return {
        "domain": domain,
        "results": results,
        "assets_found": len(results.get("subdomains", [])),
    }


@router.post("/scan-ip")
async def scan_ip_range(
    ip_range: str,
    ports: str = Query("top-1000", description="Port range to scan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Scan an IP range for open ports and services."""
    try:
        from app.services.discovery.network_scanner import NetworkDiscoveryEngine
        engine = NetworkDiscoveryEngine()
        results = await engine.scan_range(ip_range, ports=ports)
    except Exception:
        results = {"error": "Network scanner not available"}

    return {
        "ip_range": ip_range,
        "results": results,
    }


@router.post("/scan-cloud")
async def scan_cloud(
    provider: str,
    credentials: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Discover cloud assets across providers."""
    try:
        from app.services.discovery.cloud_scanner import CloudDiscoveryEngine
        engine = CloudDiscoveryEngine()
        results = await engine.discover(provider=provider, credentials=credentials)
    except Exception:
        results = {"resources": [], "error": "Cloud scanner not available"}

    return {
        "provider": provider,
        "results": results,
        "resources_found": len(results.get("resources", [])),
    }


@router.post("/scan-github")
async def scan_github(
    org: str,
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        RoleChecker(["super_admin", "admin", "analyst"])
    ),
):
    """Discover assets in GitHub organization."""
    try:
        from app.services.discovery.github_scanner import GitHubDiscoveryEngine
        engine = GitHubDiscoveryEngine()
        results = await engine.discover(org=org, token=token)
    except Exception:
        results = {"error": "GitHub scanner not available"}

    return {
        "organization": org,
        "results": results,
    }


@router.get("/capabilities")
async def get_discovery_capabilities():
    """List all discovery engine capabilities."""
    return {
        "discovery_types": [
            {
                "type": "full_discovery",
                "name": "Full Discovery",
                "description": "Complete attack surface discovery including all modules",
                "phases": ["passive_recon", "dns_enumeration", "port_scan", "service_detection", "vulnerability_scan", "threat_intel"],
            },
            {
                "type": "passive_recon",
                "name": "Passive Reconnaissance",
                "description": "Gather information without touching the target",
                "sources": ["shodan", "censys", "virustotal", "osint"],
            },
            {
                "type": "dns_enumeration",
                "name": "DNS Enumeration",
                "description": "Discover subdomains and DNS records",
                "methods": ["brute_force", "certificate_transparency", "wordlist", "passive"],
            },
            {
                "type": "port_scan",
                "name": "Port Scanning",
                "description": "Discover open ports and services",
                "methods": ["tcp_syn", "tcp_connect", "udp"],
            },
            {
                "type": "cloud_discovery",
                "name": "Cloud Discovery",
                "description": "Discover assets across cloud providers",
                "providers": ["aws", "azure", "gcp", "digital_ocean"],
            },
            {
                "type": "web_application",
                "name": "Web Application Discovery",
                "description": "Discover web applications and APIs",
                "features": ["technology_detection", "api_discovery", "authentication_detection"],
            },
            {
                "type": "certificate_transparency",
                "name": "Certificate Transparency",
                "description": "Discover subdomains via CT logs",
                "sources": ["crt_sh", "censys_ct", "google_ct"],
            },
            {
                "type": "threat_intelligence",
                "name": "Threat Intelligence",
                "description": "Correlate assets with threat intelligence",
                "feeds": ["virustotal", "abuseipdb", "otx", "misp"],
            },
        ],
        "asset_types_supported": [
            "domain", "subdomain", "ip_address", "web_application", "api_endpoint",
            "cloud_resource", "container", "kubernetes", "serverless", "database",
            "dns_record", "ssl_certificate", "email_server", "vpn", "firewall",
            "repository", "ci_cd_pipeline", "identity_provider", "saas_application",
        ],
    }
