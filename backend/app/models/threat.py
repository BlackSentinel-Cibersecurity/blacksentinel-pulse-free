import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON, Float
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ThreatType(str, enum.Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    C2 = "c2"
    BOTNET = "botnet"
    DATA_BREACH = "data_breach"
    CREDENTIAL_STUFFING = "credential_stuffing"
    DDoS = "ddos"
    APT = "apt"
    SUPPLY_CHAIN = "supply_chain"
    ZERO_DAY = "zero_day"
    EXPLOIT = "exploit"
    OTHER = "other"


class ThreatIntelligence(Base):
    """Threat intelligence data associated with assets."""
    __tablename__ = "threat_intelligence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), index=True)
    threat_type = Column(Enum(ThreatType), nullable=False)
    confidence = Column(Float, default=0.0)
    severity = Column(String(20), default="medium")

    # Indicators
    indicators = Column(JSON, default=list)  # IPs, domains, hashes, URLs
    indicator_type = Column(String(50))  # ip, domain, hash, url, email
    indicator_value = Column(String(500), index=True)

    # Threat details
    title = Column(String(500))
    description = Column(Text)
    ttps = Column(JSON, default=list)  # MITRE ATT&CK TTPs
    tags = Column(JSON, default=list)

    # Source
    source = Column(String(100))
    source_url = Column(String(500))
    source_reliability = Column(Float)  # 0-1 scale
    raw_data = Column(JSON, default=dict)

    # Dates
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Matched assets
    asset_id = Column(Integer, ForeignKey("assets.id"), index=True)
    asset = relationship("Asset", backref="threat_intel_entries")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ThreatIntelligence {self.threat_type} ({self.source})>"


class ThreatFeed(Base):
    """External threat intelligence feed configuration."""
    __tablename__ = "threat_feeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    feed_type = Column(String(100), nullable=False)  # stix, csv, api, rss
    url = Column(String(500))
    api_key = Column(String(255))
    config = Column(JSON, default=dict)

    is_enabled = Column(Boolean, default=True)
    last_fetched = Column(DateTime)
    fetch_interval = Column(Integer, default=3600)  # seconds

    entries_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ThreatFeed {self.name}>"
