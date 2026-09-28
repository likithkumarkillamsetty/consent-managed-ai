from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TrainingDataRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_id: str = Field(..., json_schema_extra={"example": "R001"})
    user_id: str = Field(..., json_schema_extra={"example": "user001"})
    dataset_name: str = Field(..., json_schema_extra={"example": "transaction_fraud_dataset"})
    transaction_amount: float = Field(..., json_schema_extra={"example": 2500.0})
    transaction_count: int = Field(..., json_schema_extra={"example": 5})
    average_transaction_amount: float = Field(..., json_schema_extra={"example": 500.0})
    account_balance: float = Field(..., json_schema_extra={"example": 12000.0})
    transaction_category: str = Field(..., json_schema_extra={"example": "ONLINE"})
    fraud_label: int = Field(..., json_schema_extra={"example": 0})
    created_at: Optional[datetime] = None


class DatasetInfoResponse(BaseModel):
    dataset_name: str
    total_records: int
    unique_users: int
    fraud_count: int
    legit_count: int


class DatasetPreviewResponse(BaseModel):
    dataset_name: str
    total_records: int
    preview_count: int
    records: List[TrainingDataRecordSchema]


class DatasetSeedResponse(BaseModel):
    message: str
    dataset_name: str
    records_seeded: int
    total_records: int
