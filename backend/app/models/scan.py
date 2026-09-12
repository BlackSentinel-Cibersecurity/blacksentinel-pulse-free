import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScanType(str, enum.Enum):
    FULL_DISCOVERY = "full_discovery"
    PASSIVE_RECON = "passive_recon"
    ACTIVE_SCAN = "active_scan"
    VULNERABILITY_SCAN = "vulnerability_scan"
    DNS_ENUMERATION = "dns_enumeration"
    PORT_SCAN = "port_scan"
    SSL_SCAN = "ssl_scan"
    WEB_SCAN = "web_scan"
    CLOUD_SCAN = "cloud_scan"
    API_SCAN = "api_scan"
    CREDENTIAL_CHECK = "credential_check"
    CERTIFICATE_TRANSparency = "certificate_transparency"
    OSINT = "osint"
    THREAT_INTEL = "threat_intel"
    COMPLIANCE = "compliance"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class Scan(Base):
    """Scan execution record."""
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(255))
    scan_type = Column(Enum(ScanType), nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, index=True)

    # Configuration
    config = Column(JSON, default=dict)
    targets = Column(JSON, default=list)  # List of asset IDs or target specs
    options = Column(JSON, default=dict)

    # Progress
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(255))
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)

    # Results summary
    assets_found = Column(Integer, default=0)
    vulnerabilities_found = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)

    # Execution details
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    triggered_by = Column(String(100))  # manual, scheduled, api, webhook

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)

    # Metadata
    scan_config_version = Column(String(20))
    engine_version = Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="scans")

    assets = relationship("Asset", secondary="scan_assets", backref="scans")

    def __repr__(self):
        return f"<Scan {self.scan_id} ({self.scan_type})>"

    @property
    def is_running(self) -> bool:
        return self.status == ScanStatus.RUNNING

    @property
    def is_complete(self) -> bool:
        return self.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED)


class ScanAsset(Base):
    """Association between scans and assets discovered during the scan."""
    __tablename__ = "scan_assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_new = Column(Boolean, default=True)

    scan = relationship("Scan", backref="scan_assets")
    asset = relationship("Asset", backref="asset_scans")


class ScanResult(Base):
    """Detailed results from a scan."""
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    result_type = Column(String(100), nullable=False)  # asset, vulnerability, finding, etc.
    data = Column(JSON, nullable=False)
    severity = Column(String(20))
    confidence = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", backref="results")
