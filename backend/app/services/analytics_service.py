from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.consent import Consent
from app.models.audit import AuditLog
from app.schemas.analytics import AnalyticsSummary
from app.services.consent_service import check_and_update_expiry


def get_analytics_summary(db: Session) -> AnalyticsSummary:
    # Refresh statuses for any recently expired consents
    all_consents = db.query(Consent).all()
    for c in all_consents:
        check_and_update_expiry(db, c)

    total_consents = db.query(Consent).count()
    pending_consents = db.query(Consent).filter(Consent.status == "PENDING").count()
    approved_consents = db.query(Consent).filter(Consent.status == "APPROVED").count()
    denied_consents = db.query(Consent).filter(Consent.status == "DENIED").count()
    revoked_consents = db.query(Consent).filter(Consent.status == "REVOKED").count()
    expired_consents = db.query(Consent).filter(Consent.status == "EXPIRED").count()

    total_access_allowed = db.query(AuditLog).filter(
        (AuditLog.event_type == "ACCESS_ALLOWED") | (AuditLog.result == "ALLOWED")
    ).count()

    total_access_blocked = db.query(AuditLog).filter(
        (AuditLog.event_type == "ACCESS_BLOCKED") | (AuditLog.result == "BLOCKED")
    ).count()

    return AnalyticsSummary(
        total_consents=total_consents,
        pending_consents=pending_consents,
        approved_consents=approved_consents,
        denied_consents=denied_consents,
        revoked_consents=revoked_consents,
        expired_consents=expired_consents,
        total_access_allowed=total_access_allowed,
        total_access_blocked=total_access_blocked,
    )
