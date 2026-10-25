"""
Privacy Protection Service (Module 2 Extension: Phase 2)
Consent-Managed Data Pipelines for Enterprise AI (DEPA-Inspired)

PRIVACY PROTECTION SPECIFICATION & ARCHITECTURAL BOUNDS:
1. Pseudonymization (Active Phase 2 Mechanism):
   - Replaces direct identifiers (`user_id`) and pseudo-identifiers (`record_id`)
     with deterministic, cryptographically secure HMAC-SHA256 pseudonyms.
   - Secret key is read from the environment (`PRIVACY_HMAC_SECRET`).
   - The secret key and original-to-pseudonym mapping are never persisted to disk,
     never logged in audit trails, and never exported in CSV files or API responses.
   - Regulatory Note (GDPR Recital 26): Pseudonymization protects direct identifiers
     against external inspection and re-identification in exported training datasets,
     but pseudonymous data remains personal data if additional linkage data exists.

2. Differential Privacy Status (PENDING - Phase 3 Roadmap):
   - In accordance with the project roadmap (Infosys Review 2, Slides 4 & 7),
     Differential Privacy (calibrated Laplace/Gaussian perturbation of numeric features
     with formal (epsilon, delta) guarantees) is scheduled for Phase 3.
   - No uncalibrated noise or informal perturbation is falsely labeled as "differentially private".
"""

import os
import hmac
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("privacy_service")

# Fallback development key if environment variable is not explicitly provided.
# In production, PRIVACY_HMAC_SECRET MUST be securely configured in the environment.
DEFAULT_DEV_SECRET = "depa_privacy_dev_hmac_secret_key_v1"


def is_production() -> bool:
    """Checks whether the application is running in a production environment."""
    env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or os.environ.get("ENV") or "").strip().lower()
    return env in ("production", "prod")


def is_development_or_test() -> bool:
    """Checks whether the environment explicitly indicates development or testing."""
    env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or os.environ.get("ENV") or "").strip().lower()
    return env in ("development", "dev", "test", "testing")


def get_privacy_secret() -> bytes:
    """
    Retrieves the HMAC secret key from the environment configuration.

    Security & Validation:
    - Strips leading and trailing whitespace from the environment value.
    - Never returns an empty HMAC key.
    - If missing or empty in production, raises a ValueError rather than
      silently using a known development secret.
    - If missing or empty and the environment is undeclared or not explicitly
      development/testing, raises a ValueError (fail-closed).
    - Only when the environment explicitly indicates development or testing
      does it log a warning and fall back to DEFAULT_DEV_SECRET.
    """
    raw_secret = os.environ.get("PRIVACY_HMAC_SECRET")
    secret_str = (raw_secret or "").strip()

    if not secret_str:
        if is_production():
            raise ValueError(
                "PRIVACY_HMAC_SECRET environment variable is required in production when privacy protection is enabled."
            )
        if not is_development_or_test():
            raise ValueError(
                "PRIVACY_HMAC_SECRET environment variable is required when privacy protection is enabled. "
                "For local development or testing, set APP_ENV=development or configure PRIVACY_HMAC_SECRET."
            )
        logger.warning(
            "PRIVACY_HMAC_SECRET is unset or empty; using default development fallback secret in development/test mode. "
            "Configure PRIVACY_HMAC_SECRET in production environments."
        )
        return DEFAULT_DEV_SECRET.encode("utf-8")

    return secret_str.encode("utf-8")


def pseudonymize_identifier(identifier: str, prefix: str = "anon_", custom_secret: Optional[bytes] = None) -> str:
    """
    Generates a deterministic HMAC-SHA256 pseudonym for a given identifier string.

    Args:
        identifier: The raw string identifier (e.g. 'user001' or 'R001')
        prefix: Namespace prefix (e.g. 'anon_usr_' or 'anon_rec_')
        custom_secret: Optional override secret for testing key rotation

    Returns:
        Pseudonymized token string (e.g. 'anon_usr_9a4f21d8b0c3f5e1a2b4c6d8e0f2a4b6')
    """
    secret = custom_secret if custom_secret is not None else get_privacy_secret()
    if not secret or len(secret) == 0:
        raise ValueError("HMAC secret key must not be empty.")

    h = hmac.new(secret, identifier.encode("utf-8"), hashlib.sha256)
    token = h.hexdigest()[:32]
    return f"{prefix}{token}"


def transform_training_records(
    records: List[Dict[str, Any]],
    custom_secret: Optional[bytes] = None,
) -> List[Dict[str, Any]]:
    """
    Transforms authorized training records by pseudonymizing direct identifiers
    (user_id and record_id) while preserving feature values and types for ML model training.

    Args:
        records: List of dictionaries representing approved training data records.
        custom_secret: Optional override secret for testing.

    Returns:
        New list of dictionaries with pseudonymized user_id and record_id.
        Original list is not mutated.
    """
    transformed = []
    for rec in records:
        new_rec = dict(rec)
        if "user_id" in new_rec and new_rec["user_id"]:
            new_rec["user_id"] = pseudonymize_identifier(
                str(new_rec["user_id"]),
                prefix="anon_usr_",
                custom_secret=custom_secret,
            )
        if "record_id" in new_rec and new_rec["record_id"]:
            new_rec["record_id"] = pseudonymize_identifier(
                str(new_rec["record_id"]),
                prefix="anon_rec_",
                custom_secret=custom_secret,
            )
        transformed.append(new_rec)
    return transformed
