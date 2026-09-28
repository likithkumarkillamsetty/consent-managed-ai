from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.audit import AuditLogResponse
from app.services import audit_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogResponse], summary="Retrieve system audit logs")
def get_audit_logs_endpoint(
    consent_id: Optional[str] = Query(None, description="Filter by consent_id"),
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs to return"),
    db: Session = Depends(get_db),
):
    return audit_service.get_audit_logs(
        db=db,
        consent_id=consent_id,
        user_id=user_id,
        limit=limit,
    )
