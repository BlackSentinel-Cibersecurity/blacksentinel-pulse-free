from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DNSRecord(Base):
    """DNS record associated with an asset."""
    __tablename__ = "dns_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_type = Column(String(10), nullable=False, index=True)  # A, AAAA, CNAME, MX, TXT, NS, SOA, SRV, CAA, PTR
    name = Column(String(500), nullable=False, index=True)
    value = Column(String(500), nullable=False)
    ttl = Column(Integer)
    priority = Column(Integer)

    # DNS Security
    is_dnssec = Column(Boolean, default=False)
    dnssec_algorithm = Column(String(20))

    # Metadata
    nameserver = Column(String(255))
    source = Column(String(50))  # direct, passive, recursive
    is_active = Column(Boolean, default=True)

    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    asset = relationship("Asset", back_populates="dns_records")

    def __repr__(self):
        return f"<DNSRecord {self.record_type} {self.name} -> {self.value}>"
