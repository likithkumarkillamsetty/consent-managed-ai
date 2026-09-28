import random
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.training_data import TrainingDataRecord
from app.schemas.training_data import DatasetInfoResponse, DatasetPreviewResponse


def seed_synthetic_dataset(
    db: Session,
    dataset_name: str = "transaction_fraud_dataset",
    force_reseed: bool = False,
) -> int:
    """
    Seeds a realistic synthetic enterprise dataset for demonstration.
    Uses deterministic seeding so results are consistent and reproducible.
    Dataset includes users with various consent profiles:
    - user001, user002: (Approved consent)
    - user003: (Revoked consent)
    - user004: (No consent)
    - user005: (Wrong purpose consent)
    - user006: (Wrong scope consent)
    - user007: (Expired consent)
    - user008: (Pending/Denied consent)
    - user009, user010: (Additional users)
    """
    existing_count = db.query(TrainingDataRecord).filter(
        TrainingDataRecord.dataset_name == dataset_name
    ).count()

    if existing_count > 0 and not force_reseed:
        return existing_count

    if force_reseed:
        db.query(TrainingDataRecord).filter(
            TrainingDataRecord.dataset_name == dataset_name
        ).delete()
        db.commit()

    rng = random.Random(42)  # Deterministic seed

    users = [
        "user001", "user002", "user003", "user004", "user005",
        "user006", "user007", "user008", "user009", "user010",
    ]
    categories = ["ONLINE", "POS", "WIRE_TRANSFER", "ATM", "INVESTMENT"]

    records_to_insert = []
    record_counter = 1

    # Generate 8-10 records per user (80 records total)
    for u_idx, user_id in enumerate(users):
        num_records_for_user = 8
        base_balance = 10000.0 + (u_idx * 5000.0)

        for _ in range(num_records_for_user):
            rec_id = f"R{record_counter:03d}"
            category = rng.choice(categories)

            # Generate realistic features
            if category == "WIRE_TRANSFER" and rng.random() > 0.4:
                # Higher probability of fraud flag on suspicious large wire transfers
                amount = round(rng.uniform(12000.0, 48000.0), 2)
                tx_count = rng.randint(8, 30)
                avg_amount = round(amount / rng.randint(1, 4), 2)
                balance = round(rng.uniform(1000.0, 15000.0), 2)
                fraud_label = 1
            else:
                amount = round(rng.uniform(50.0, 4500.0), 2)
                tx_count = rng.randint(1, 15)
                avg_amount = round(amount / max(1, rng.randint(1, 3)), 2)
                balance = round(base_balance + rng.uniform(-2000.0, 10000.0), 2)
                # Small fraction of fraud
                fraud_label = 1 if rng.random() < 0.15 else 0

            record = TrainingDataRecord(
                record_id=rec_id,
                user_id=user_id,
                dataset_name=dataset_name,
                transaction_amount=amount,
                transaction_count=tx_count,
                average_transaction_amount=avg_amount,
                account_balance=max(100.0, balance),
                transaction_category=category,
                fraud_label=fraud_label,
            )
            records_to_insert.append(record)
            record_counter += 1

    db.bulk_save_objects(records_to_insert)
    db.commit()
    return len(records_to_insert)


def get_dataset_records(
    db: Session,
    dataset_name: str,
) -> List[TrainingDataRecord]:
    return (
        db.query(TrainingDataRecord)
        .filter(TrainingDataRecord.dataset_name == dataset_name)
        .order_by(TrainingDataRecord.record_id.asc())
        .all()
    )


def get_dataset_info(
    db: Session,
    dataset_name: str,
) -> Optional[DatasetInfoResponse]:
    total = (
        db.query(TrainingDataRecord)
        .filter(TrainingDataRecord.dataset_name == dataset_name)
        .count()
    )
    if total == 0:
        return None

    unique_users = (
        db.query(func.count(func.distinct(TrainingDataRecord.user_id)))
        .filter(TrainingDataRecord.dataset_name == dataset_name)
        .scalar()
    )
    fraud_count = (
        db.query(TrainingDataRecord)
        .filter(
            TrainingDataRecord.dataset_name == dataset_name,
            TrainingDataRecord.fraud_label == 1,
        )
        .count()
    )
    legit_count = total - fraud_count

    return DatasetInfoResponse(
        dataset_name=dataset_name,
        total_records=total,
        unique_users=unique_users or 0,
        fraud_count=fraud_count,
        legit_count=legit_count,
    )


def list_datasets(db: Session) -> List[DatasetInfoResponse]:
    names = (
        db.query(TrainingDataRecord.dataset_name)
        .distinct()
        .all()
    )
    result = []
    for (name,) in names:
        info = get_dataset_info(db, name)
        if info:
            result.append(info)
    return result


def preview_dataset(
    db: Session,
    dataset_name: str,
    limit: int = 50,
) -> Optional[DatasetPreviewResponse]:
    records = (
        db.query(TrainingDataRecord)
        .filter(TrainingDataRecord.dataset_name == dataset_name)
        .order_by(TrainingDataRecord.record_id.asc())
        .limit(limit)
        .all()
    )
    if not records:
        return None

    total = (
        db.query(TrainingDataRecord)
        .filter(TrainingDataRecord.dataset_name == dataset_name)
        .count()
    )

    return DatasetPreviewResponse(
        dataset_name=dataset_name,
        total_records=total,
        preview_count=len(records),
        records=records,
    )
