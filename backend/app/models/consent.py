import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database import Base


class Consent(Base):
    __tablename__ = "consents"

    consent_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(100), nullable=False, index=True)
    data_provider = Column(String(100), nullable=False)
    data_consumer = Column(String(100), nullable=False)
    data_scope = Column(String(50), nullable=False, index=True)
    purpose = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
