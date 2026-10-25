import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from app.database import Base


class TrainingBatch(Base):
    __tablename__ = "training_batches"

    batch_id = Column(
        String(50),
        primary_key=True,
        default=lambda: f"BATCH-{str(uuid.uuid4())[:8].upper()}",
        index=True,
    )
    dataset_name = Column(String(100), nullable=False, index=True)
    purpose = Column(String(50), nullable=False, index=True)
    data_scope = Column(String(50), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="CREATED", index=True)  # CREATED, VALIDATING, READY, TRAINING, COMPLETED, FAILED
    total_records = Column(Integer, nullable=False, default=0)
    allowed_records = Column(Integer, nullable=False, default=0)
    blocked_records = Column(Integer, nullable=False, default=0)
    model_type = Column(String(50), nullable=False, default="logistic_regression")
    model_path = Column(String(255), nullable=True)
    dataset_path = Column(String(255), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    privacy_enabled = Column(Boolean, nullable=False, default=False)
    privacy_mechanism = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
