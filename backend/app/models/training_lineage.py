import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database import Base


class TrainingLineage(Base):
    __tablename__ = "training_lineage"

    lineage_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    consent_id = Column(String(36), nullable=True, index=True)
    purpose = Column(String(50), nullable=False)
    data_scope = Column(String(50), nullable=False)
    consent_status = Column(String(30), nullable=True)
    access_result = Column(String(20), nullable=False)  # ALLOWED or BLOCKED
    reason = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
