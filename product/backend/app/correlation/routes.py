from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.correlation.schemas import CorrelationGroupResponse, CorrelatedEventResponse, CorrelationSummary
from app.correlation.service import (
    correlate_by_ip,
    correlate_by_time_window,
    get_correlation_groups,
    get_group_by_id,
    get_group_events,
    get_correlation_summary,
    resolve_group,
)
from app.core.deps import get_current_user, get_db

router = APIRouter()


@router.get("", response_model=list[CorrelationGroupResponse], summary="Liste des groupes de correlation")
def list_correlations(
    active_only: bool = True,
    group_type: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_correlation_groups(db, active_only, group_type, severity)


@router.get("/summary", response_model=CorrelationSummary, summary="Synthese de correlation")
def correlation_summary(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_correlation_summary(db)


@router.post("/run-ip", response_model=list[CorrelationGroupResponse], summary="Lancer la correlation par IP")
def run_ip_correlation(
    events: list[dict],
    min_events: int = Query(3, ge=1),
    window_minutes: int = Query(60, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    groups = correlate_by_ip(db, events, min_events, window_minutes)
    return groups


@router.post("/run-temporal", response_model=list[CorrelationGroupResponse], summary="Lancer la correlation temporelle")
def run_temporal_correlation(
    events: list[dict],
    window_minutes: int = Query(10, ge=1),
    min_events: int = Query(5, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    groups = correlate_by_time_window(db, events, window_minutes, min_events)
    return groups


@router.get("/{group_id}", response_model=CorrelationGroupResponse, summary="Detail d'un groupe de correlation")
def get_correlation_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return group


@router.get("/{group_id}/events", response_model=list[CorrelatedEventResponse], summary="Evenements d'un groupe")
def get_correlation_events(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return get_group_events(db, group_id)


@router.patch("/{group_id}/resolve", response_model=CorrelationGroupResponse, summary="Resoudre un groupe de correlation")
def resolve_correlation_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = resolve_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return group
