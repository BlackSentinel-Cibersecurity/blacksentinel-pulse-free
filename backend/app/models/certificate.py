from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Certificate(Base):
    """SSL/TLS certificate information."""
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(String(100), index=True)
    fingerprint_sha256 = Column(String(64), unique=True)
    fingerprint_sha1 = Column(String(40))

    # Certificate details
    subject = Column(String(500))
    issuer = Column(String(500))
    subject_alt_names = Column(JSON, default=list)
    common_name = Column(String(255))

    # Validity
    not_before = Column(DateTime)
    not_after = Column(DateTime)
    is_expired = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    days_until_expiry = Column(Integer)

    # Type
    is_self_signed = Column(Boolean, default=False)
    is_wildcard = Column(Boolean, default=False)
    is_ev = Column(Boolean, default=False)
    is_ca = Column(Boolean, default=False)
    key_size = Column(Integer)
    signature_algorithm = Column(String(50))

    # Chain
    chain_depth = Column(Integer, default=0)
    parent_certificate_id = Column(Integer, ForeignKey("certificates.id"))

    # Transparency
    ct_log = Column(JSON, default=list)  # Certificate Transparency logs
    first_seen_ct = Column(DateTime)

    # Source
    source = Column(String(50))  # crt_sh, direct_scan, acme
    raw_cert = Column(Text)  # PEM encoded

    discovered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    asset = relationship("Asset", back_populates="certificates")

    def __repr__(self):
        return f"<Certificate {self.common_name}>"

    @property
    def needs_renewal(self) -> bool:
        if self.days_until_expiry is None:
            return False
        return self.days_until_expiry <= 30
