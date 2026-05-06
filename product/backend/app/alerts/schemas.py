from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    title: str
    description: str | None
    severity: str
    status: str
    source_ip: str | None
    target_ip: str | None
    rule_name: str | None
    event_count: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdateStatus(BaseModel):
    status: str


class AuditLogResponse(BaseModel):
    id: int
    action: str
    actor: str | None
    target_type: str | None
    target_id: int | None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
