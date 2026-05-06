from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.assets.schemas import AssetCreate, AssetResponse, PortFindingResponse, ScanRequest, ScanResult
from app.assets.service import (
    AssetError,
    add_port_finding,
    create_or_update_asset,
    delete_asset,
    discover_network,
    get_all_ports,
    get_asset_by_id,
    get_asset_by_ip,
    get_asset_ports,
    get_assets,
)
from app.core.deps import get_current_user, get_db

router = APIRouter()


@router.get("", response_model=list[AssetResponse], summary="Liste des actifs")
def list_assets(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_assets(db, active_only)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, summary="Créer un actif")
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    try:
        return create_or_update_asset(db, data)
    except AssetError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/scan", response_model=ScanResult, summary="Scan réseau de découverte")
def scan_network(
    data: ScanRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    try:
        return discover_network(db, data.ip_range, data.ports, data.protocol)
    except AssetError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse, summary="Détail d'un actif")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    asset = get_asset_by_id(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actif introuvable")
    return asset


@router.get("/{asset_id}/ports", response_model=list[PortFindingResponse], summary="Ports d'un actif")
def get_asset_ports_route(
    asset_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    asset = get_asset_by_id(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actif introuvable")
    return get_asset_ports(db, asset_id)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer un actif")
def delete_asset_route(
    asset_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if not delete_asset(db, asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actif introuvable")
