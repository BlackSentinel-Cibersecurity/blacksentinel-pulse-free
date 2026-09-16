import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, JSON

from app.core.database import Base


class IncidentSeverity(str, enum.Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low
    P5 = "P5"  # Info


class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


class Incident(Base):
    """Security incident triggered by Pulse detection."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(Enum(IncidentSeverity), nullable=False, index=True)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.DETECTED)

    # Classification
    incident_type = Column(
        String(100)
    )  # data_breach, unauthorized_access, malware, etc.
    category = Column(String(100))  # technical, physical, human
    ttps = Column(JSON, default=list)  # MITRE ATT&CK

    # Impact
    affected_assets = Column(JSON, default=list)
    affected_users = Column(Integer, default=0)
    data_classification = Column(
        String(50)
    )  # public, internal, confidential, restricted
    estimated_impact = Column(String(50))

    # Response
    assigned_to = Column(Integer, ForeignKey("users.id"))
    response_team = Column(JSON, default=list)
    timeline = Column(JSON, default=list)  # Array of events
    actions_taken = Column(JSON, default=list)

    # Evidence
    evidence = Column(JSON, default=list)
    iocs = Column(JSON, default=list)  # Indicators of Compromise
    raw_data = Column(JSON, default=dict)

    # Metrics
    time_to_detect = Column(Integer)  # minutes
    time_to_contain = Column(Integer)  # minutes
    time_to_recover = Column(Integer)  # minutes

    detected_at = Column(DateTime, default=datetime.utcnow)
    triaged_at = Column(DateTime)
    contained_at = Column(DateTime)
    eradicated_at = Column(DateTime)
    recovered_at = Column(DateTime)
    closed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Incident {self.incident_id} ({self.severity})>"
