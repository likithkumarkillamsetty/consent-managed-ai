# Consent-Managed Data Pipelines for Enterprise AI (DEPA-Inspired)
## Module 1 & Module 2: Consent Governance & Consent-Aware ML Training Pipeline

> **IMPORTANT DISCLAIMER:**
> "This module implements a DEPA/Account-Aggregator-inspired consent management model for the project. It is not an official Account Aggregator implementation."

---

## 1. Overview & Statement of Purpose
"Module 2 implements a consent-aware ML training pipeline that uses the existing Module 1 Consent Gate to ensure that only data with valid, purpose-bound consent enters a training batch. Each training batch maintains record-level lineage linking training data to the consent that authorized its use."

This project ensures:
- **No valid consent = No training data**: Data access is strictly bound to granular scopes and explicit purposes.
- **Dynamic Revocation Enforcement**: Revoking consent prevents that user's records from entering any subsequent training batch while preserving historical training lineage.
- **End-to-End Lineage Tracking**: Every training batch maintains queryable, record-level lineage recording the exact consent ID, user ID, purpose, and decision reason.
- **Audit Logging**: All consent operations and ML pipeline events are immutably logged in the unified audit trail.

---

## 2. Architecture & Data Flow

```
 DATA SOURCE (Synthetic Enterprise Dataset)
    ↓
 DATASET RECORDS (Records belonging to users user001..user010)
    ↓
 TRAINING REQUEST (POST /training/batches with data_scope, purpose, model_type)
    ↓
 CONSENT GATE (Module 1 Policy Enforcement Engine)
    ↓
 ┌──────────────────────────────────────────────┐
 │ Valid, approved, unexpired, matching consent?│
 └──────────────────────────────────────────────┘
       ↓                                    ↓
      YES                                  NO
       ↓                                    ↓
 ALLOW RECORD                         BLOCK RECORD
 (Record retained)                    (Record filtered out)
       ↓                                    ↓
       └──────────────────┬─────────────────┘
                          ↓
              RECORD-LEVEL DATA LINEAGE
            (batch_id, record_id, user_id,
             consent_id, access_result, reason)
                          ↓
              APPROVED TRAINING DATASET
            (data/training/batch_<id>.csv)
                          ↓
                 ML MODEL TRAINING
            (Logistic Regression Classifier)
                          ↓
              TRAINED MODEL ARTIFACT
            (data/models/batch_<id>.joblib)
                          ↓
            REAL MODEL PERFORMANCE METRICS
            (Accuracy, Precision, Recall, F1)
```

---

## 3. Database Schema

- **Engine:** SQLite + SQLAlchemy ORM
- **Database File:** `backend/data/consent.db`

### Tables:

#### 1. `consents` (Module 1)
| Column | Type | Description |
|---|---|---|
| `consent_id` | String(36) PK | Unique consent identifier (UUID) |
| `user_id` | String(100) | Data Principal ID |
| `data_provider` | String(100) | Data Custodian / Provider |
| `data_consumer` | String(100) | Data Consumer / Model Platform |
| `data_scope` | String(50) | `TRANSACTION_DATA`, `CUSTOMER_PROFILE`, `HEALTH_DATA`, `LOCATION_DATA` |
| `purpose` | String(50) | `AI_TRAINING`, `FRAUD_DETECTION`, `MARKETING`, `ANALYTICS` |
| `status` | String(20) | `PENDING`, `APPROVED`, `DENIED`, `REVOKED`, `EXPIRED` |
| `created_at` | DateTime | Timestamp of creation (UTC) |
| `expires_at` | DateTime | Expiration timestamp (UTC) |
| `approved_at` | DateTime | Timestamp when approved (UTC, nullable) |
| `revoked_at` | DateTime | Timestamp when revoked (UTC, nullable) |

#### 2. `training_data_records` (Module 2)
| Column | Type | Description |
|---|---|---|
| `record_id` | String(50) PK | Record identifier (e.g. `R001`..`R080`) |
| `user_id` | String(100) | User identifier |
| `dataset_name` | String(100) | Dataset identifier |
| `transaction_amount` | Float | Transaction amount |
| `transaction_count` | Integer | Transaction count |
| `average_transaction_amount` | Float | Average amount per transaction |
| `account_balance` | Float | Account balance |
| `transaction_category` | String(50) | `ONLINE`, `POS`, `WIRE_TRANSFER`, `ATM`, `INVESTMENT` |
| `fraud_label` | Integer | Target variable (`0` = Legit, `1` = Fraud) |
| `created_at` | DateTime | Ingestion timestamp |

#### 3. `training_batches` (Module 2)
| Column | Type | Description |
|---|---|---|
| `batch_id` | String(50) PK | Unique batch ID (e.g. `BATCH-XXXXXXXX`) |
| `dataset_name` | String(100) | Target dataset |
| `purpose` | String(50) | Training purpose (e.g. `AI_TRAINING`) |
| `data_scope` | String(50) | Training data scope (e.g. `TRANSACTION_DATA`) |
| `status` | String(30) | `CREATED`, `VALIDATING`, `READY`, `TRAINING`, `COMPLETED`, `FAILED` |
| `total_records` | Integer | Total records evaluated |
| `allowed_records` | Integer | Total records passed through Consent Gate |
| `blocked_records` | Integer | Total records blocked by Consent Gate |
| `model_type` | String(50) | Machine learning algorithm (`logistic_regression`) |
| `model_path` | String(255) | Path to saved model artifact (`.joblib`) |
| `dataset_path` | String(255) | Path to approved training dataset (`.csv`) |
| `accuracy` | Float | Calculated accuracy on test split |
| `precision` | Float | Calculated precision |
| `recall` | Float | Calculated recall |
| `f1_score` | Float | Calculated F1 score |
| `created_at` | DateTime | Batch creation timestamp |
| `started_at` | DateTime | Training start timestamp |
| `completed_at` | DateTime | Training completion timestamp |
| `error_message` | Text | Failure reason if status is `FAILED` |

#### 4. `training_lineage` (Module 2)
| Column | Type | Description |
|---|---|---|
| `lineage_id` | String(36) PK | Unique lineage UUID |
| `batch_id` | String(50) | Associated Training Batch |
| `record_id` | String(50) | Source dataset record ID |
| `user_id` | String(100) | Data owner ID |
| `consent_id` | String(36) | Authorizing consent ID (null if no consent) |
| `purpose` | String(50) | Evaluated purpose |
| `data_scope` | String(50) | Evaluated data scope |
| `consent_status` | String(30) | State of consent during evaluation |
| `access_result` | String(20) | `ALLOWED` or `BLOCKED` |
| `reason` | String(100) | Decision reason (e.g. `Valid consent`, `CONSENT_REVOKED`, `NO_CONSENT`) |
| `timestamp` | DateTime | Evaluation timestamp (UTC) |

#### 5. `audit_logs` (Module 1 & 2)
Unified audit trail logging all lifecycle actions:
`CONSENT_CREATED`, `CONSENT_APPROVED`, `CONSENT_DENIED`, `CONSENT_REVOKED`, `CONSENT_EXPIRED`, `ACCESS_ALLOWED`, `ACCESS_BLOCKED`, `TRAINING_BATCH_CREATED`, `TRAINING_STARTED`, `TRAINING_COMPLETED`, `TRAINING_FAILED`.

---

## 4. API Endpoints

### Module 1: Consent Management & Gate
- `POST /consents` – Create a consent request (`PENDING`)
- `GET /consents` – List consents (filter by `user_id`, `status`)
- `GET /consents/{id}` – Get consent details
- `POST /consents/{id}/approve` – Approve consent (`APPROVED`)
- `POST /consents/{id}/deny` – Deny consent (`DENIED`)
- `POST /consents/{id}/revoke` – Revoke consent (`REVOKED`)
- `GET /consents/{id}/audit` – Get consent-specific audit trail
- `POST /consent-gate/check` – Evaluate access in real-time
- `GET /audit-logs` – Get system-wide audit history
- `GET /analytics/summary` – Live summary statistics

### Module 2: ML Training Pipeline & Lineage
- `POST /training/datasets/seed` – Seed synthetic enterprise dataset (idempotent)
- `GET /training/datasets` – List available datasets and summary statistics
- `GET /training/datasets/{name}/preview` – Preview dataset records
- `POST /training/batches` – Create and execute a consent-aware ML training batch
- `GET /training/batches` – List all training batches
- `GET /training/batches/{id}` – Get training batch details and metrics
- `GET /training/batches/{id}/lineage` – View record-level data lineage
- `GET /training/batches/{id}/dataset` – Download approved training dataset CSV
- `POST /training/batches/{id}/run` – Re-run batch training

---

## 5. How to Run Locally

### Start Backend:
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger Documentation: `http://localhost:8000/docs`

### Seed Synthetic Dataset:
```powershell
curl -X POST "http://localhost:8000/training/datasets/seed"
```

### Create and Run a Training Batch:
```powershell
curl -X POST "http://localhost:8000/training/batches" `
     -H "Content-Type: application/json" `
     -d '{"dataset_name": "transaction_fraud_dataset", "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "model_type": "logistic_regression"}'
```

### View Data Lineage:
```powershell
curl -X GET "http://localhost:8000/training/batches/<BATCH_ID>/lineage"
```

### Run Automated Test Suite:
```powershell
pytest -v
```

---

## 6. End-to-End Demonstration Scenario

| Step | Action | Endpoint / Details | Result |
|---|---|---|---|
| **1** | Seed Dataset | `POST /training/datasets/seed` | 80 synthetic records created across `user001`..`user010` |
| **2** | Create Consents | `user001` & `user002` (APPROVED, `AI_TRAINING`), `user003` (REVOKED), `user004` (NO CONSENT) | Consents registered & approved/revoked |
| **3** | Execute Batch 1 | `POST /training/batches` | `user001` & `user002` → ALLOWED (16 records); `user003` & `user004` → BLOCKED (64 records). Model trains with real metrics. |
| **4** | Inspect Lineage | `GET /training/batches/{batch1_id}/lineage` | Full audit attribution mapping each record to consent and user |
| **5** | Revoke `user001` | `POST /consents/{c1_id}/revoke` | `user001` status becomes `REVOKED` |
| **6** | Execute Batch 2 | `POST /training/batches` | `user001` is now BLOCKED; only `user002` is ALLOWED (8 records). Model trains strictly on remaining allowed data. |
| **7** | Verify Immutability | `GET /training/batches/{batch1_id}/lineage` | Historical Batch 1 lineage remains unchanged and verifiable. |
