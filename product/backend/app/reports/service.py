import csv
import io
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.alerts.models import Alert, AuditLog
from app.assets.models import Asset
from app.telemetry.models import Agent, Heartbeat, TelemetryEvent


def get_dashboard_summary(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    last_heartbeat = None
    latest_hb = db.query(Heartbeat).order_by(Heartbeat.sent_at.desc()).first()
    if latest_hb:
        last_heartbeat = latest_hb.sent_at.isoformat()

    alerts_new = db.query(Alert).filter(Alert.status == "new").count()
    alerts_critical = db.query(Alert).filter(Alert.severity == "critical").count()
    alerts_high = db.query(Alert).filter(Alert.severity == "high").count()

    return {
        "total_events": db.query(TelemetryEvent).count(),
        "total_alerts": db.query(Alert).count(),
        "total_assets": db.query(Asset).count(),
        "total_agents": db.query(Agent).filter(Agent.is_active.is_(True)).count(),
        "total_correlations": 0,
        "active_alerts": alerts_new,
        "critical_alerts": alerts_critical,
        "high_alerts": alerts_high,
        "last_heartbeat": last_heartbeat,
        "generated_at": now.isoformat(),
    }


def get_alert_breakdown(db: Session) -> dict:
    return {
        "new": db.query(Alert).filter(Alert.status == "new").count(),
        "acknowledged": db.query(Alert).filter(Alert.status == "acknowledged").count(),
        "investigating": db.query(Alert).filter(Alert.status == "investigating").count(),
        "resolved": db.query(Alert).filter(Alert.status == "resolved").count(),
        "false_positive": db.query(Alert).filter(Alert.status == "false_positive").count(),
        "closed": db.query(Alert).filter(Alert.status == "closed").count(),
    }


def get_event_breakdown(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(hours=24)

    events_by_type = (
        db.query(TelemetryEvent.event_type, func.count(TelemetryEvent.id))
        .group_by(TelemetryEvent.event_type)
        .all()
    )
    events_by_severity = (
        db.query(TelemetryEvent.severity, func.count(TelemetryEvent.id))
        .group_by(TelemetryEvent.severity)
        .all()
    )
    events_24h = db.query(TelemetryEvent).filter(TelemetryEvent.observed_at >= yesterday).count()

    return {
        "by_type": {t: c for t, c in events_by_type},
        "by_severity": {s: c for s, c in events_by_severity},
        "last_24h": events_24h,
    }


def get_asset_breakdown(db: Session) -> dict:
    by_type = (
        db.query(Asset.asset_type, func.count(Asset.id))
        .group_by(Asset.asset_type)
        .all()
    )
    return {
        "total": db.query(Asset).count(),
        "active": db.query(Asset).filter(Asset.is_active.is_(True)).count(),
        "inactive": db.query(Asset).filter(Asset.is_active.is_(False)).count(),
        "by_type": {t: c for t, c in by_type},
    }


def export_alerts_csv(db: Session) -> str:
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "severity", "status", "source_ip", "target_ip", "rule_name", "created_at"])
    for a in alerts:
        writer.writerow([a.id, a.title, a.severity, a.status, a.source_ip, a.target_ip, a.rule_name, a.created_at.isoformat()])
    return output.getvalue()


def export_events_csv(db: Session) -> str:
    events = db.query(TelemetryEvent).order_by(TelemetryEvent.observed_at.desc()).limit(10000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "agent_id", "source_ip", "target_ip", "event_type", "severity", "message", "observed_at"])
    for e in events:
        writer.writerow([e.id, e.agent_id, e.source_ip, e.target_ip, e.event_type, e.severity, e.message, e.observed_at.isoformat()])
    return output.getvalue()


def export_assets_csv(db: Session) -> str:
    assets = db.query(Asset).order_by(Asset.last_seen.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "ip_address", "hostname", "asset_type", "os_guess", "is_active", "last_seen"])
    for a in assets:
        writer.writerow([a.id, a.ip_address, a.hostname, a.asset_type, a.os_guess, a.is_active, a.last_seen.isoformat()])
    return output.getvalue()


def export_json(db: Session, resource: str) -> dict:
    if resource == "alerts":
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
        return {
            "resource": "alerts",
            "count": len(alerts),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": [
                {
                    "id": a.id, "title": a.title, "severity": a.severity,
                    "status": a.status, "source_ip": a.source_ip,
                    "target_ip": a.target_ip, "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ],
        }
    elif resource == "events":
        events = db.query(TelemetryEvent).order_by(TelemetryEvent.observed_at.desc()).limit(5000).all()
        return {
            "resource": "events",
            "count": len(events),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": [
                {
                    "id": e.id, "agent_id": e.agent_id, "source_ip": e.source_ip,
                    "event_type": e.event_type, "severity": e.severity,
                    "message": e.message, "observed_at": e.observed_at.isoformat(),
                }
                for e in events
            ],
        }
    return {"error": f"Unknown resource: {resource}"}
