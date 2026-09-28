import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    consent_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    purpose = Column(String(50), nullable=True)
    data_scope = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    result = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
