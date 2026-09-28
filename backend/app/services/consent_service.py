from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.consent import Consent
from app.schemas.consent import ConsentCreate
from app.services.audit_service import create_audit_log


def _normalize_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_and_update_expiry(db: Session, consent: Consent) -> Consent:
    now = datetime.now(timezone.utc)
    expires_at = _normalize_utc(consent.expires_at)
    if consent.status in ["PENDING", "APPROVED"] and now > expires_at:
        consent.status = "EXPIRED"
        db.commit()
        db.refresh(consent)
        create_audit_log(
            db=db,
            event_type="CONSENT_EXPIRED",
            consent_id=consent.consent_id,
            user_id=consent.user_id,
            purpose=consent.purpose,
            data_scope=consent.data_scope,
            result="EXPIRED",
            details="Consent validity period has expired",
        )
    return consent


def create_consent(db: Session, consent_in: ConsentCreate) -> Consent:
    expires_at_utc = _normalize_utc(consent_in.expires_at)
    now = datetime.now(timezone.utc)
    if expires_at_utc <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expires_at must be in the future",
        )

    consent = Consent(
        user_id=consent_in.user_id,
        data_provider=consent_in.data_provider,
        data_consumer=consent_in.data_consumer,
        data_scope=consent_in.data_scope,
        purpose=consent_in.purpose,
        status="PENDING",
        created_at=now,
        expires_at=expires_at_utc.replace(tzinfo=None),  # store standard UTC
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    create_audit_log(
        db=db,
        event_type="CONSENT_CREATED",
        consent_id=consent.consent_id,
        user_id=consent.user_id,
        purpose=consent.purpose,
        data_scope=consent.data_scope,
        result="SUCCESS",
        details="Consent request created with PENDING status",
    )
    return consent


def get_consent_by_id(db: Session, consent_id: str) -> Consent:
    consent = db.query(Consent).filter(Consent.consent_id == consent_id).first()
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consent with ID '{consent_id}' not found",
        )
    return check_and_update_expiry(db, consent)


def get_all_consents(
    db: Session,
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[Consent]:
    query = db.query(Consent)
    if user_id:
        query = query.filter(Consent.user_id == user_id)
    if status_filter:
        query = query.filter(Consent.status == status_filter)

    consents = query.order_by(Consent.created_at.desc()).all()
    updated_consents = []
    for c in consents:
        updated_consents.append(check_and_update_expiry(db, c))
    return updated_consents


def approve_consent(db: Session, consent_id: str) -> Consent:
    consent = get_consent_by_id(db, consent_id)

    if consent.status == "EXPIRED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve an expired consent",
        )

    if consent.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot approve consent with status '{consent.status}'. Only PENDING consents can be approved.",
        )

    now = datetime.now(timezone.utc)
    consent.status = "APPROVED"
    consent.approved_at = now.replace(tzinfo=None)
    db.commit()
    db.refresh(consent)

    create_audit_log(
        db=db,
        event_type="CONSENT_APPROVED",
        consent_id=consent.consent_id,
        user_id=consent.user_id,
        purpose=consent.purpose,
        data_scope=consent.data_scope,
        result="SUCCESS",
        details="Consent has been approved by user/custodian",
    )
    return consent


def deny_consent(db: Session, consent_id: str) -> Consent:
    consent = get_consent_by_id(db, consent_id)

    if consent.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot deny consent with status '{consent.status}'. Only PENDING consents can be denied.",
        )

    consent.status = "DENIED"
    db.commit()
    db.refresh(consent)

    create_audit_log(
        db=db,
        event_type="CONSENT_DENIED",
        consent_id=consent.consent_id,
        user_id=consent.user_id,
        purpose=consent.purpose,
        data_scope=consent.data_scope,
        result="SUCCESS",
        details="Consent request was denied",
    )
    return consent


def revoke_consent(db: Session, consent_id: str) -> Consent:
    consent = get_consent_by_id(db, consent_id)

    if consent.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot revoke consent with status '{consent.status}'. Only APPROVED consents can be revoked.",
        )

    now = datetime.now(timezone.utc)
    consent.status = "REVOKED"
    consent.revoked_at = now.replace(tzinfo=None)
    db.commit()
    db.refresh(consent)

    create_audit_log(
        db=db,
        event_type="CONSENT_REVOKED",
        consent_id=consent.consent_id,
        user_id=consent.user_id,
        purpose=consent.purpose,
        data_scope=consent.data_scope,
        result="SUCCESS",
        details="Consent has been revoked; future access requests will be blocked",
    )
    return consent
