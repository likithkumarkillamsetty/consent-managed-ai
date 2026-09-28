from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    consent_id: Optional[str] = None
    user_id: Optional[str] = None
    event_type: str
    purpose: Optional[str] = None
    data_scope: Optional[str] = None
    timestamp: datetime
    result: str
    details: Optional[str] = None
