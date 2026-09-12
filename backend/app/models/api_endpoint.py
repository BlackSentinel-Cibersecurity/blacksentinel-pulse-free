from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIEndpoint(Base):
    """Discovered API endpoint."""
    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
    path = Column(String(1000), nullable=False)
    full_url = Column(String(2000))

    # API Details
    api_version = Column(String(20))
    api_type = Column(String(50))  # rest, graphql, grpc, websocket, soap
    requires_auth = Column(Boolean, default=False)
    auth_type = Column(String(50))  # bearer, basic, api_key, oauth, jwt

    # Response info
    response_format = Column(String(20))  # json, xml, html, binary
    status_codes = Column(JSON, default=list)
    avg_response_time = Column(Float)

    # Security
    has_cors = Column(Boolean, default=False)
    cors_origins = Column(JSON, default=list)
    rate_limited = Column(Boolean, default=False)
    input_validated = Column(Boolean, default=False)
    has_waf = Column(Boolean, default=False)

    # Documentation
    documentation_url = Column(String(500))
    swagger_spec = Column(JSON, default=dict)

    # Discovery
    discovery_method = Column(String(100))
    is_public = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    is_documented = Column(Boolean, default=False)

    # Risk
    risk_score = Column(Float, default=0.0)
    exposure_level = Column(String(20))  # public, internal, restricted

    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, default=datetime.utcnow)

    # Relationships
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    asset = relationship("Asset", back_populates="api_endpoints")

    def __repr__(self):
        return f"<APIEndpoint {self.method} {self.path}>"
