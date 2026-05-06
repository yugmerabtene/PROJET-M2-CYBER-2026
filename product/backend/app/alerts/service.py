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
        src = event.get("source_ip") or ""
        if not src:
            continue
        if src not in ip_counts:
            ip_counts[src] = {"count": 0, "ports": set(), "event_types": set()}
        ip_counts[src]["count"] += 1
        ip_counts[src]["event_types"].add(event.get("event_type", ""))
        raw = event.get("raw_payload") or {}
        if "connection" in raw:
            ip_counts[src]["ports"].add(raw["connection"].get("remote_port", 0))

    # Get recent alerts for deduplication (last 5 minutes)
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    recent_alerts = db.query(Alert).filter(Alert.created_at >= cutoff).all()
    recent_alert_keys = {(a.source_ip, a.rule_name) for a in recent_alerts}

    def is_duplicate(src_ip: str, rule_name: str) -> bool:
        return (src_ip, rule_name) in recent_alert_keys

    # Rule 1: Immediate alert for critical/high severity events
    for event in events:
        evt_type = event.get("event_type", "")
        severity = event.get("severity", "")
        src = event.get("source_ip") or ""
        if not src:
            continue

        if evt_type in ("network_scan", "port_scan") and severity in ("high", "critical"):
            if is_duplicate(src, "network_scan_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Scan réseau détecté depuis {src}",
                severity="high",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="network_scan_detected",
                description=f"Type: {evt_type} | {event.get('message', '')}",
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "network_scan_detected"))

        if evt_type in ("brute_force", "brute_force_detected", "ssh_brute_force") and severity in ("high", "critical"):
            if is_duplicate(src, "brute_force_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Brute force détecté depuis {src}",
                severity="critical",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="brute_force_detected",
                description=f"Type: {evt_type} | {event.get('message', '')}",
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "brute_force_detected"))

        if evt_type == "suspicious_connection" and severity in ("high", "critical"):
            if is_duplicate(src, "suspicious_connection_critical"):
                continue
            alert = create_alert(
                db,
                title=f"Connexion suspecte depuis {src}",
                severity="high",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="suspicious_connection_critical",
                description=event.get("message", ""),
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "suspicious_connection_critical"))

        if evt_type in ("privilege_escalation", "privilege_escalation_attempt", "sudo_exploit") and severity in ("high", "critical"):
            if is_duplicate(src, "privilege_escalation_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Escalade de privilèges détectée depuis {src}",
                severity="critical",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="privilege_escalation_detected",
                description=event.get("message", ""),
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "privilege_escalation_detected"))

        if evt_type in ("malware_detected", "malware_execution", "trojan_detected", "ransomware_detected") and severity in ("high", "critical"):
            if is_duplicate(src, "malware_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Logiciel malveillant détecté depuis {src}",
                severity="critical",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="malware_detected",
                description=event.get("message", ""),
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "malware_detected"))

        if evt_type in ("data_exfiltration", "data_theft", "large_data_transfer") and severity in ("high", "critical"):
            if is_duplicate(src, "data_exfiltration_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Exfiltration de données détectée vers {event.get('target_ip', src)}",
                severity="critical",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="data_exfiltration_detected",
                description=event.get("message", ""),
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "data_exfiltration_detected"))

        if evt_type in ("traffic_burst", "connection_flood", "dos_attack") and severity in ("high", "critical"):
            if is_duplicate(src, "traffic_burst_detected"):
                continue
            alert = create_alert(
                db,
                title=f"Rafale de trafic détectée depuis {src}",
                severity="high",
                source_ip=src,
                target_ip=event.get("target_ip"),
                rule_name="traffic_burst_detected",
                description=event.get("message", ""),
                raw_payload=event,
            )
            alerts.append(alert)
            recent_alert_keys.add((src, "traffic_burst_detected"))

    # Rule 2: Threshold-based alerts (aggregated)
    for src_ip, data in ip_counts.items():
        if data["count"] >= 3 and len(data["ports"]) >= 2:
            if is_duplicate(src_ip, "port_scan_threshold"):
                continue
            alert = create_alert(
                db,
                title=f"Scan de ports détecté depuis {src_ip}",
                severity="high",
                source_ip=src_ip,
                target_ip=None,
                rule_name="port_scan_threshold",
                description=f"{data['count']} événements sur {len(data['ports'])} ports différents",
                raw_payload={"source_ip": src_ip, "port_count": len(data["ports"]), "event_count": data["count"]},
            )
            alerts.append(alert)

        if data["count"] >= 5 and "suspicious_connection" in data["event_types"]:
            if is_duplicate(src_ip, "suspicious_activity_threshold"):
                continue
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
            recent_alert_keys.add((src_ip, "suspicious_activity_threshold"))

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
