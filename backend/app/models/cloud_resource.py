import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, JSON, Float
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CloudProvider(str, enum.Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITAL_OCEAN = "digital_ocean"
    ALIBABA = "alibaba"
    ORACLE = "oracle"
    IBM = "ibm"
    OTHER = "other"


class CloudResource(Base):
    """Cloud infrastructure resource discovered across providers."""
    __tablename__ = "cloud_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(Enum(CloudProvider), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)  # ec2, s3, lambda, aks, etc.
    resource_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    arn = Column(String(500))
    resource_group = Column(String(255))
    region = Column(String(50))
    availability_zone = Column(String(50))

    # Configuration
    config = Column(JSON, default=dict)
    tags = Column(JSON, default=dict)
    labels = Column(JSON, default=dict)

    # Network
    public_ip = Column(String(45))
    private_ip = Column(String(45))
    vpc_id = Column(String(255))
    subnet_id = Column(String(255))
    security_groups = Column(JSON, default=list)

    # Access
    is_public = Column(Boolean, default=False)
    is_internet_facing = Column(Boolean, default=False)
    iam_roles = Column(JSON, default=list)
    permissions = Column(JSON, default=list)

    # Cost
    monthly_cost = Column(Float)
    currency = Column(String(3), default="USD")

    # Compliance
    compliance_status = Column(JSON, default=dict)
    encryption_enabled = Column(Boolean, default=True)
    logging_enabled = Column(Boolean, default=True)

    # Risk
    risk_score = Column(Float, default=0.0)
    misconfigurations = Column(JSON, default=list)

    # Lifecycle
    state = Column(String(50))  # running, stopped, terminated, etc.
    created_at_cloud = Column(DateTime)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_synced = Column(DateTime)

    # Relationships
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    asset = relationship("Asset", back_populates="cloud_resources")

    def __repr__(self):
        return f"<CloudResource {self.provider}:{self.resource_type}:{self.resource_id}>"
