from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.consent import Consent
from app.schemas.gate import GateCheckResponse
from app.services.consent_service import check_and_update_expiry
from app.services.audit_service import create_audit_log


def check_access(
    db: Session,
    user_id: str,
    data_scope: str,
    purpose: str,
) -> GateCheckResponse:
    # 1. Check if any consents exist for this user
    user_consents = db.query(Consent).filter(Consent.user_id == user_id).order_by(Consent.created_at.desc()).all()

    if not user_consents:
        reason = "NO_CONSENT"
        create_audit_log(
            db=db,
            event_type="ACCESS_BLOCKED",
            consent_id=None,
            user_id=user_id,
            purpose=purpose,
            data_scope=data_scope,
            result="BLOCKED",
            details=reason,
        )
        return GateCheckResponse(allowed=False, reason=reason)

    # Update any expired consents in real-time
    for c in user_consents:
        check_and_update_expiry(db, c)

    # 2. Check for matching scope and purpose
    exact_match = next(
        (c for c in user_consents if c.data_scope == data_scope and c.purpose == purpose),
        None,
    )

    if exact_match:
        if exact_match.status == "APPROVED":
            # Access granted
            create_audit_log(
                db=db,
                event_type="ACCESS_ALLOWED",
                consent_id=exact_match.consent_id,
                user_id=user_id,
                purpose=purpose,
                data_scope=data_scope,
                result="ALLOWED",
                details="Valid consent",
            )
            return GateCheckResponse(allowed=True, reason="Valid consent")

        elif exact_match.status == "REVOKED":
            reason = "CONSENT_REVOKED"
            create_audit_log(
                db=db,
                event_type="ACCESS_BLOCKED",
                consent_id=exact_match.consent_id,
                user_id=user_id,
                purpose=purpose,
                data_scope=data_scope,
                result="BLOCKED",
                details=reason,
            )
            return GateCheckResponse(allowed=False, reason=reason)

        elif exact_match.status == "EXPIRED":
            reason = "CONSENT_EXPIRED"
            create_audit_log(
                db=db,
                event_type="ACCESS_BLOCKED",
                consent_id=exact_match.consent_id,
                user_id=user_id,
                purpose=purpose,
                data_scope=data_scope,
                result="BLOCKED",
                details=reason,
            )
            return GateCheckResponse(allowed=False, reason=reason)

        else:  # PENDING or DENIED
            reason = "CONSENT_NOT_APPROVED"
            create_audit_log(
                db=db,
                event_type="ACCESS_BLOCKED",
                consent_id=exact_match.consent_id,
                user_id=user_id,
                purpose=purpose,
                data_scope=data_scope,
                result="BLOCKED",
                details=reason,
            )
            return GateCheckResponse(allowed=False, reason=reason)

    # 3. Check for matching scope (but mismatched purpose)
    scope_match = next((c for c in user_consents if c.data_scope == data_scope), None)
    if scope_match:
        if scope_match.status == "APPROVED":
            reason = "PURPOSE_NOT_ALLOWED"
        elif scope_match.status == "REVOKED":
            reason = "CONSENT_REVOKED"
        elif scope_match.status == "EXPIRED":
            reason = "CONSENT_EXPIRED"
        else:
            reason = "CONSENT_NOT_APPROVED"

        create_audit_log(
            db=db,
            event_type="ACCESS_BLOCKED",
            consent_id=scope_match.consent_id,
            user_id=user_id,
            purpose=purpose,
            data_scope=data_scope,
            result="BLOCKED",
            details=reason,
        )
        return GateCheckResponse(allowed=False, reason=reason)

    # 4. Check for matching purpose (but mismatched scope)
    purpose_match = next((c for c in user_consents if c.purpose == purpose), None)
    if purpose_match:
        if purpose_match.status == "APPROVED":
            reason = "DATA_SCOPE_NOT_ALLOWED"
        elif purpose_match.status == "REVOKED":
            reason = "CONSENT_REVOKED"
        elif purpose_match.status == "EXPIRED":
            reason = "CONSENT_EXPIRED"
        else:
            reason = "CONSENT_NOT_APPROVED"

        create_audit_log(
            db=db,
            event_type="ACCESS_BLOCKED",
            consent_id=purpose_match.consent_id,
            user_id=user_id,
            purpose=purpose,
            data_scope=data_scope,
            result="BLOCKED",
            details=reason,
        )
        return GateCheckResponse(allowed=False, reason=reason)

    # 5. Fallback if user has consent but neither scope nor purpose matched
    fallback_consent = user_consents[0]
    reason = "DATA_SCOPE_NOT_ALLOWED"
    create_audit_log(
        db=db,
        event_type="ACCESS_BLOCKED",
        consent_id=fallback_consent.consent_id,
        user_id=user_id,
        purpose=purpose,
        data_scope=data_scope,
        result="BLOCKED",
        details=reason,
    )
    return GateCheckResponse(allowed=False, reason=reason)
