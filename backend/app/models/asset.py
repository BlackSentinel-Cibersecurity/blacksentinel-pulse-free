import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON, Float
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AssetType(str, enum.Enum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    WEB_APPLICATION = "web_application"
    API_ENDPOINT = "api_endpoint"
    CLOUD_RESOURCE = "cloud_resource"
    CONTAINER = "container"
    KUBERNETES = "kubernetes"
    SERVERLESS = "serverless"
    DATABASE = "database"
    DNS_RECORD = "dns_record"
    SSL_CERTIFICATE = "ssl_certificate"
    EMAIL_SERVER = "email_server"
    VPN = "vpn"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    CDN = "cdn"
    REPOSITORY = "repository"
    CI_CD_PIPELINE = "ci_cd_pipeline"
    IDENTITY_PROVIDER = "identity_provider"
    SAAS_APPLICATION = "saas_application"
    IOT_DEVICE = "iot_device"
    OT_DEVICE = "ot_device"
    CODEC = "codec"
    DOCUMENT = "document"
    USER = "user"
    GROUP = "group"
    PERMISSION = "permission"
    CREDENTIAL = "credential"
    UNKNOWN = "unknown"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MONITORED = "monitoring"
    UNKNOWN = "unknown"
    DECOMMISSIONED = "decommissioned"
    COMPROMISED = "compromised"


class Asset(Base):
    """Core asset model representing any discovered entity in the attack surface."""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    status = Column(Enum(AssetStatus), default=AssetStatus.ACTIVE)

    # Risk scoring
    risk_score = Column(Float, default=0.0, index=True)
    risk_factors = Column(JSON, default=dict)
    criticality = Column(String(20), default="medium")  # critical, high, medium, low, info

    # Discovery metadata
    discovery_method = Column(String(100))  # passive, active, osint, integration
    discovery_source = Column(String(100))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_scan = Column(DateTime)
    scan_count = Column(Integer, default=0)

    # Core data
    raw_data = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    extra_metadata = Column(JSON, default=dict)

    # Network data
    ip_address = Column(String(45))
    port = Column(Integer)
    protocol = Column(String(20))
    hostname = Column(String(500))

    # Location
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    asn = Column(Integer)
    isp = Column(String(255))

    # Ownership
    whois_data = Column(JSON, default=dict)
    registrar = Column(String(255))
    registrant_org = Column(String(255))

    # Expiration
    expires_at = Column(DateTime)
    renewal_cost = Column(Float)

    # Relationships
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="assets")

    parent_id = Column(Integer, ForeignKey("assets.id"))
    parent = relationship("Asset", remote_side=[id], backref="children")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vulnerabilities = relationship("Vulnerability", back_populates="asset")
    certificates = relationship("Certificate", back_populates="asset")
    dns_records = relationship("DNSRecord", back_populates="asset")
    cloud_resources = relationship("CloudResource", back_populates="asset")
    api_endpoints = relationship("APIEndpoint", back_populates="asset")
    credential_exposures = relationship("CredentialExposure", back_populates="asset")

    def __repr__(self):
        return f"<Asset {self.name} ({self.asset_type})>"


class AssetRelationship(Base):
    """Relationship between two assets (also stored in Neo4j for graph queries)."""
    __tablename__ = "asset_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    target_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    relationship_type = Column(String(100), nullable=False)  # resolves_to, points_to, hosts, contains, etc.
    confidence = Column(Float, default=1.0)
    rel_metadata = Column(JSON, default=dict)
    is_bidirectional = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, default=datetime.utcnow)

    source_asset = relationship("Asset", foreign_keys=[source_asset_id])
    target_asset = relationship("Asset", foreign_keys=[target_asset_id])

    def __repr__(self):
        return f"<AssetRelationship {self.relationship_type}>"


class AssetTag(Base):
    """Tags for asset classification and filtering."""
    __tablename__ = "asset_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False)
    value = Column(String(255))
    color = Column(String(7))  # hex color

    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    asset = relationship("Asset", backref="asset_tags")

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AssetTag {self.key}={self.value}>"


class AssetMetadata(Base):
    """Additional metadata for specific asset types."""
    __tablename__ = "asset_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    metadata_type = Column(String(100), nullable=False)  # ssl_info, whois, dns, cloud, etc.
    data = Column(JSON, nullable=False)
    source = Column(String(100))
    collected_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", backref="metadata_entries")

    def __repr__(self):
        return f"<AssetMetadata {self.metadata_type}>"
