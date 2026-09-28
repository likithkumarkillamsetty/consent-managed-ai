from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TrainingLineageRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lineage_id: str
    batch_id: str
    record_id: str
    user_id: str
    consent_id: Optional[str] = None
    purpose: str
    data_scope: str
    consent_status: Optional[str] = None
    access_result: str  # ALLOWED or BLOCKED
    reason: str
    timestamp: datetime


class TrainingBatchLineageResponse(BaseModel):
    batch_id: str
    total_records: int
    allowed_records: int
    blocked_records: int
    records: List[TrainingLineageRecordResponse]
