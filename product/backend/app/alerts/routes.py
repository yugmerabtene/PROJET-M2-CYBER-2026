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


@router.get("/{alert_id}", response_model=AlertResponse, summary="Détail d'une alerte")
def get_alert_route(
    alert_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    alert = get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    return alert


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
