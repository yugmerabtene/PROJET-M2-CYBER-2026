from datetime import datetime
from pydantic import BaseModel, Field, field_validator

VALID_EVENT_SEVERITIES = {"critical", "high", "medium", "low", "info", "warning"}


class HeartbeatPayload(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    status: str = Field("alive", max_length=16)
    mode: str | None = Field(None, max_length=32)
    interfaces: list[str] | None = None
    sent_at: str

    model_config = {"extra": "forbid"}


class EventPayload(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    source_ip: str | None = Field("", max_length=45)
    target_ip: str | None = Field("", max_length=45)
    event_type: str = Field(..., min_length=1, max_length=64)
    severity: str = Field("info", max_length=16)
    message: str = Field(..., min_length=1, max_length=2000)
    observed_at: str
    raw_payload: dict | None = None

    model_config = {"extra": "forbid"}

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in VALID_EVENT_SEVERITIES:
            raise ValueError(f"Severity must be one of: {', '.join(sorted(VALID_EVENT_SEVERITIES))}")
        return v


class HeartbeatResponse(BaseModel):
    id: int
    agent_id: int
    status: str
    sent_at: datetime
    received_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}


class TelemetryEventResponse(BaseModel):
    id: int
    agent_id: int
    source_ip: str | None
    target_ip: str | None
    event_type: str
    severity: str
    message: str
    observed_at: datetime
    received_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}


class AgentResponse(BaseModel):
    id: int
    sensor_id: str
    hostname: str
    ip_address: str | None
    mode: str
    interfaces: list | None
    is_active: bool
    last_heartbeat_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "forbid"}
