from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_events: int
    total_alerts: int
    total_assets: int
    total_agents: int
    total_correlations: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    last_heartbeat: str | None
    generated_at: str


class AlertBreakdown(BaseModel):
    new: int
    acknowledged: int
    investigating: int
    resolved: int
    false_positive: int
    closed: int


class EventBreakdown(BaseModel):
    by_type: dict
    by_severity: dict
    last_24h: int


class AssetBreakdown(BaseModel):
    total: int
    active: int
    inactive: int
    by_type: dict


class ExportResponse(BaseModel):
    format: str
    filename: str
    created_at: datetime
    record_count: int
    download_url: str | None = None
