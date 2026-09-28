import os
import time
from datetime import datetime, timedelta, timezone
import pytest


def test_01_seed_dataset(client):
    """TEST 1: Seed synthetic dataset."""
    res = client.post("/training/datasets/seed")
    assert res.status_code == 201
    data = res.json()
    assert data["records_seeded"] > 0
    assert data["total_records"] >= 50
    assert data["dataset_name"] == "transaction_fraud_dataset"

    # Seed again without force_reseed (idempotent)
    res2 = client.post("/training/datasets/seed")
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["total_records"] == data["total_records"]


def test_02_dataset_preview(client):
    """TEST 2: Dataset preview works."""
    client.post("/training/datasets/seed")

    prev_res = client.get("/training/datasets/transaction_fraud_dataset/preview?limit=10")
    assert prev_res.status_code == 200
    preview = prev_res.json()
    assert preview["preview_count"] == 10
    assert len(preview["records"]) == 10
    assert preview["records"][0]["record_id"] == "R001"


def test_03_create_training_batch(client):
    """TEST 3: Create training batch."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c}/approve")

    res = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    })
    assert res.status_code == 201
    assert "batch_id" in res.json()


def test_04_approved_consent_allows_data(client):
    """TEST 4: Approved consent allows data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u1_records = [r for r in lineage["records"] if r["user_id"] == "user001"]
    assert len(u1_records) > 0
    assert all(r["access_result"] == "ALLOWED" for r in u1_records)


def test_05_no_consent_blocks_data(client):
    """TEST 5: No consent blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    # Approve user001 so batch doesn't fail
    c = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c}/approve")

    # user004 has no consent
    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u4_records = [r for r in lineage["records"] if r["user_id"] == "user004"]
    assert len(u4_records) > 0
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "NO_CONSENT" for r in u4_records)


def test_06_pending_consent_blocks_data(client):
    """TEST 6: Pending consent blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    # Approve user001
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user002 has pending consent
    client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    })

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u2_records = [r for r in lineage["records"] if r["user_id"] == "user002"]
    assert len(u2_records) > 0
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "CONSENT_NOT_APPROVED" for r in u2_records)


def test_07_denied_consent_blocks_data(client):
    """TEST 7: Denied consent blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user002 denied
    c2 = client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c2}/deny")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u2_records = [r for r in lineage["records"] if r["user_id"] == "user002"]
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "CONSENT_NOT_APPROVED" for r in u2_records)


def test_08_revoked_consent_blocks_data(client):
    """TEST 8: Revoked consent blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user003 revoked
    c3 = client.post("/consents", json={
        "user_id": "user003", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c3}/approve")
    client.post(f"/consents/{c3}/revoke")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u3_records = [r for r in lineage["records"] if r["user_id"] == "user003"]
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "CONSENT_REVOKED" for r in u3_records)


def test_09_expired_consent_blocks_data(client):
    """TEST 9: Expired consent blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    short_expiry = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()

    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user007 expired
    c7 = client.post("/consents", json={
        "user_id": "user007", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": short_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c7}/approve")
    time.sleep(1.2)

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u7_records = [r for r in lineage["records"] if r["user_id"] == "user007"]
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "CONSENT_EXPIRED" for r in u7_records)


def test_10_wrong_purpose_blocks_data(client):
    """TEST 10: Wrong purpose blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user005 has MARKETING purpose
    c5 = client.post("/consents", json={
        "user_id": "user005", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "MARKETING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c5}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u5_records = [r for r in lineage["records"] if r["user_id"] == "user005"]
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "PURPOSE_NOT_ALLOWED" for r in u5_records)


def test_11_wrong_data_scope_blocks_data(client):
    """TEST 11: Wrong data scope blocks data."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    # user006 has HEALTH_DATA scope
    c6 = client.post("/consents", json={
        "user_id": "user006", "data_provider": "Hospital", "data_consumer": "AI Corp",
        "data_scope": "HEALTH_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c6}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    u6_records = [r for r in lineage["records"] if r["user_id"] == "user006"]
    assert all(r["access_result"] == "BLOCKED" and r["reason"] == "DATA_SCOPE_NOT_ALLOWED" for r in u6_records)


def test_12_13_only_allowed_records_in_training_dataset(client):
    """TEST 12 & 13: Only allowed records enter training CSV, blocked records never enter."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    dataset_res = client.get(f"/training/batches/{batch['batch_id']}/dataset")
    assert dataset_res.status_code == 200
    csv_text = dataset_res.text
    assert "user001" in csv_text
    assert "user002" not in csv_text
    assert "user003" not in csv_text


def test_14_15_16_lineage_for_allowed_and_blocked(client):
    """TEST 14, 15, 16: Lineage created for allowed/blocked, allowed contains consent_id."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    lineage = client.get(f"/training/batches/{batch['batch_id']}/lineage").json()
    records = lineage["records"]

    allowed = [r for r in records if r["access_result"] == "ALLOWED"]
    blocked = [r for r in records if r["access_result"] == "BLOCKED"]

    assert len(allowed) == 8
    assert len(blocked) == 72
    assert all(r["consent_id"] == c1 for r in allowed)
    assert all(r["reason"] != "" for r in blocked)


def test_17_18_19_20_ml_training_model_metrics(client):
    """TEST 17, 18, 19, 20: ML training runs, model file created, metrics calculated, batch COMPLETED."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    c2 = client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c2}/approve")

    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    assert batch["status"] == "COMPLETED"
    assert batch["model_path"] is not None
    assert os.path.exists(batch["model_path"])
    assert batch["accuracy"] is not None
    assert 0.0 <= batch["accuracy"] <= 1.0
    assert batch["completed_at"] is not None


def test_21_training_failure(client):
    """TEST 21: Training failure becomes FAILED."""
    client.post("/training/datasets/seed")
    # No consents granted
    batch = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    assert batch["status"] == "FAILED"
    assert batch["allowed_records"] == 0
    assert "No records passed" in batch["error_message"]


def test_22_23_revocation_lifecycle(client):
    """TEST 22 & 23: Revocation affects Batch 2, preserves Batch 1 lineage."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    c2 = client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c2}/approve")

    # Batch 1
    b1 = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()
    assert b1["allowed_records"] == 16

    # Revoke user001
    client.post(f"/consents/{c1}/revoke")

    # Batch 2
    b2 = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()
    assert b2["allowed_records"] == 8

    # Check Batch 2 lineage for user001
    b2_lin = client.get(f"/training/batches/{b2['batch_id']}/lineage").json()
    assert all(r["access_result"] == "BLOCKED" for r in b2_lin["records"] if r["user_id"] == "user001")

    # Check Batch 1 lineage remains ALLOWED
    b1_lin = client.get(f"/training/batches/{b1['batch_id']}/lineage").json()
    assert all(r["access_result"] == "ALLOWED" for r in b1_lin["records"] if r["user_id"] == "user001")


def test_24_audit_logs(client):
    """TEST 24: Audit logs contain training events."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    })

    logs = client.get("/audit-logs?limit=200").json()
    events = {l["event_type"] for l in logs}
    assert "TRAINING_BATCH_CREATED" in events
    assert "TRAINING_STARTED" in events
    assert "TRAINING_COMPLETED" in events


def test_25_lineage_api(client):
    """TEST 25: API returns correct lineage for a batch."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")

    b = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    }).json()

    res = client.get(f"/training/batches/{b['batch_id']}/lineage")
    assert res.status_code == 200
    data = res.json()
    assert data["batch_id"] == b["batch_id"]
    assert data["total_records"] == 80
    assert data["allowed_records"] == 8
    assert data["blocked_records"] == 72
    assert len(data["records"]) == 80


def test_28_end_to_end_scenario(client):
    """
    TEST 28: Complete End-to-End Demonstration Scenario.
    """
    client.post("/training/datasets/seed", params={"force_reseed": True})
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

    # User A (user001)
    cA = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank A", "data_consumer": "AI Core",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{cA}/approve")

    # User B (user002)
    cB = client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank B", "data_consumer": "AI Core",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{cB}/approve")

    # User C (user003)
    cC = client.post("/consents", json={
        "user_id": "user003", "data_provider": "Bank C", "data_consumer": "AI Core",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{cC}/approve")
    client.post(f"/consents/{cC}/revoke")

    # User D (user004) has NO consent created

    # RUN BATCH 1
    res_b1 = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
        "model_type": "logistic_regression",
    })
    assert res_b1.status_code == 201
    b1_data = res_b1.json()
    b1_id = b1_data["batch_id"]

    assert b1_data["status"] == "COMPLETED"
    assert b1_data["allowed_records"] == 16  # User A (8) + User B (8)
    assert b1_data["blocked_records"] == 64
    assert b1_data["accuracy"] is not None

    # Lineage Batch 1
    lin1 = client.get(f"/training/batches/{b1_id}/lineage").json()
    lin1_map = {r["user_id"]: r["access_result"] for r in lin1["records"]}
    assert lin1_map["user001"] == "ALLOWED"
    assert lin1_map["user002"] == "ALLOWED"
    assert lin1_map["user003"] == "BLOCKED"
    assert lin1_map["user004"] == "BLOCKED"

    # CSV for Batch 1
    csv1 = client.get(f"/training/batches/{b1_id}/dataset").text
    assert "user001" in csv1
    assert "user002" in csv1
    assert "user003" not in csv1
    assert "user004" not in csv1

    # REVOKE USER A
    client.post(f"/consents/{cA}/revoke")

    # RUN BATCH 2
    res_b2 = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
        "model_type": "logistic_regression",
    })
    assert res_b2.status_code == 201
    b2_data = res_b2.json()
    b2_id = b2_data["batch_id"]

    assert b2_data["status"] == "COMPLETED"
    assert b2_data["allowed_records"] == 8  # Only User B
    assert b2_data["blocked_records"] == 72

    # Lineage Batch 2
    lin2 = client.get(f"/training/batches/{b2_id}/lineage").json()
    lin2_map = {r["user_id"]: r["access_result"] for r in lin2["records"]}
    assert lin2_map["user001"] == "BLOCKED"  # Now BLOCKED due to revocation
    assert lin2_map["user002"] == "ALLOWED"
    assert lin2_map["user003"] == "BLOCKED"
    assert lin2_map["user004"] == "BLOCKED"

    # CSV for Batch 2
    csv2 = client.get(f"/training/batches/{b2_id}/dataset").text
    assert "user001" not in csv2
    assert "user002" in csv2
    assert "user003" not in csv2
    assert "user004" not in csv2

    # Verify Batch 1 is unchanged
    lin1_after = client.get(f"/training/batches/{b1_id}/lineage").json()
    lin1_after_map = {r["user_id"]: r["access_result"] for r in lin1_after["records"]}
    assert lin1_after_map["user001"] == "ALLOWED"
    assert lin1_after_map["user002"] == "ALLOWED"
