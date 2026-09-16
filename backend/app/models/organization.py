from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    logo_url = Column(String(500))
    website = Column(String(500))
    industry = Column(String(100))
    size = Column(String(50))  # startup, small, medium, large, enterprise
    plan = Column(String(50), default="professional")  # free, professional, enterprise
    is_active = Column(Boolean, default=True)

    # Settings
    settings = Column(JSON, default=dict)
    notification_config = Column(JSON, default=dict)

    # Limits
    max_assets = Column(Integer, default=10000)
    max_users = Column(Integer, default=10)
    max_scans_per_day = Column(Integer, default=100)

    # Billing
    stripe_customer_id = Column(String(255))
    subscription_id = Column(String(255))
    subscription_status = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("OrganizationMember", back_populates="organization")
    users = relationship("User", back_populates="organization")
    assets = relationship("Asset", back_populates="organization")
    scans = relationship("Scan", back_populates="organization")
    policies = relationship("Policy", back_populates="organization")
    alerts = relationship("Alert", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User")

    def __repr__(self):
        return f"<OrganizationMember org={self.organization_id} user={self.user_id}>"
