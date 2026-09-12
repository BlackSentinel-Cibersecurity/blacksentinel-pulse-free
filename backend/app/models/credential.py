from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CredentialExposure(Base):
    """Exposed or leaked credentials found during discovery."""
    __tablename__ = "credential_exposures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_type = Column(String(50), nullable=False)  # password, api_key, token, private_key, etc.
    username = Column(String(255))
    email = Column(String(255))
    service = Column(String(255))
    domain = Column(String(255))

    # Exposure details
    source = Column(String(100))  # github, paste, dark_web, breach_db, etc.
    source_url = Column(String(500))
    exposure_type = Column(String(50))  # public, private, dark_web, paste, code_repo

    # Risk
    risk_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=False)
    last_validated = Column(DateTime)

    # Evidence
    evidence_hash = Column(String(255))  # Hash of the actual credential (never store plaintext)
    evidence_metadata = Column(JSON, default=dict)
    redacted_preview = Column(String(255))  # Partially redacted for display

    # Context
    repository = Column(String(500))
    file_path = Column(String(500))
    line_number = Column(Integer)
    commit_hash = Column(String(40))

    discovered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    asset = relationship("Asset", back_populates="credential_exposures")

    def __repr__(self):
        return f"<CredentialExposure {self.credential_type} ({self.source})>"

    @property
    def is_credential_valid(self) -> bool:
        return self.is_active and self.is_valid
