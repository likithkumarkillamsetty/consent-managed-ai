import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np
import joblib
from sqlalchemy.orm import Session

from app.database import DATA_DIR
from app.models.consent import Consent
from app.models.training_data import TrainingDataRecord
from app.models.training_batch import TrainingBatch
from app.models.training_lineage import TrainingLineage
from app.schemas.training_batch import TrainingBatchCreateRequest
from app.services.consent_gate import check_access
from app.services.audit_service import create_audit_log

TRAINING_DIR = DATA_DIR / "training"
MODELS_DIR = DATA_DIR / "models"
TRAINING_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class ConsentAwareLogisticRegression:
    """
    Standard Logistic Regression Classifier with internal Feature Standardization,
    One-Hot Categorical Encoding, and Gradient Descent optimization.
    """
    def __init__(self, learning_rate: float = 0.05, epochs: int = 1500):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None
        self.categories: List[str] = []
        self.numeric_features = [
            "transaction_amount",
            "transaction_count",
            "average_transaction_amount",
            "account_balance",
        ]

    def _preprocess(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        num_data = df[self.numeric_features].to_numpy(dtype=float)

        if fit:
            self.feature_means = np.mean(num_data, axis=0)
            self.feature_stds = np.std(num_data, axis=0)
            self.feature_stds[self.feature_stds == 0] = 1.0
            self.categories = sorted(df["transaction_category"].unique().tolist())

        norm_num = (num_data - self.feature_means) / self.feature_stds

        cat_data = df["transaction_category"].tolist()
        cat_map = {c: i for i, c in enumerate(self.categories)}
        encoded_cats = np.zeros((len(cat_data), len(self.categories)), dtype=float)
        for i, c in enumerate(cat_data):
            if c in cat_map:
                encoded_cats[i, cat_map[c]] = 1.0

        return np.hstack([norm_num, encoded_cats])

    def fit(self, df_train: pd.DataFrame, y_train: np.ndarray):
        X = self._preprocess(df_train, fit=True)
        y = np.array(y_train, dtype=float)
        n_samples, n_features = X.shape

        self.weights = np.zeros(n_features, dtype=float)
        self.bias = 0.0

        for _ in range(self.epochs):
            linear = np.dot(X, self.weights) + self.bias
            # Sigmoid activation with clipping for numerical stability
            y_pred = 1.0 / (1.0 + np.exp(-np.clip(linear, -250, 250)))
            dw = (1.0 / n_samples) * np.dot(X.T, (y_pred - y))
            db = (1.0 / n_samples) * np.sum(y_pred - y)
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self._preprocess(df, fit=False)
        linear = np.dot(X, self.weights) + self.bias
        prob = 1.0 / (1.0 + np.exp(-np.clip(linear, -250, 250)))
        return (prob >= 0.5).astype(int)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    total = len(y_true)
    accuracy = float((tp + tn) / total) if total > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float((2 * precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
    }


def get_training_batch(db: Session, batch_id: str) -> Optional[TrainingBatch]:
    return db.query(TrainingBatch).filter(TrainingBatch.batch_id == batch_id).first()


def list_training_batches(db: Session, limit: int = 100) -> List[TrainingBatch]:
    return (
        db.query(TrainingBatch)
        .order_by(TrainingBatch.created_at.desc())
        .limit(limit)
        .all()
    )


def create_and_run_training_batch(
    db: Session,
    request: TrainingBatchCreateRequest,
) -> TrainingBatch:
    # 1. Fetch dataset records
    records = (
        db.query(TrainingDataRecord)
        .filter(TrainingDataRecord.dataset_name == request.dataset_name)
        .order_by(TrainingDataRecord.record_id.asc())
        .all()
    )

    if not records:
        raise ValueError(f"Dataset '{request.dataset_name}' contains no records or does not exist.")

    # 2. Create TrainingBatch entity
    batch = TrainingBatch(
        dataset_name=request.dataset_name,
        purpose=request.purpose,
        data_scope=request.data_scope,
        model_type=request.model_type,
        status="VALIDATING",
        total_records=len(records),
        allowed_records=0,
        blocked_records=0,
        privacy_enabled=request.privacy_enabled,
        privacy_mechanism="PSEUDONYMIZATION_HMAC" if request.privacy_enabled else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Audit batch creation
    create_audit_log(
        db=db,
        event_type="TRAINING_BATCH_CREATED",
        consent_id=None,
        user_id=None,
        purpose=request.purpose,
        data_scope=request.data_scope,
        result="SUCCESS",
        details=f"Training batch {batch.batch_id} created for dataset {request.dataset_name}",
    )

    # 3. Evaluate records via existing Module 1 Consent Gate
    allowed_records: List[TrainingDataRecord] = []
    blocked_records: List[TrainingDataRecord] = []
    lineage_entries: List[TrainingLineage] = []

    user_gate_cache = {}
    user_consent_cache = {}

    for record in records:
        user_id = record.user_id
        if user_id not in user_gate_cache:
            # Call the exact existing Module 1 Consent Gate logic
            gate_res = check_access(
                db=db,
                user_id=user_id,
                data_scope=request.data_scope,
                purpose=request.purpose,
            )
            user_gate_cache[user_id] = gate_res

            # Lookup matching consent for lineage attribution
            user_consents = (
                db.query(Consent)
                .filter(Consent.user_id == user_id)
                .order_by(Consent.created_at.desc())
                .all()
            )
            exact_match = next(
                (c for c in user_consents if c.data_scope == request.data_scope and c.purpose == request.purpose),
                None,
            )
            if exact_match:
                matched_c = exact_match
            else:
                scope_match = next((c for c in user_consents if c.data_scope == request.data_scope), None)
                matched_c = scope_match or next((c for c in user_consents if c.purpose == request.purpose), None) or (user_consents[0] if user_consents else None)

            user_consent_cache[user_id] = matched_c

        gate_result = user_gate_cache[user_id]
        matched_consent = user_consent_cache[user_id]

        consent_id = matched_consent.consent_id if matched_consent else None
        consent_status = matched_consent.status if matched_consent else "NO_CONSENT"

        if gate_result.allowed:
            access_result = "ALLOWED"
            reason = gate_result.reason
            allowed_records.append(record)
        else:
            access_result = "BLOCKED"
            reason = gate_result.reason
            blocked_records.append(record)
            if consent_status == "NO_CONSENT":
                consent_id = None

        lineage_entries.append(
            TrainingLineage(
                batch_id=batch.batch_id,
                record_id=record.record_id,
                user_id=record.user_id,
                consent_id=consent_id,
                purpose=request.purpose,
                data_scope=request.data_scope,
                consent_status=consent_status,
                access_result=access_result,
                reason=reason,
                timestamp=datetime.now(timezone.utc),
            )
        )

    # 4. Save lineage records to database
    db.bulk_save_objects(lineage_entries)
    db.commit()

    # Update batch counts
    batch.allowed_records = len(allowed_records)
    batch.blocked_records = len(blocked_records)

    # Check if we have any allowed records to train on
    if len(allowed_records) == 0:
        batch.status = "FAILED"
        batch.error_message = "No records passed the Consent Gate. Training cannot proceed."
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(batch)

        create_audit_log(
            db=db,
            event_type="TRAINING_FAILED",
            consent_id=None,
            user_id=None,
            purpose=request.purpose,
            data_scope=request.data_scope,
            result="FAILED",
            details=f"Training batch {batch.batch_id} failed: No valid consent records found.",
        )
        return batch

    # 5. Generate Approved Training Dataset CSV (ONLY ALLOWED RECORDS)
    csv_filename = f"batch_{batch.batch_id}.csv"
    csv_path = TRAINING_DIR / csv_filename

    allowed_dicts = [
        {
            "record_id": r.record_id,
            "user_id": r.user_id,
            "transaction_amount": r.transaction_amount,
            "transaction_count": r.transaction_count,
            "average_transaction_amount": r.average_transaction_amount,
            "account_balance": r.account_balance,
            "transaction_category": r.transaction_category,
            "fraud_label": r.fraud_label,
        }
        for r in allowed_records
    ]

    # Apply Privacy Protection if opt-in enabled
    if request.privacy_enabled:
        from app.services import privacy_service
        export_dicts = privacy_service.transform_training_records(allowed_dicts)
        create_audit_log(
            db=db,
            event_type="PRIVACY_PROTECTION_APPLIED",
            consent_id=None,
            user_id=None,
            purpose=request.purpose,
            data_scope=request.data_scope,
            result="SUCCESS",
            details=f"HMAC-SHA256 pseudonymization applied to {len(export_dicts)} records in batch {batch.batch_id}",
        )
    else:
        export_dicts = allowed_dicts

    df_allowed = pd.DataFrame(export_dicts)
    df_allowed.to_csv(csv_path, index=False)
    batch.dataset_path = str(csv_path)

    # 6. Execute ML Model Training
    batch.status = "TRAINING"
    batch.started_at = datetime.now(timezone.utc)
    db.commit()

    create_audit_log(
        db=db,
        event_type="TRAINING_STARTED",
        consent_id=None,
        user_id=None,
        purpose=request.purpose,
        data_scope=request.data_scope,
        result="SUCCESS",
        details=f"Training batch {batch.batch_id} started with {len(allowed_records)} allowed records",
    )

    try:
        model = ConsentAwareLogisticRegression()

        # Split 80% train / 20% test if sufficient records
        n_total = len(df_allowed)
        if n_total >= 10:
            train_size = int(0.8 * n_total)
            shuffled_df = df_allowed.sample(frac=1, random_state=42).reset_index(drop=True)
            df_train = shuffled_df.iloc[:train_size]
            df_test = shuffled_df.iloc[train_size:]

            model.fit(df_train, df_train["fraud_label"].to_numpy())
            y_pred = model.predict(df_test)
            metrics = calculate_metrics(df_test["fraud_label"].to_numpy(), y_pred)
        else:
            model.fit(df_allowed, df_allowed["fraud_label"].to_numpy())
            y_pred = model.predict(df_allowed)
            metrics = calculate_metrics(df_allowed["fraud_label"].to_numpy(), y_pred)

        # 7. Save Model Artifact
        model_filename = f"batch_{batch.batch_id}.joblib"
        model_path = MODELS_DIR / model_filename
        joblib.dump(model, model_path)

        batch.model_path = str(model_path)
        batch.accuracy = metrics["accuracy"]
        batch.precision = metrics["precision"]
        batch.recall = metrics["recall"]
        batch.f1_score = metrics["f1_score"]
        batch.status = "COMPLETED"
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(batch)

        create_audit_log(
            db=db,
            event_type="TRAINING_COMPLETED",
            consent_id=None,
            user_id=None,
            purpose=request.purpose,
            data_scope=request.data_scope,
            result="SUCCESS",
            details=f"Training batch {batch.batch_id} completed successfully with accuracy={metrics['accuracy']:.4f}",
        )
        return batch

    except Exception as e:
        batch.status = "FAILED"
        batch.error_message = str(e)
        batch.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(batch)

        create_audit_log(
            db=db,
            event_type="TRAINING_FAILED",
            consent_id=None,
            user_id=None,
            purpose=request.purpose,
            data_scope=request.data_scope,
            result="FAILED",
            details=f"Training batch {batch.batch_id} failed: {str(e)}",
        )
        return batch
