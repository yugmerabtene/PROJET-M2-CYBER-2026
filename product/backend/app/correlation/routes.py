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
    enrich_with_ml_scores,
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


@router.get("/ml-summary", summary="ML anomaly detection summary")
def ml_summary(
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    from app.telemetry.models import TelemetryEvent
    from app.ml.service import anomaly_detector

    db_events = (
        db.query(TelemetryEvent)
        .order_by(TelemetryEvent.observed_at.desc())
        .limit(limit)
        .all()
    )
    events = [
        {
            "source_ip": e.source_ip,
            "target_ip": e.target_ip,
            "event_type": e.event_type,
            "severity": e.severity,
            "message": e.message,
            "observed_at": e.observed_at.isoformat() if e.observed_at else "",
        }
        for e in db_events
    ]

    if not events:
        return {"total": 0, "anomalies": 0, "anomaly_rate": 0.0, "avg_score": 0.0, "model_ready": False}

    anomaly_detector.fit(events)
    summary = anomaly_detector.get_anomaly_summary(events)
    summary["model_ready"] = anomaly_detector.is_fitted

    return summary


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


@router.post("/{group_id}/ml-enrich", summary="Enrichir un groupe avec ML anomaly detection")
def ml_enrich_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = enrich_with_ml_scores(db, group_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result
