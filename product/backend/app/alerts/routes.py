from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.alerts.schemas import AlertResponse, AlertUpdateStatus, AuditLogResponse
from app.alerts.service import AlertError, create_alert, evaluate_detection_rules, get_alert_by_id, get_alerts, get_audit_logs, log_audit, update_alert_status
from app.core.deps import get_current_user, get_db

router = APIRouter()


@router.get("", response_model=list[AlertResponse], summary="Liste des alertes")
def list_alerts(
    limit: int = Query(100, le=1000),
    status_filter: str | None = None,
    severity_filter: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_alerts(db, limit, status_filter, severity_filter)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, summary="Créer une alerte manuellement")
def create_alert_route(
    title: str,
    severity: str = "medium",
    source_ip: str | None = None,
    target_ip: str | None = None,
    rule_name: str | None = None,
    description: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    alert = create_alert(db, title, severity, source_ip, target_ip, rule_name, description)
    log_audit(db, action="alert_created", actor=user.username, target_type="alert", target_id=alert.id)

    # Broadcast real-time update
    from app.core.realtime import send_dashboard_update
    send_dashboard_update()

    return alert


@router.patch("/{alert_id}/status", response_model=AlertResponse, summary="Mettre à jour le statut d'une alerte")
def update_alert_status_route(
    alert_id: int,
    data: AlertUpdateStatus,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        alert = update_alert_status(db, alert_id, data.status, actor=user.username)
    except AlertError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    return alert


@router.get("/{alert_id}", summary="Detail enrichi d'une alerte")
def get_alert_route(
    alert_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    alert = get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")

    # Enrich with linked events and correlation info
    from app.telemetry.models import TelemetryEvent
    from app.correlation.models import CorrelatedEvent, CorrelationGroup

    # Find events matching alert's source/target IP and time window
    related_events = (
        db.query(TelemetryEvent)
        .filter(
            (TelemetryEvent.source_ip == alert.source_ip) | (TelemetryEvent.target_ip == alert.target_ip)
        )
        .order_by(TelemetryEvent.observed_at.desc())
        .limit(50)
        .all()
    )

    # Find correlation groups that contain events related to this alert
    event_ids = [e.id for e in related_events]
    if event_ids:
        correlated = (
            db.query(CorrelatedEvent)
            .filter(CorrelatedEvent.telemetry_event_id.in_(event_ids))
            .all()
        )
        correlation_group_ids = list(set(c.group_id for c in correlated))
        correlations = (
            db.query(CorrelationGroup)
            .filter(CorrelationGroup.id.in_(correlation_group_ids))
            .all()
        )
    else:
        correlations = []

    return {
        "id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status,
        "source_ip": alert.source_ip,
        "target_ip": alert.target_ip,
        "rule_name": alert.rule_name,
        "description": alert.description,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
        "raw_payload": alert.raw_payload,
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "actor": log.actor,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in alert.audit_logs
        ],
        "related_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "source_ip": e.source_ip,
                "target_ip": e.target_ip,
                "severity": e.severity,
                "message": e.message,
                "observed_at": e.observed_at,
                "raw_payload": e.raw_payload,
            }
            for e in related_events
        ],
        "related_correlations": [
            {
                "id": g.id,
                "group_type": g.group_type,
                "source_ip": g.source_ip,
                "severity": g.severity,
                "event_count": g.event_count,
                "is_resolved": g.is_resolved,
                "ml_anomaly_score": g.ml_anomaly_score,
            }
            for g in correlations
        ],
        "event_count": len(related_events),
        "correlation_count": len(correlations),
    }


@router.post("/detect", response_model=list[AlertResponse], summary="Évaluer les règles de détection sur des événements")
def run_detection(
    events: list[dict],
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    alerts = evaluate_detection_rules(db, events)
    return alerts


@router.get("/audit", response_model=list[AuditLogResponse], summary="Journal d'audit")
def list_audit_logs(
    limit: int = Query(100, le=1000),
    action_filter: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_audit_logs(db, limit, action_filter)
