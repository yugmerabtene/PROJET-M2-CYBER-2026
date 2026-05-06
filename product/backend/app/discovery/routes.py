from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.deps import get_current_user
from app.discovery.service import (
    discover_single_host,
    discover_network_range,
    DiscoveryResult,
)

router = APIRouter()


class ScanRequest(BaseModel):
    ip_range: str = "192.168.1.0/24"
    ports: Optional[list[int]] = None


class ScanResponse(BaseModel):
    network: str
    hosts_found: int
    results: list[DiscoveryResult]


@router.post("/scan", response_model=ScanResponse)
def scan_network(req: ScanRequest, current_user: dict = Depends(get_current_user)):
    """Scan a network range for active hosts and open ports."""
    results = discover_network_range(req.ip_range, req.ports)
    alive = [r for r in results if r.is_alive]
    return ScanResponse(
        network=req.ip_range,
        hosts_found=len(alive),
        results=results,
    )


@router.get("/scan/{ip}", response_model=DiscoveryResult)
def scan_host(ip: str, current_user: dict = Depends(get_current_user)):
    """Scan a single host."""
    return discover_single_host(ip)
