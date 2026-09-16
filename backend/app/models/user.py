import enum
import secrets
import random
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
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    # Leadership & Management
    SUPER_ADMIN = "super_admin"
    CISO = "ciso"
    SECURITY_DIRECTOR = "security_director"
    SOC_MANAGER = "soc_manager"
    SOC_SUPERVISOR = "soc_supervisor"
    SECURITY_INFORMATION_MANAGER = "security_information_manager"
    SECURITY_COMPLIANCE_MANAGER = "security_compliance_manager"

    # SOC Analysts
    SOC_ANALYST_1 = "soc_analyst_1"
    SOC_ANALYST_2 = "soc_analyst_2"
    SOC_ANALYST_3 = "soc_analyst_3"
    SOC_ANALYST_4 = "soc_analyst_4"
    SOC_ANALYST_5 = "soc_analyst_5"

    # Security Analysts
    SECURITY_ANALYST_1 = "security_analyst_1"
    SECURITY_ANALYST_2 = "security_analyst_2"
    SECURITY_ANALYST_3 = "security_analyst_3"
    SECURITY_ANALYST_4 = "security_analyst_4"
    SECURITY_ANALYST_5 = "security_analyst_5"

    # Specialized Roles
    INCIDENT_RESPONDER = "incident_responder"
    THREAT_HUNTER = "threat_hunter"
    FORENSICS_ANALYST = "forensics_analyst"
    VULNERABILITY_ANALYST = "vulnerability_analyst"
    PENETRATION_TESTER = "penetration_tester"
    SECURITY_ENGINEER = "security_engineer"
    SECURITY_ARCHITECT = "security_architect"
    CLOUD_SECURITY_ENGINEER = "cloud_security_engineer"
    DEVSECOPS_ENGINEER = "devsecops_engineer"

    # Infrastructure & Support
    SYSTEM_ADMINISTRATOR = "system_administrator"
    NETWORK_ENGINEER = "network_engineer"
    IT_ADMINISTRATOR = "it_administrator"

    # Access Levels
    VIEWER = "viewer"
    AUDITOR = "auditor"
    API = "api"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    black_id = Column(String(20), unique=True, nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32))
    totp_secret = Column(String(64))
    totp_enabled = Column(Boolean, default=False)
    temp_password = Column(String(255), nullable=True)
    temp_password_plain = Column(String(255), nullable=True)
    current_password_plain = Column(String(255), nullable=True)
    force_password_change = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization_id = Column(Integer, ForeignKey("organizations.id"))
    organization = relationship("Organization", back_populates="users")

    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    @staticmethod
    def generate_black_id(first_name: str, last_name: str) -> str:
        initials = (first_name[0] + last_name[0]).upper()
        numbers = f"{random.randint(1000, 9999)}"
        return f"{initials}{numbers}"

    @staticmethod
    def generate_username(first_name: str, last_name: str) -> str:
        nums = f"{random.randint(10, 99)}"
        return f"{first_name.lower()}.{last_name.lower()}{nums}"

    @staticmethod
    def generate_temp_password() -> str:
        return f"Temp{secrets.token_urlsafe(8)}!"


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="api_keys")

    permissions = Column(Text)

    def __repr__(self):
        return f"<APIKey {self.name}>"
