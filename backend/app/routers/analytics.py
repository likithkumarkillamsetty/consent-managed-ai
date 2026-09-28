from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import AnalyticsSummary
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary, summary="Get summary statistics of consents and access checks")
def get_analytics_summary_endpoint(
    db: Session = Depends(get_db),
):
    return analytics_service.get_analytics_summary(db)
