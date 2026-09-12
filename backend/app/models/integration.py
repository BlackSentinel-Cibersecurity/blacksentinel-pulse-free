import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "connected"
    ERROR = "error"
    PENDING = "pending"
    DISABLED = "disabled"


class Integration(Base):
    """External integration configuration. API keys encrypted at rest."""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False, index=True)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.PENDING)
    is_enabled = Column(Boolean, default=True)

    # Encrypted configuration - API keys stored encrypted via vault module
    config_encrypted = Column(JSON, nullable=False, default=dict)

    # Sync state
    last_sync = Column(DateTime)
    last_sync_status = Column(String(50))
    sync_error = Column(Text)
    assets_synced = Column(Integer, default=0)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", backref="integrations")

    @property
    def config(self):
        """Decrypt config for internal use only. NEVER return to API."""
        from app.core.vault import decrypt_config
        return decrypt_config(self.config_encrypted or {})

    def set_config(self, plaintext_config: dict):
        """Encrypt and store config. Called when saving from API."""
        from app.core.vault import encrypt_config
        self.config_encrypted = encrypt_config(plaintext_config)

    @property
    def config_masked(self):
        """Return config with all secrets masked for API responses."""
        from app.core.vault import mask_dict_secrets
        return mask_dict_secrets(self.config_encrypted or {})

    def __repr__(self):
        return f"<Integration {self.provider}:{self.name}>"
