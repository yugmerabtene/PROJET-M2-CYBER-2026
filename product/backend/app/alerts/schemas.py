from datetime import datetime
from pydantic import BaseModel, Field, field_validator

VALID_STATUSES = {"new", "acknowledged", "investigating", "resolved", "closed"}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}


class AlertResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    status: str = Field(..., pattern="^(new|acknowledged|investigating|resolved|closed)$")
    source_ip: str | None = Field(None, max_length=45)
    target_ip: str | None = Field(None, max_length=45)
    rule_name: str | None = Field(None, max_length=128)
    event_count: int = Field(..., ge=0)
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}


class AlertUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(new|acknowledged|investigating|resolved|closed)$")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v


class AuditLogResponse(BaseModel):
    id: int
    action: str = Field(..., max_length=64)
    actor: str | None = Field(None, max_length=128)
    target_type: str | None = Field(None, max_length=32)
    target_id: int | None = None
    details: str | None = Field(None, max_length=2000)
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}
