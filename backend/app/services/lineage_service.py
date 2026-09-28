from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.training_lineage import TrainingLineage
from app.models.training_batch import TrainingBatch
from app.schemas.training_lineage import (
    TrainingBatchLineageResponse,
    TrainingLineageRecordResponse,
)


def get_batch_lineage(
    db: Session,
    batch_id: str,
) -> Optional[TrainingBatchLineageResponse]:
    batch = db.query(TrainingBatch).filter(TrainingBatch.batch_id == batch_id).first()
    if not batch:
        return None

    lineage_records = (
        db.query(TrainingLineage)
        .filter(TrainingLineage.batch_id == batch_id)
        .order_by(TrainingLineage.record_id.asc())
        .all()
    )

    allowed_count = sum(1 for r in lineage_records if r.access_result == "ALLOWED")
    blocked_count = sum(1 for r in lineage_records if r.access_result == "BLOCKED")

    return TrainingBatchLineageResponse(
        batch_id=batch_id,
        total_records=len(lineage_records),
        allowed_records=allowed_count,
        blocked_records=blocked_count,
        records=lineage_records,
    )
