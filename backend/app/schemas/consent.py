from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataScopeEnum(str, Enum):
    CUSTOMER_PROFILE = "CUSTOMER_PROFILE"
    TRANSACTION_DATA = "TRANSACTION_DATA"
    HEALTH_DATA = "HEALTH_DATA"
    LOCATION_DATA = "LOCATION_DATA"


class PurposeEnum(str, Enum):
    AI_TRAINING = "AI_TRAINING"
    FRAUD_DETECTION = "FRAUD_DETECTION"
    ANALYTICS = "ANALYTICS"
    MARKETING = "MARKETING"


class ConsentStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ConsentCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "user001"})
    data_provider: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Bank"})
    data_consumer: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "AI Platform"})
    data_scope: str = Field(..., json_schema_extra={"example": "TRANSACTION_DATA"})
    purpose: str = Field(..., json_schema_extra={"example": "AI_TRAINING"})
    expires_at: datetime = Field(..., json_schema_extra={"example": "2027-01-01T00:00:00Z"})

    @field_validator("data_scope")
    @classmethod
    def validate_data_scope(cls, v: str) -> str:
        valid_scopes = [e.value for e in DataScopeEnum]
        if v not in valid_scopes:
            raise ValueError(f"Invalid data_scope. Must be one of {valid_scopes}")
        return v

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        valid_purposes = [e.value for e in PurposeEnum]
        if v not in valid_purposes:
            raise ValueError(f"Invalid purpose. Must be one of {valid_purposes}")
        return v


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consent_id: str
    user_id: str
    data_provider: str
    data_consumer: str
    data_scope: str
    purpose: str
    status: str
    created_at: datetime
    expires_at: datetime
    approved_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
