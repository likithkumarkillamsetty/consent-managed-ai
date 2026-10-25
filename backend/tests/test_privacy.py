import os
from datetime import datetime, timedelta, timezone
import pytest
import pandas as pd
import io

from app.services import privacy_service


@pytest.fixture(autouse=True)
def explicit_test_env(monkeypatch):
    """Ensure tests in this module explicitly run in a test environment unless overridden."""
    monkeypatch.setenv("APP_ENV", "test")


def test_pseudonymization_deterministic_and_prefixed():
    """Verify pseudonymization generates deterministic, properly prefixed tokens."""
    token1 = privacy_service.pseudonymize_identifier("user001", prefix="anon_usr_")
    token2 = privacy_service.pseudonymize_identifier("user001", prefix="anon_usr_")
    token_diff = privacy_service.pseudonymize_identifier("user002", prefix="anon_usr_")

    assert token1.startswith("anon_usr_")
    assert token1 == token2, "Pseudonymization must be deterministic for identical input"
    assert token1 != token_diff, "Different users must produce distinct pseudonyms"
    assert len(token1) == len("anon_usr_") + 32


def test_pseudonymization_secret_rotation():
    """Verify changing HMAC secret key produces different pseudonyms (key rotation)."""
    secret_a = b"secret_key_alpha_123"
    secret_b = b"secret_key_beta_456"

    tok_a = privacy_service.pseudonymize_identifier("user001", custom_secret=secret_a)
    tok_b = privacy_service.pseudonymize_identifier("user001", custom_secret=secret_b)

    assert tok_a != tok_b, "Rotating secret key must produce different pseudonyms"


def test_transform_training_records_preserves_features():
    """Verify transform_training_records replaces IDs and preserves feature values."""
    raw_records = [
        {
            "record_id": "R001",
            "user_id": "user001",
            "transaction_amount": 1500.50,
            "transaction_count": 5,
            "average_transaction_amount": 300.10,
            "account_balance": 12000.0,
            "transaction_category": "ONLINE",
            "fraud_label": 0,
        },
        {
            "record_id": "R002",
            "user_id": "user001",
            "transaction_amount": 4200.00,
            "transaction_count": 8,
            "average_transaction_amount": 525.00,
            "account_balance": 11500.0,
            "transaction_category": "WIRE_TRANSFER",
            "fraud_label": 1,
        },
    ]

    transformed = privacy_service.transform_training_records(raw_records)

    assert len(transformed) == 2
    # Check ID replacement
    assert transformed[0]["user_id"].startswith("anon_usr_")
    assert transformed[0]["record_id"].startswith("anon_rec_")
    assert transformed[0]["user_id"] != "user001"
    assert transformed[0]["record_id"] != "R001"

    # User consistency within batch
    assert transformed[0]["user_id"] == transformed[1]["user_id"]
    # Distinct records
    assert transformed[0]["record_id"] != transformed[1]["record_id"]

    # Features unchanged
    assert transformed[0]["transaction_amount"] == 1500.50
    assert transformed[0]["account_balance"] == 12000.0
    assert transformed[0]["transaction_category"] == "ONLINE"
    assert transformed[0]["fraud_label"] == 0
    assert transformed[1]["fraud_label"] == 1

    # Raw list was not mutated
    assert raw_records[0]["user_id"] == "user001"


def test_batch_legacy_default_privacy_disabled(client):
    """Verify default privacy_enabled is False and raw IDs are preserved for backward compatibility."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c}/approve")

    # Call without privacy_enabled specified
    res = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
    })
    assert res.status_code == 201
    batch = res.json()
    assert batch["privacy_enabled"] is False
    assert batch["privacy_mechanism"] is None

    # CSV should contain raw user001
    csv_text = client.get(f"/training/batches/{batch['batch_id']}/dataset").text
    assert "user001" in csv_text
    assert "R001" in csv_text


def test_batch_with_privacy_enabled_masks_identifiers(client):
    """Verify privacy_enabled=True masks user_id and record_id in exported CSV."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c}/approve")

    # Call with privacy_enabled=True
    res = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
        "privacy_enabled": True,
    })
    assert res.status_code == 201
    batch = res.json()
    assert batch["privacy_enabled"] is True
    assert batch["privacy_mechanism"] == "PSEUDONYMIZATION_HMAC"
    assert batch["status"] == "COMPLETED"
    assert batch["accuracy"] is not None

    # Download CSV
    csv_text = client.get(f"/training/batches/{batch['batch_id']}/dataset").text
    # Raw IDs must NOT be present
    assert "user001" not in csv_text, "Raw user_id must not appear in privacy-enabled CSV"
    assert "R001" not in csv_text, "Raw record_id must not appear in privacy-enabled CSV"

    # Pseudonymized prefixes MUST be present
    assert "anon_usr_" in csv_text
    assert "anon_rec_" in csv_text

    # Verify CSV format and columns
    df = pd.read_csv(io.StringIO(csv_text))
    assert "user_id" in df.columns
    assert "record_id" in df.columns
    assert all(u.startswith("anon_usr_") for u in df["user_id"])
    assert all(r.startswith("anon_rec_") for r in df["record_id"])
    assert df["fraud_label"].isin([0, 1]).all()


def test_privacy_enabled_preserves_internal_lineage_traceability(client):
    """Verify internal data lineage retains authentic consent_id and user_id for audit compliance."""
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
        "privacy_enabled": True,
    })
    batch = res.json()
    batch_id = batch["batch_id"]

    # Query lineage
    lin_res = client.get(f"/training/batches/{batch_id}/lineage")
    assert lin_res.status_code == 200
    lineage = lin_res.json()

    # In internal database lineage, authentic user_id and consent_id MUST be maintained for compliance
    u1_records = [r for r in lineage["records"] if r["user_id"] == "user001"]
    assert len(u1_records) > 0
    assert all(r["consent_id"] == c for r in u1_records if r["access_result"] == "ALLOWED")


def test_privacy_enabled_audit_event_logged(client):
    """Verify PRIVACY_PROTECTION_APPLIED is recorded in audit logs when privacy is enabled."""
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
        "privacy_enabled": True,
    })
    batch_id = res.json()["batch_id"]

    audit_logs = client.get("/audit-logs?limit=50").json()
    privacy_events = [
        log for log in audit_logs
        if log["event_type"] == "PRIVACY_PROTECTION_APPLIED" and batch_id in log.get("details", "")
    ]
    assert len(privacy_events) >= 1
    assert "HMAC-SHA256" in privacy_events[0]["details"]


def test_privacy_enabled_revocation_enforced(client):
    """Verify consent revocation still blocks data even when privacy protection is enabled."""
    client.post("/training/datasets/seed")
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    c1 = client.post("/consents", json={
        "user_id": "user001", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    c2 = client.post("/consents", json={
        "user_id": "user002", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "TRANSACTION_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/approve")
    client.post(f"/consents/{c2}/approve")

    # Revoke user001
    client.post(f"/consents/{c1}/revoke")

    # Run privacy-enabled batch
    res = client.post("/training/batches", json={
        "dataset_name": "transaction_fraud_dataset",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
        "privacy_enabled": True,
    })
    batch = res.json()
    assert batch["status"] == "COMPLETED"
    assert batch["allowed_records"] == 8  # Only user002 allowed
    assert batch["blocked_records"] == 72


def test_privacy_secret_undeclared_environment_rejection(monkeypatch):
    """Verify that an undeclared environment refuses fallback and raises ValueError (fail-closed)."""
    monkeypatch.delenv("PRIVACY_HMAC_SECRET", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)

    with pytest.raises(ValueError, match="PRIVACY_HMAC_SECRET environment variable is required"):
        privacy_service.get_privacy_secret()

    # Whitespace in undeclared environment is also rejected
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", "   ")
    with pytest.raises(ValueError, match="PRIVACY_HMAC_SECRET environment variable is required"):
        privacy_service.get_privacy_secret()

    # Non-development environment (e.g. staging) is also rejected without a secret
    monkeypatch.delenv("PRIVACY_HMAC_SECRET", raising=False)
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ValueError, match="PRIVACY_HMAC_SECRET environment variable is required"):
        privacy_service.get_privacy_secret()


def test_privacy_secret_explicit_dev_fallback(monkeypatch):
    """Verify explicit development/test environments permit fallback to DEFAULT_DEV_SECRET."""
    monkeypatch.delenv("PRIVACY_HMAC_SECRET", raising=False)

    for env_var, env_val in [
        ("APP_ENV", "development"),
        ("ENVIRONMENT", "dev"),
        ("ENV", "test"),
        ("APP_ENV", "testing"),
    ]:
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("ENV", raising=False)
        monkeypatch.setenv(env_var, env_val)
        secret = privacy_service.get_privacy_secret()
        assert secret == privacy_service.DEFAULT_DEV_SECRET.encode("utf-8")


def test_privacy_secret_empty_and_whitespace_fallback(monkeypatch):
    """Verify empty or whitespace-only secret falls back safely in an explicit dev environment."""
    monkeypatch.setenv("APP_ENV", "development")

    # Empty string
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", "")
    assert privacy_service.get_privacy_secret() == privacy_service.DEFAULT_DEV_SECRET.encode("utf-8")

    # Whitespace only
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", "   \t\n   ")
    assert privacy_service.get_privacy_secret() == privacy_service.DEFAULT_DEV_SECRET.encode("utf-8")


def test_privacy_secret_production_enforcement(monkeypatch):
    """Verify PRIVACY_HMAC_SECRET is strictly required when running in production."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("PRIVACY_HMAC_SECRET", raising=False)

    with pytest.raises(ValueError, match="PRIVACY_HMAC_SECRET environment variable is required in production"):
        privacy_service.get_privacy_secret()

    # Whitespace in production is also rejected
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", "   ")
    with pytest.raises(ValueError, match="PRIVACY_HMAC_SECRET environment variable is required in production"):
        privacy_service.get_privacy_secret()

    # Valid secret in production is accepted
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", "valid_production_secret_key_777")
    assert privacy_service.get_privacy_secret() == b"valid_production_secret_key_777"


def test_privacy_secret_configured_secret_works_in_any_env(monkeypatch):
    """Verify configured, nonblank PRIVACY_HMAC_SECRET works in production, dev, or undeclared envs."""
    test_key = "custom_enterprise_secret_key_999"
    monkeypatch.setenv("PRIVACY_HMAC_SECRET", test_key)

    # In undeclared environment
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    assert privacy_service.get_privacy_secret() == test_key.encode("utf-8")

    # In production
    monkeypatch.setenv("APP_ENV", "production")
    assert privacy_service.get_privacy_secret() == test_key.encode("utf-8")

    # In development
    monkeypatch.setenv("APP_ENV", "development")
    assert privacy_service.get_privacy_secret() == test_key.encode("utf-8")


def test_pseudonymize_identifier_rejects_empty_custom_secret():
    """Verify pseudonymize_identifier explicitly refuses an empty HMAC key."""
    with pytest.raises(ValueError, match="HMAC secret key must not be empty"):
        privacy_service.pseudonymize_identifier("user001", custom_secret=b"")


def test_upgrade_db_schema_migrates_legacy_table(tmp_path):
    """
    Verify upgrade_db_schema successfully migrates a legacy SQLite table lacking
    privacy_enabled and privacy_mechanism, preserving existing row data.
    """
    from sqlalchemy import create_engine, text
    from app.database import upgrade_db_schema

    db_file = tmp_path / "legacy_migration_test.db"
    test_engine = create_engine(f"sqlite:///{db_file.as_posix()}")

    # 1. Create a legacy table without privacy columns
    with test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE training_batches (
                batch_id VARCHAR(50) PRIMARY KEY,
                dataset_name VARCHAR(100) NOT NULL,
                purpose VARCHAR(50) NOT NULL,
                data_scope VARCHAR(50) NOT NULL,
                status VARCHAR(30) NOT NULL,
                total_records INTEGER NOT NULL,
                allowed_records INTEGER NOT NULL,
                blocked_records INTEGER NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                created_at DATETIME NOT NULL
            );
        """))
        conn.execute(text("""
            INSERT INTO training_batches (
                batch_id, dataset_name, purpose, data_scope, status,
                total_records, allowed_records, blocked_records, model_type, created_at
            ) VALUES (
                'BATCH-LEGACY-001', 'transaction_fraud_dataset', 'AI_TRAINING',
                'TRANSACTION_DATA', 'COMPLETED', 80, 16, 64, 'logistic_regression', '2026-01-01 00:00:00'
            );
        """))
        conn.commit()

    # 2. Run upgrade_db_schema on the legacy test engine
    upgrade_db_schema(target_engine=test_engine)

    # 3. Verify columns were added and the existing row data was preserved
    with test_engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(training_batches);")).fetchall()
        col_names = {row[1] for row in cols}
        assert "privacy_enabled" in col_names
        assert "privacy_mechanism" in col_names

        row = conn.execute(text(
            "SELECT batch_id, dataset_name, status, privacy_enabled, privacy_mechanism "
            "FROM training_batches WHERE batch_id = 'BATCH-LEGACY-001';"
        )).fetchone()
        assert row is not None
        assert row[0] == "BATCH-LEGACY-001"
        assert row[1] == "transaction_fraud_dataset"
        assert row[2] == "COMPLETED"
        assert row[3] in (0, False)
        assert row[4] is None

    # 4. Run upgrade a second time to ensure idempotency
    upgrade_db_schema(target_engine=test_engine)
    with test_engine.connect() as conn:
        cols2 = conn.execute(text("PRAGMA table_info(training_batches);")).fetchall()
        assert len(cols2) == len(cols)


def test_upgrade_db_schema_surfaces_failures():
    """Verify that a genuine schema-upgrade failure is raised rather than silently swallowed."""
    import sqlite3
    from unittest.mock import MagicMock
    from app.database import upgrade_db_schema

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # First call: PRAGMA table_info returns table with batch_id but missing privacy_enabled
    # Second call: ALTER TABLE raises an OperationalError (e.g. database locked)
    mock_conn.execute.side_effect = [
        MagicMock(fetchall=MagicMock(return_value=[(0, "batch_id", "TEXT", 1, None, 1)])),
        sqlite3.OperationalError("database is locked"),
    ]

    with pytest.raises(sqlite3.OperationalError, match="database is locked"):
        upgrade_db_schema(target_engine=mock_engine)
