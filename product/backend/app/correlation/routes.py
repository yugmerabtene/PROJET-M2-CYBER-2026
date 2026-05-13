from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.correlation.models import CorrelationGroup
from app.correlation.schemas import CorrelationGroupResponse, CorrelatedEventResponse, CorrelationSummary
from app.correlation.service import (
    correlate_by_ip,
    correlate_by_time_window,
    correlate_by_session,
    get_correlation_groups,
    get_group_by_id,
    get_group_events,
    get_group_events_with_sequence,
    get_correlation_summary,
    resolve_group,
    calculate_composite_score,
    correlate_by_hostname,
    detect_attack_chains,
    create_manual_group,
    run_full_correlation_from_db,
)
from app.core.deps import get_current_user, get_db

router = APIRouter()


@router.get("", response_model=list[CorrelationGroupResponse], summary="Liste des groupes de correlation")
def list_correlations(
    active_only: bool = True,
    group_type: str | None = None,
    severity: str | None = None,
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(CorrelationGroup).order_by(CorrelationGroup.created_at.desc())
    if active_only:
        query = query.filter(CorrelationGroup.is_resolved.is_(False))
    if group_type:
        query = query.filter(CorrelationGroup.group_type == group_type)
    if severity:
        query = query.filter(CorrelationGroup.severity == severity)
    if min_score > 0:
        query = query.filter(CorrelationGroup.correlation_score >= min_score)
    return query.all()


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


@router.post("/run-session", summary="Lancer la correlation par session")
def run_session_correlation(
    events: list[dict],
    min_events: int = Query(3, ge=1),
    window_minutes: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return correlate_by_session(db, events, min_events=min_events, window_minutes=window_minutes)


@router.post("/run-all-db", summary="Exécuter la corrélation complète depuis la base")
def run_all_correlation_from_db(
    lookback_minutes: int = Query(120, ge=5, le=1440),
    limit: int = Query(2000, ge=10, le=10000),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return run_full_correlation_from_db(db, lookback_minutes=lookback_minutes, limit=limit)


@router.get("/{group_id}", summary="Detail d'un groupe de correlation")
def get_correlation_group(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    
    # Include score breakdown in response
    result = {
        "id": group.id,
        "name": group.name,
        "group_type": group.group_type,
        "description": group.description,
        "source_ip": group.source_ip,
        "target_ip": group.target_ip,
        "severity": group.severity,
        "event_count": group.event_count,
        "is_resolved": group.is_resolved,
        "first_seen": group.first_seen,
        "last_seen": group.last_seen,
        "created_at": group.created_at,
        "correlation_score": group.correlation_score,
        "score_breakdown": group.score_breakdown,
        "hostname": group.hostname,
        "ip_cidr": group.ip_cidr,
        "attack_chain_type": group.attack_chain_type,
    }
    return result


@router.get("/{group_id}/events", summary="Evenements d'un groupe")
def get_correlation_events(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return get_group_events(db, group_id)


@router.get("/{group_id}/timeline", summary="Timeline detaillee")
def get_correlation_timeline(
    group_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Retourne la timeline séquencée d'un groupe."""
    group = get_group_by_id(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    events = get_group_events_with_sequence(db, group_id)
    return {
        "group_id": group_id,
        "timeline": events,
        "score_breakdown": group.score_breakdown,
        "composite_score": group.correlation_score,
    }


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


@router.post("/run-hostname", summary="Correlation par hostname")
def run_hostname_correlation(
    events: list[dict],
    min_events: int = Query(3, ge=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Regroupe les evenements par hostname cible."""
    return correlate_by_hostname(db, events, min_events)


@router.post("/run-attack-chain", summary="Detecter chaines d'attaque")
def run_attack_chain_detection(
    events: list[dict] | None = None,
    use_database: bool = True,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Detecte sequences logiques (scan → bruteforce → ...)"""
    if events is None and use_database:
        from app.telemetry.models import TelemetryEvent
        db_events = (
            db.query(TelemetryEvent)
            .order_by(TelemetryEvent.observed_at.desc())
            .limit(1000)
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
    return detect_attack_chains(db, events)


@router.post("/manual-group", summary="Creation manuelle par analyste")
def manual_correlation_group(
    event_ids: list[int],
    group_name: str,
    group_type: str = "manual",
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Permet a l'analyste de regrouper manuellement des evenements."""
    return create_manual_group(db, event_ids, group_name, group_type, _user.username)
