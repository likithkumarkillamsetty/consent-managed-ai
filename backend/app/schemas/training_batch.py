from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TrainingBatchCreateRequest(BaseModel):
    dataset_name: str = Field(
        default="transaction_fraud_dataset",
        min_length=1,
        json_schema_extra={"example": "transaction_fraud_dataset"},
    )
    data_scope: str = Field(
        default="TRANSACTION_DATA",
        min_length=1,
        json_schema_extra={"example": "TRANSACTION_DATA"},
    )
    purpose: str = Field(
        default="AI_TRAINING",
        min_length=1,
        json_schema_extra={"example": "AI_TRAINING"},
    )
    model_type: str = Field(
        default="logistic_regression",
        min_length=1,
        json_schema_extra={"example": "logistic_regression"},
    )


class TrainingBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: str
    dataset_name: str
    purpose: str
    data_scope: str
    status: str
    total_records: int
    allowed_records: int
    blocked_records: int
    model_type: str
    model_path: Optional[str] = None
    dataset_path: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TrainingBatchListResponse(BaseModel):
    total_batches: int
    batches: List[TrainingBatchResponse]
