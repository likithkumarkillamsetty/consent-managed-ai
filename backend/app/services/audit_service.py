from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def create_audit_log(
    db: Session,
    event_type: str,
    consent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    purpose: Optional[str] = None,
    data_scope: Optional[str] = None,
    result: str = "SUCCESS",
    details: Optional[str] = None,
) -> AuditLog:
    log_entry = AuditLog(
        consent_id=consent_id,
        user_id=user_id,
        event_type=event_type,
        purpose=purpose,
        data_scope=data_scope,
        timestamp=datetime.now(timezone.utc),
        result=result,
        details=details,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    consent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    query = db.query(AuditLog)
    if consent_id:
        query = query.filter(AuditLog.consent_id == consent_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
