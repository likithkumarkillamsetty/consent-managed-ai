from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime
from app.database import Base


class TrainingDataRecord(Base):
    __tablename__ = "training_data_records"

    record_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    dataset_name = Column(String(100), nullable=False, index=True)
    transaction_amount = Column(Float, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    average_transaction_amount = Column(Float, nullable=False)
    account_balance = Column(Float, nullable=False)
    transaction_category = Column(String(50), nullable=False)
    fraud_label = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
