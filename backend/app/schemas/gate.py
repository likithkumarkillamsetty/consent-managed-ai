from pydantic import BaseModel, Field


class GateCheckRequest(BaseModel):
    user_id: str = Field(..., min_length=1, json_schema_extra={"example": "user001"})
    data_scope: str = Field(..., min_length=1, json_schema_extra={"example": "TRANSACTION_DATA"})
    purpose: str = Field(..., min_length=1, json_schema_extra={"example": "AI_TRAINING"})


class GateCheckResponse(BaseModel):
    allowed: bool
    reason: str
