from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.gate import GateCheckRequest, GateCheckResponse
from app.services import consent_gate

router = APIRouter(prefix="/consent-gate", tags=["Consent Gate"])


@router.post("/check", response_model=GateCheckResponse, summary="Validate access permissions through the Consent Gate")
def check_access_endpoint(
    request: GateCheckRequest,
    db: Session = Depends(get_db),
):
    return consent_gate.check_access(
        db=db,
        user_id=request.user_id,
        data_scope=request.data_scope,
        purpose=request.purpose,
    )
