import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PolicyType(str, enum.Enum):
    VULNERABILITY = "vulnerability"
    EXPOSURE = "exposure"
    COMPLIANCE = "compliance"
    REMEDIATION = "remediation"
    NOTIFICATION = "notification"
    SCANNING = "scanning"


class Policy(Base):
    """Security policy for automated response and compliance."""

    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    policy_type = Column(Enum(PolicyType), nullable=False)
    is_enabled = Column(Boolean, default=True)

    # Conditions
    conditions = Column(JSON, nullable=False)
    # Example: {"asset_type": "domain", "risk_score": {"gte": 80}}

    # Actions
    actions = Column(JSON, nullable=False)
    # Example: {"alert": true, "notify": ["slack"], "auto_remediate": true}

    # Scope
    scope = Column(JSON, default=dict)
    # Example: {"asset_types": ["domain", "subdomain"], "tags": ["production"]}

    # Priority
    priority = Column(Integer, default=0)
    override_policies = Column(JSON, default=list)

    # State
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    # Audit
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="policies")
    rules = relationship(
        "PolicyRule", back_populates="policy", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Policy {self.name} ({self.policy_type})>"


class PolicyRule(Base):
    """Individual rule within a policy."""

    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)

    # Rule definition
    condition = Column(JSON, nullable=False)
    action = Column(JSON, nullable=False)
    severity = Column(String(20), default="medium")

    # Thresholds
    threshold_count = Column(Integer)
    threshold_window = Column(Integer)  # seconds

    # State
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    policy = relationship("Policy", back_populates="rules")

    def __repr__(self):
        return f"<PolicyRule {self.name}>"
