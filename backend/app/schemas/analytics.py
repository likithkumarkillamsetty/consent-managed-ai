from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_consents: int
    pending_consents: int
    approved_consents: int
    denied_consents: int
    revoked_consents: int
    expired_consents: int
    total_access_allowed: int
    total_access_blocked: int
