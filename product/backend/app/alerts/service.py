from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.alerts.models import Alert, AuditLog


class AlertError(Exception):
    pass


def create_alert(db: Session, title: str, severity: str, source_ip: str | None, target_ip: str | None, rule_name: str | None, description: str | None = None, raw_payload: dict | None = None) -> Alert:
    now = datetime.now(timezone.utc)
    alert = Alert(
        title=title,
        description=description,
        severity=severity,
        status="new",
        source_ip=source_ip,
        target_ip=target_ip,
        rule_name=rule_name,
        first_seen=now,
        last_seen=now,
        created_at=now,
        updated_at=now,
        raw_payload=raw_payload,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def update_alert_status(db: Session, alert_id: int, new_status: str, actor: str | None = None) -> Alert | None:
    valid_statuses = {"new", "acknowledged", "investigating", "resolved", "false_positive", "closed"}
    if new_status not in valid_statuses:
        raise AlertError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        return None

    alert.status = new_status
    alert.updated_at = datetime.now(timezone.utc)

    log_audit(db, action="alert_status_change", actor=actor, target_type="alert", target_id=alert_id, details=f"Status changed to {new_status}")

    db.commit()
    db.refresh(alert)
    return alert


def get_alerts(db: Session, limit: int = 100, status_filter: str | None = None, severity_filter: str | None = None) -> list[Alert]:
    query = db.query(Alert).order_by(Alert.created_at.desc())
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    if severity_filter:
        query = query.filter(Alert.severity == severity_filter)
    return query.limit(limit).all()


def get_alert_by_id(db: Session, alert_id: int) -> Alert | None:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def get_alerts_by_source_ip(db: Session, source_ip: str) -> list[Alert]:
    return db.query(Alert).filter(Alert.source_ip == source_ip).order_by(Alert.created_at.desc()).all()


def evaluate_detection_rules(db: Session, events: list[dict]) -> list[Alert]:
    alerts = []
    ip_counts: dict[str, dict] = {}

    for event in events:
        src = event.get("source_ip", "")
        if not src:
            continue
        if src not in ip_counts:
            ip_counts[src] = {"count": 0, "ports": set(), "event_types": set()}
        ip_counts[src]["count"] += 1
        ip_counts[src]["event_types"].add(event.get("event_type", ""))
        if "connection" in event.get("raw_payload", {}):
            ip_counts[src]["ports"].add(event["raw_payload"]["connection"].get("remote_port", 0))

    for src_ip, data in ip_counts.items():
        if data["count"] >= 5 and len(data["ports"]) >= 3:
            alert = create_alert(
                db,
                title=f"Port scan détecté depuis {src_ip}",
                severity="high",
                source_ip=src_ip,
                target_ip=None,
                rule_name="port_scan_threshold",
                description=f"{data['count']} événements sur {len(data['ports'])} ports différents",
                raw_payload={"source_ip": src_ip, "port_count": len(data["ports"]), "event_count": data["count"]},
            )
            alerts.append(alert)

        if data["count"] >= 10 and "suspicious_connection" in data["event_types"]:
            alert = create_alert(
                db,
                title=f"Activité suspecte détectée depuis {src_ip}",
                severity="medium",
                source_ip=src_ip,
                target_ip=None,
                rule_name="suspicious_activity_threshold",
                description=f"{data['count']} événements suspects depuis {src_ip}",
                raw_payload={"source_ip": src_ip, "event_count": data["count"]},
            )
            alerts.append(alert)

    return alerts


def log_audit(db: Session, action: str, actor: str | None = None, target_type: str | None = None, target_id: int | None = None, details: str | None = None) -> AuditLog:
    log = AuditLog(
        action=action,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_logs(db: Session, limit: int = 100, action_filter: str | None = None) -> list[AuditLog]:
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    return query.limit(limit).all()
