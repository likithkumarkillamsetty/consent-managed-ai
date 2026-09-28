from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.consent import ConsentCreate, ConsentResponse
from app.schemas.audit import AuditLogResponse
from app.services import consent_service, audit_service

router = APIRouter(prefix="/consents", tags=["Consents"])


@router.post("", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED, summary="Create a new consent request")
def create_consent_endpoint(
    consent_in: ConsentCreate,
    db: Session = Depends(get_db),
):
    return consent_service.create_consent(db, consent_in)


@router.get("", response_model=List[ConsentResponse], summary="List all consents")
def list_consents_endpoint(
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    return consent_service.get_all_consents(db, user_id=user_id, status_filter=status)


@router.get("/{consent_id}", response_model=ConsentResponse, summary="Get consent details by ID")
def get_consent_endpoint(
    consent_id: str,
    db: Session = Depends(get_db),
):
    return consent_service.get_consent_by_id(db, consent_id)


@router.post("/{consent_id}/approve", response_model=ConsentResponse, summary="Approve a pending consent")
def approve_consent_endpoint(
    consent_id: str,
    db: Session = Depends(get_db),
):
    return consent_service.approve_consent(db, consent_id)


@router.post("/{consent_id}/deny", response_model=ConsentResponse, summary="Deny a pending consent")
def deny_consent_endpoint(
    consent_id: str,
    db: Session = Depends(get_db),
):
    return consent_service.deny_consent(db, consent_id)


@router.post("/{consent_id}/revoke", response_model=ConsentResponse, summary="Revoke an approved consent")
def revoke_consent_endpoint(
    consent_id: str,
    db: Session = Depends(get_db),
):
    return consent_service.revoke_consent(db, consent_id)


@router.get("/{consent_id}/audit", response_model=List[AuditLogResponse], summary="Get audit logs for a specific consent")
def get_consent_audit_endpoint(
    consent_id: str,
    db: Session = Depends(get_db),
):
    # Ensure consent exists
    consent_service.get_consent_by_id(db, consent_id)
    return audit_service.get_audit_logs(db, consent_id=consent_id)
