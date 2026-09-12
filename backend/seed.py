"""Seed script to create initial admin user, organization, and demo data."""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.vulnerability import Vulnerability, Severity, VulnerabilityStatus
from app.models.scan import Scan, ScanType, ScanStatus
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.threat import ThreatIntelligence, ThreatType
from app.models.certificate import Certificate
from app.models.dns_record import DNSRecord

# Use configured database URL (PostgreSQL in Docker, SQLite locally)
_database_url = settings.DATABASE_URL


DEMO_DOMAINS = [
    "blacksentinel.com", "api.blacksentinel.com", "app.blacksentinel.com",
    "staging.blacksentinel.com", "admin.blacksentinel.com", "mail.blacksentinel.com",
    "cdn.blacksentinel.com", "grafana.blacksentinel.com", "jira.blacksentinel.com",
    "git.blacksentinel.com", "ci.blacksentinel.com", "monitoring.blacksentinel.com",
]

DEMO_IPS = [
    "104.21.45.67", "104.21.46.68", "172.67.189.34", "172.67.189.35",
    "52.84.12.100", "52.84.12.101", "34.102.136.180", "34.102.136.181",
    "13.107.42.14", "20.190.151.68", "20.190.151.69", "40.126.32.140",
]

VULN_TEMPLATES = [
    {"name": "Open Redirect", "severity": Severity.LOW, "cwe": "CWE-601"},
    {"name": "Cross-Site Scripting (XSS)", "severity": Severity.MEDIUM, "cwe": "CWE-79"},
    {"name": "SQL Injection", "severity": Severity.CRITICAL, "cwe": "CWE-89"},
    {"name": "Remote Code Execution", "severity": Severity.CRITICAL, "cwe": "CWE-94"},
    {"name": "Server-Side Request Forgery", "severity": Severity.HIGH, "cwe": "CWE-918"},
    {"name": "Insecure Direct Object Reference", "severity": Severity.MEDIUM, "cwe": "CWE-639"},
    {"name": "Broken Authentication", "severity": Severity.HIGH, "cwe": "CWE-287"},
    {"name": "Sensitive Data Exposure", "severity": Severity.HIGH, "cwe": "CWE-200"},
    {"name": "XML External Entity", "severity": Severity.HIGH, "cwe": "CWE-611"},
    {"name": "Security Misconfiguration", "severity": Severity.MEDIUM, "cwe": "CWE-538"},
    {"name": "Cross-Site Request Forgery", "severity": Severity.MEDIUM, "cwe": "CWE-352"},
    {"name": "Path Traversal", "severity": Severity.HIGH, "cwe": "CWE-22"},
    {"name": "Information Disclosure", "severity": Severity.LOW, "cwe": "CWE-200"},
    {"name": "Deprecated TLS Version", "severity": Severity.MEDIUM, "cwe": "CWE-326"},
    {"name": "Missing Security Headers", "severity": Severity.LOW, "cwe": "CWE-693"},
]


async def seed():
    engine = create_async_engine(_database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if admin already exists
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("Data already seeded. Skipping.")
            await engine.dispose()
            return

        # Create default organization
        org = Organization(
            name="Default Organization",
            slug="default",
            description="Default organization for BlackSentinel Pulse",
            plan="enterprise",
            max_assets=100000,
            max_users=100,
            max_scans_per_day=1000,
        )
        db.add(org)
        await db.flush()

        # Create users
        admin = User(
            email="admin@blacksentinel.com", username="admin",
            hashed_password=hash_password("admin123"),
            full_name="System Administrator", role=UserRole.SUPER_ADMIN,
            is_active=True, is_verified=True, organization_id=org.id,
        )
        analyst = User(
            email="analyst@blacksentinel.com", username="analyst",
            hashed_password=hash_password("analyst123"),
            full_name="SOC Analyst", role=UserRole.SOC_ANALYST_3,
            is_active=True, is_verified=True, organization_id=org.id,
        )
        viewer = User(
            email="viewer@blacksentinel.com", username="viewer",
            hashed_password=hash_password("viewer123"),
            full_name="Read Only User", role=UserRole.VIEWER,
            is_active=True, is_verified=True, organization_id=org.id,
        )
        db.add_all([admin, analyst, viewer])
        await db.flush()

        # Create demo assets
        assets = []
        for i, domain in enumerate(DEMO_DOMAINS):
            asset = Asset(
                uuid=str(uuid.uuid4()),
                name=domain,
                asset_type=AssetType.DOMAIN if i == 0 else AssetType.SUBDOMAIN,
                status=random.choice([AssetStatus.ACTIVE, AssetStatus.ACTIVE, AssetStatus.MONITORED]),
                risk_score=random.uniform(0.1, 0.9),
                criticality=random.choice(["critical", "high", "medium", "low"]),
                ip_address=random.choice(DEMO_IPS),
                hostname=domain,
                tags=["production", "internet-facing"],
                organization_id=org.id,
                first_seen=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                last_seen=datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
            )
            assets.append(asset)

        for i, ip in enumerate(DEMO_IPS[:6]):
            asset = Asset(
                uuid=str(uuid.uuid4()),
                name=ip,
                asset_type=AssetType.IP_ADDRESS,
                status=AssetStatus.ACTIVE,
                risk_score=random.uniform(0.1, 0.8),
                criticality=random.choice(["high", "medium", "low"]),
                ip_address=ip,
                tags=["production", "server"],
                organization_id=org.id,
                first_seen=datetime.utcnow() - timedelta(days=random.randint(60, 730)),
                last_seen=datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
            )
            assets.append(asset)

        db.add_all(assets)
        await db.flush()

        # Create vulnerabilities
        vulns = []
        for asset in assets:
            num_vulns = random.randint(0, 5)
            for _ in range(num_vulns):
                template = random.choice(VULN_TEMPLATES)
                vuln = Vulnerability(
                    title=template["name"],
                    severity=template["severity"],
                    cwe_id=template.get("cwe"),
                    status=random.choice([VulnerabilityStatus.OPEN, VulnerabilityStatus.OPEN, VulnerabilityStatus.IN_PROGRESS]),
                    description=f"Detected {template['name']} on {asset.name}",
                    risk_score=random.uniform(0.2, 1.0),
                    asset_id=asset.id,
                    discovered_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                )
                vulns.append(vuln)
        db.add_all(vulns)
        await db.flush()

        # Create scans
        scans = []
        for i in range(10):
            scan = Scan(
                scan_id=str(uuid.uuid4()),
                name=f"Discovery Scan #{i+1}",
                scan_type=random.choice([ScanType.FULL_DISCOVERY, ScanType.VULNERABILITY_SCAN, ScanType.ACTIVE_SCAN]),
                status=random.choice([ScanStatus.COMPLETED, ScanStatus.COMPLETED, ScanStatus.RUNNING]),
                progress=random.randint(0, 100),
                started_at=datetime.utcnow() - timedelta(days=random.randint(0, 7)),
                completed_at=datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
                organization_id=org.id,
                assets_found=random.randint(5, 50),
                vulnerabilities_found=random.randint(0, 20),
            )
            scans.append(scan)
        db.add_all(scans)
        await db.flush()

        # Create alerts
        alerts = []
        alert_titles = [
            "New critical vulnerability detected",
            "SSL certificate expiring soon",
            "Unusual scan activity detected",
            "New subdomain discovered",
            "Credential exposure found",
            "Configuration change detected",
        ]
        for title in alert_titles:
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                title=title,
                description=f"Alert: {title} on external infrastructure",
                severity=random.choice([AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]),
                status=random.choice([AlertStatus.OPEN, AlertStatus.OPEN, AlertStatus.INVESTIGATING]),
                alert_type="vulnerability",
                organization_id=org.id,
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
            )
            alerts.append(alert)
        db.add_all(alerts)

        # Create threat intel entries
        threat_intel = []
        for asset in assets[:5]:
            ti = ThreatIntelligence(
                indicator_value=asset.ip_address or asset.name,
                indicator_type="ip_address" if asset.ip_address else "domain",
                indicators=[asset.ip_address or asset.name],
                threat_type=random.choice([ThreatType.MALWARE, ThreatType.C2, ThreatType.BOTNET]),
                confidence=random.uniform(0.5, 1.0),
                severity=random.choice(["high", "critical"]),
                source="VirusTotal",
                asset_id=asset.id,
            )
            threat_intel.append(ti)
        db.add_all(threat_intel)

        await db.commit()

        print("=" * 60)
        print("BLACKSENTINEL PULSE - Seed Complete")
        print("=" * 60)
        print()
        print("Organization: Default Organization")
        print()
        print("Demo users created (use /api/v1/setup/initialize for production)")
        print()
        print(f"Demo Data:")
        print(f"  Assets:          {len(assets)}")
        print(f"  Vulnerabilities: {len(vulns)}")
        print(f"  Scans:           {len(scans)}")
        print(f"  Alerts:          {len(alerts)}")
        print(f"  Threat Intel:    {len(threat_intel)}")
        print()
        print("Login at: http://localhost:3000")
        print("API docs: http://localhost:8000/api/docs")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
