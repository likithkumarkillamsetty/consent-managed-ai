import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.training_data import (
    DatasetInfoResponse,
    DatasetPreviewResponse,
    DatasetSeedResponse,
)
from app.schemas.training_batch import (
    TrainingBatchCreateRequest,
    TrainingBatchResponse,
)
from app.schemas.training_lineage import TrainingBatchLineageResponse
from app.services import training_data_service, training_service, lineage_service

router = APIRouter(prefix="/training", tags=["Module 2: ML Training Pipeline & Lineage"])


# -------------------------------------------------------------
# Dataset Endpoints
# -------------------------------------------------------------

@router.post(
    "/datasets/seed",
    response_model=DatasetSeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Seed Synthetic Enterprise Dataset",
    description="Populates the database with a realistic synthetic transaction dataset for demonstration. Idempotent by default.",
)
def seed_dataset(
    dataset_name: str = Query("transaction_fraud_dataset", description="Name of the dataset"),
    force_reseed: bool = Query(False, description="Whether to clear and reseed the dataset"),
    db: Session = Depends(get_db),
):
    count = training_data_service.seed_synthetic_dataset(
        db=db, dataset_name=dataset_name, force_reseed=force_reseed
    )
    total = db.query(training_data_service.TrainingDataRecord).filter(
        training_data_service.TrainingDataRecord.dataset_name == dataset_name
    ).count()

    return DatasetSeedResponse(
        message="Dataset successfully seeded.",
        dataset_name=dataset_name,
        records_seeded=count,
        total_records=total,
    )


@router.get(
    "/datasets",
    response_model=List[DatasetInfoResponse],
    summary="List Datasets",
    description="Lists all available training datasets and their summary statistics.",
)
def list_datasets(db: Session = Depends(get_db)):
    return training_data_service.list_datasets(db)


@router.get(
    "/datasets/{dataset_name}/preview",
    response_model=DatasetPreviewResponse,
    summary="Preview Dataset Records",
    description="Returns a preview of the records in the specified dataset.",
)
def preview_dataset(
    dataset_name: str,
    limit: int = Query(50, ge=1, le=500, description="Max number of records to preview"),
    db: Session = Depends(get_db),
):
    preview = training_data_service.preview_dataset(db=db, dataset_name=dataset_name, limit=limit)
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_name}' not found or contains no records.",
        )
    return preview


# -------------------------------------------------------------
# Training Batch Endpoints
# -------------------------------------------------------------

@router.post(
    "/batches",
    response_model=TrainingBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Consent-Aware ML Training Batch",
    description=(
        "Validates consent for every record in the dataset via Module 1's Consent Gate. "
        "Constructs an approved dataset with only allowed records, trains a machine learning model, "
        "stores model artifacts and calculates real performance metrics, and logs complete data lineage."
    ),
)
def create_training_batch(
    request: TrainingBatchCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        batch = training_service.create_and_run_training_batch(db=db, request=request)
        return batch
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error executing training batch: {str(e)}",
        )


@router.get(
    "/batches",
    response_model=List[TrainingBatchResponse],
    summary="List Training Batches",
    description="Returns a list of all ML training batches.",
)
def list_batches(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return training_service.list_training_batches(db=db, limit=limit)


@router.get(
    "/batches/{batch_id}",
    response_model=TrainingBatchResponse,
    summary="Get Training Batch Details",
    description="Returns details and metrics for a specific ML training batch.",
)
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    batch = training_service.get_training_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training batch '{batch_id}' not found.",
        )
    return batch


@router.get(
    "/batches/{batch_id}/lineage",
    response_model=TrainingBatchLineageResponse,
    summary="View Record-Level Data Lineage",
    description="View record-level data lineage and consent decisions for a training batch.",
)
def get_batch_lineage(
    batch_id: str,
    db: Session = Depends(get_db),
):
    lineage = lineage_service.get_batch_lineage(db=db, batch_id=batch_id)
    if not lineage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training batch '{batch_id}' not found.",
        )
    return lineage


@router.get(
    "/batches/{batch_id}/dataset",
    summary="Download Approved Training Dataset",
    description="Returns the approved training CSV containing only records that passed the Consent Gate.",
)
def get_batch_dataset(
    batch_id: str,
    db: Session = Depends(get_db),
):
    batch = training_service.get_training_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training batch '{batch_id}' not found.",
        )
    if not batch.dataset_path or not os.path.exists(batch.dataset_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approved dataset file for batch '{batch_id}' not found on disk.",
        )
    return FileResponse(
        path=batch.dataset_path,
        media_type="text/csv",
        filename=f"batch_{batch_id}_approved.csv",
    )


@router.post(
    "/batches/{batch_id}/run",
    response_model=TrainingBatchResponse,
    summary="Re-run Training for Batch",
    description="Re-runs consent validation and ML training for an existing batch configuration.",
)
def rerun_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    batch = training_service.get_training_batch(db=db, batch_id=batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training batch '{batch_id}' not found.",
        )
    req = TrainingBatchCreateRequest(
        dataset_name=batch.dataset_name,
        data_scope=batch.data_scope,
        purpose=batch.purpose,
        model_type=batch.model_type,
    )
    new_batch = training_service.create_and_run_training_batch(db=db, request=req)
    return new_batch
