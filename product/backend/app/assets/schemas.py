from datetime import datetime

from pydantic import BaseModel


class AssetCreate(BaseModel):
    ip_address: str
    hostname: str | None = None
    mac_address: str | None = None
    asset_type: str = "host"
    os_guess: str | None = None


class AssetResponse(BaseModel):
    id: int
    ip_address: str
    hostname: str | None
    mac_address: str | None
    asset_type: str
    os_guess: str | None
    is_active: bool
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class PortFindingResponse(BaseModel):
    id: int
    port: int
    protocol: str
    service: str | None
    version: str | None
    state: str
    discovered_at: datetime

    model_config = {"from_attributes": True}


class ScanRequest(BaseModel):
    ip_range: str
    ports: list[int] | None = None
    protocol: str = "tcp"


class ScanResult(BaseModel):
    scanned_range: str
    hosts_found: int
    ports_found: int
    scanned_at: datetime
