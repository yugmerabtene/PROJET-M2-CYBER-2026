from datetime import datetime

from pydantic import BaseModel, Field


class HeartbeatPayload(BaseModel):
    agent_id: str
    hostname: str
    ip_address: str | None = None
    status: str = "alive"
    mode: str | None = None
    interfaces: list[str] | None = None
    sent_at: str


class EventPayload(BaseModel):
    agent_id: str
    source_ip: str | None = ""
    target_ip: str | None = ""
    event_type: str
    severity: str = "info"
    message: str
    observed_at: str
    raw_payload: dict | None = None


class HeartbeatResponse(BaseModel):
    id: int
    agent_id: int
    status: str
    sent_at: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}
