from datetime import datetime

from pydantic import BaseModel


class CorrelationGroupResponse(BaseModel):
    id: int
    name: str
    group_type: str
    description: str | None
    source_ip: str | None
    target_ip: str | None
    severity: str
    event_count: int
    alert_ids: list | None
    first_seen: datetime
    last_seen: datetime
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CorrelatedEventResponse(BaseModel):
    id: int
    group_id: int
    telemetry_event_id: int | None
    source_ip: str | None
    target_ip: str | None
    event_type: str
    severity: str
    message: str | None
    observed_at: datetime

    model_config = {"from_attributes": True}


class CorrelationSummary(BaseModel):
    total_groups: int
    active_groups: int
    resolved_groups: int
    by_type: dict
    by_severity: dict
    top_source_ips: list[dict]
