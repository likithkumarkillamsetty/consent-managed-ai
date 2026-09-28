from datetime import datetime, timedelta, timezone
import pytest


def test_create_consent(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    response = client.post(
        "/consents",
        json={
            "user_id": "user001",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
            "expires_at": future_expiry,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user001"
    assert data["data_scope"] == "TRANSACTION_DATA"
    assert data["purpose"] == "AI_TRAINING"
    assert data["status"] == "PENDING"
    assert "consent_id" in data

    # Check audit log
    audit_resp = client.get(f"/consents/{data['consent_id']}/audit")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert any(log["event_type"] == "CONSENT_CREATED" for log in logs)


def test_approve_consent(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user002",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "CUSTOMER_PROFILE",
            "purpose": "FRAUD_DETECTION",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]

    approve_resp = client.post(f"/consents/{consent_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
    assert approve_resp.json()["approved_at"] is not None

    # Check audit log
    audit_resp = client.get(f"/consents/{consent_id}/audit")
    logs = audit_resp.json()
    assert any(log["event_type"] == "CONSENT_APPROVED" for log in logs)


def test_deny_consent(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user003",
            "data_provider": "Hospital",
            "data_consumer": "Research Lab",
            "data_scope": "HEALTH_DATA",
            "purpose": "ANALYTICS",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]

    deny_resp = client.post(f"/consents/{consent_id}/deny")
    assert deny_resp.status_code == 200
    assert deny_resp.json()["status"] == "DENIED"

    # Check audit log
    audit_resp = client.get(f"/consents/{consent_id}/audit")
    logs = audit_resp.json()
    assert any(log["event_type"] == "CONSENT_DENIED" for log in logs)


def test_valid_consent_allows_access(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user004",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]
    client.post(f"/consents/{consent_id}/approve")

    gate_resp = client.post(
        "/consent-gate/check",
        json={
            "user_id": "user004",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
        },
    )
    assert gate_resp.status_code == 200
    assert gate_resp.json()["allowed"] is True
    assert gate_resp.json()["reason"] == "Valid consent"

    # Verify ACCESS_ALLOWED in audit log
    audit_resp = client.get("/audit-logs?user_id=user004")
    logs = audit_resp.json()
    assert any(log["event_type"] == "ACCESS_ALLOWED" and log["result"] == "ALLOWED" for log in logs)


def test_wrong_purpose_blocks_access(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user005",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]
    client.post(f"/consents/{consent_id}/approve")

    gate_resp = client.post(
        "/consent-gate/check",
        json={
            "user_id": "user005",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "MARKETING",
        },
    )
    assert gate_resp.status_code == 200
    assert gate_resp.json()["allowed"] is False
    assert gate_resp.json()["reason"] == "PURPOSE_NOT_ALLOWED"

    # Verify ACCESS_BLOCKED in audit log
    audit_resp = client.get("/audit-logs?user_id=user005")
    logs = audit_resp.json()
    assert any(log["event_type"] == "ACCESS_BLOCKED" and log["result"] == "BLOCKED" for log in logs)


def test_wrong_scope_blocks_access(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user006",
            "data_provider": "Telecom",
            "data_consumer": "AI Platform",
            "data_scope": "LOCATION_DATA",
            "purpose": "ANALYTICS",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]
    client.post(f"/consents/{consent_id}/approve")

    gate_resp = client.post(
        "/consent-gate/check",
        json={
            "user_id": "user006",
            "data_scope": "HEALTH_DATA",
            "purpose": "ANALYTICS",
        },
    )
    assert gate_resp.status_code == 200
    assert gate_resp.json()["allowed"] is False
    assert gate_resp.json()["reason"] == "DATA_SCOPE_NOT_ALLOWED"


def test_expired_consent_blocks_access(client):
    # Create with an expiration 1 second in future, then simulate passage of time
    future_expiry = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user007",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]
    client.post(f"/consents/{consent_id}/approve")

    import time
    time.sleep(1.2)

    gate_resp = client.post(
        "/consent-gate/check",
        json={
            "user_id": "user007",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
        },
    )
    assert gate_resp.status_code == 200
    assert gate_resp.json()["allowed"] is False
    assert gate_resp.json()["reason"] == "CONSENT_EXPIRED"


def test_revoked_consent_blocks_access(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    create_resp = client.post(
        "/consents",
        json={
            "user_id": "user008",
            "data_provider": "Bank",
            "data_consumer": "AI Platform",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
            "expires_at": future_expiry,
        },
    )
    consent_id = create_resp.json()["consent_id"]
    client.post(f"/consents/{consent_id}/approve")

    # Revoke
    revoke_resp = client.post(f"/consents/{consent_id}/revoke")
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "REVOKED"
    assert revoke_resp.json()["revoked_at"] is not None

    # Check gate
    gate_resp = client.post(
        "/consent-gate/check",
        json={
            "user_id": "user008",
            "data_scope": "TRANSACTION_DATA",
            "purpose": "AI_TRAINING",
        },
    )
    assert gate_resp.status_code == 200
    assert gate_resp.json()["allowed"] is False
    assert gate_resp.json()["reason"] == "CONSENT_REVOKED"


def test_invalid_state_transitions_are_rejected(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    # 1. DENIED -> APPROVED must fail
    c1 = client.post("/consents", json={
        "user_id": "user009", "data_provider": "P", "data_consumer": "C",
        "data_scope": "CUSTOMER_PROFILE", "purpose": "MARKETING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c1}/deny")
    res = client.post(f"/consents/{c1}/approve")
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]

    # 2. REVOKED -> APPROVED must fail
    c2 = client.post("/consents", json={
        "user_id": "user010", "data_provider": "P", "data_consumer": "C",
        "data_scope": "CUSTOMER_PROFILE", "purpose": "MARKETING", "expires_at": future_expiry
    }).json()["consent_id"]
    client.post(f"/consents/{c2}/approve")
    client.post(f"/consents/{c2}/revoke")
    res = client.post(f"/consents/{c2}/approve")
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]

    # 3. DENIED -> REVOKED must fail
    res = client.post(f"/consents/{c1}/revoke")
    assert res.status_code == 400
    assert "Invalid transition" in res.json()["detail"]


def test_required_demo_flow(client):
    """
    Exact Demo Flow specified in Requirement 23:
    Step 1: Create consent (user001, TRANSACTION_DATA, AI_TRAINING) -> PENDING, audit CONSENT_CREATED
    Step 2: Approve consent -> APPROVED, audit CONSENT_APPROVED
    Step 3: Check access (user001, TRANSACTION_DATA, AI_TRAINING) -> ACCESS ALLOWED, Valid consent, audit ACCESS_ALLOWED
    Step 4: Check same scope wrong purpose (user001, TRANSACTION_DATA, MARKETING) -> ACCESS BLOCKED, PURPOSE_NOT_ALLOWED, audit ACCESS_BLOCKED
    Step 5: Revoke the approved consent -> REVOKED, audit CONSENT_REVOKED
    Step 6: Check access again (user001, TRANSACTION_DATA, AI_TRAINING) -> ACCESS BLOCKED, CONSENT_REVOKED, audit ACCESS_BLOCKED
    """
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    # Step 1: Create consent
    res1 = client.post("/consents", json={
        "user_id": "user001",
        "data_provider": "Bank",
        "data_consumer": "AI Platform",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING",
        "expires_at": future_expiry
    })
    assert res1.status_code == 201
    c_data = res1.json()
    consent_id = c_data["consent_id"]
    assert c_data["status"] == "PENDING"

    # Verify Step 1 Audit
    audits = client.get(f"/consents/{consent_id}/audit").json()
    assert audits[0]["event_type"] == "CONSENT_CREATED"

    # Step 2: Approve consent
    res2 = client.post(f"/consents/{consent_id}/approve")
    assert res2.status_code == 200
    assert res2.json()["status"] == "APPROVED"

    # Verify Step 2 Audit
    audits = client.get(f"/consents/{consent_id}/audit").json()
    assert any(a["event_type"] == "CONSENT_APPROVED" for a in audits)

    # Step 3: Check access (Valid)
    res3 = client.post("/consent-gate/check", json={
        "user_id": "user001",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING"
    })
    assert res3.status_code == 200
    assert res3.json()["allowed"] is True
    assert res3.json()["reason"] == "Valid consent"

    # Verify Step 3 Audit
    user_audits = client.get("/audit-logs?user_id=user001").json()
    assert any(a["event_type"] == "ACCESS_ALLOWED" and a["result"] == "ALLOWED" for a in user_audits)

    # Step 4: Check same scope but wrong purpose (MARKETING)
    res4 = client.post("/consent-gate/check", json={
        "user_id": "user001",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "MARKETING"
    })
    assert res4.status_code == 200
    assert res4.json()["allowed"] is False
    assert res4.json()["reason"] == "PURPOSE_NOT_ALLOWED"

    # Verify Step 4 Audit
    user_audits = client.get("/audit-logs?user_id=user001").json()
    assert any(a["event_type"] == "ACCESS_BLOCKED" and a["details"] == "PURPOSE_NOT_ALLOWED" for a in user_audits)

    # Step 5: Revoke the approved consent
    res5 = client.post(f"/consents/{consent_id}/revoke")
    assert res5.status_code == 200
    assert res5.json()["status"] == "REVOKED"

    # Verify Step 5 Audit
    audits = client.get(f"/consents/{consent_id}/audit").json()
    assert any(a["event_type"] == "CONSENT_REVOKED" for a in audits)

    # Step 6: Check access again
    res6 = client.post("/consent-gate/check", json={
        "user_id": "user001",
        "data_scope": "TRANSACTION_DATA",
        "purpose": "AI_TRAINING"
    })
    assert res6.status_code == 200
    assert res6.json()["allowed"] is False
    assert res6.json()["reason"] == "CONSENT_REVOKED"

    # Verify Step 6 Audit
    user_audits = client.get("/audit-logs?user_id=user001").json()
    assert any(a["event_type"] == "ACCESS_BLOCKED" and a["details"] == "CONSENT_REVOKED" for a in user_audits)


def test_analytics_summary(client):
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    # Create 1 consent, approve it, do 1 allowed access check, 1 blocked check
    c = client.post("/consents", json={
        "user_id": "user_stat", "data_provider": "Bank", "data_consumer": "AI Corp",
        "data_scope": "HEALTH_DATA", "purpose": "AI_TRAINING", "expires_at": future_expiry
    }).json()
    client.post(f"/consents/{c['consent_id']}/approve")
    client.post("/consent-gate/check", json={"user_id": "user_stat", "data_scope": "HEALTH_DATA", "purpose": "AI_TRAINING"})
    client.post("/consent-gate/check", json={"user_id": "user_stat", "data_scope": "HEALTH_DATA", "purpose": "MARKETING"})

    summary_resp = client.get("/analytics/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_consents"] >= 1
    assert summary["approved_consents"] >= 1
    assert summary["total_access_allowed"] >= 1
    assert summary["total_access_blocked"] >= 1
