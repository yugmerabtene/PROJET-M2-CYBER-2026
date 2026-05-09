import csv
import io
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.alerts.models import Alert, AuditLog
from app.assets.models import Asset
from app.correlation.models import CorrelationGroup
from app.telemetry.models import Agent, Heartbeat, TelemetryEvent


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    content_lines = [f"BT /F1 16 Tf 50 800 Td ({_pdf_escape(title)}) Tj ET"]
    y = 778
    for line in lines[:45]:
        content_lines.append(f"BT /F1 10 Tf 50 {y} Td ({_pdf_escape(line[:140])}) Tj ET")
        y -= 16
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n")
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")

    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(result))
        result.extend(obj)
    xref_pos = len(result)
    result.extend(f"xref\n0 {len(objects)+1}\n".encode("latin-1"))
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    result.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(result)


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


def export_correlations_csv(db: Session) -> str:
    groups = db.query(CorrelationGroup).order_by(CorrelationGroup.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "name",
        "group_type",
        "source_ip",
        "target_ip",
        "severity",
        "event_count",
        "correlation_score",
        "is_resolved",
        "created_at",
    ])
    for g in groups:
        writer.writerow([
            g.id,
            g.name,
            g.group_type,
            g.source_ip,
            g.target_ip,
            g.severity,
            g.event_count,
            g.correlation_score,
            g.is_resolved,
            g.created_at.isoformat(),
        ])
    return output.getvalue()


def export_pdf(db: Session, resource: str) -> bytes:
    title = f"DevinciWatch Export - {resource.title()}"
    lines: list[str] = []

    if resource == "alerts":
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
        lines.append(f"Total alerts: {len(alerts)}")
        for a in alerts[:40]:
            lines.append(f"#{a.id} [{a.severity}/{a.status}] {a.title} src={a.source_ip or '-'} dst={a.target_ip or '-'}")
    elif resource == "events":
        events = db.query(TelemetryEvent).order_by(TelemetryEvent.observed_at.desc()).limit(5000).all()
        lines.append(f"Total events: {len(events)}")
        for e in events[:40]:
            lines.append(f"#{e.id} [{e.severity}] {e.event_type} src={e.source_ip or '-'} dst={e.target_ip or '-'}")
    elif resource == "assets":
        assets = db.query(Asset).order_by(Asset.last_seen.desc()).all()
        lines.append(f"Total assets: {len(assets)}")
        for a in assets[:40]:
            lines.append(f"#{a.id} {a.ip_address} host={a.hostname or '-'} type={a.asset_type} active={a.is_active}")
    elif resource == "correlations":
        groups = db.query(CorrelationGroup).order_by(CorrelationGroup.created_at.desc()).all()
        lines.append(f"Total correlations: {len(groups)}")
        for g in groups[:40]:
            lines.append(f"#{g.id} {g.group_type} sev={g.severity} score={g.correlation_score} events={g.event_count}")
    else:
        lines.append(f"Unknown resource: {resource}")

    lines.append(f"Exported at: {datetime.now(timezone.utc).isoformat()}")
    return build_simple_pdf(title, lines)


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
    elif resource == "assets":
        assets = db.query(Asset).order_by(Asset.last_seen.desc()).all()
        return {
            "resource": "assets",
            "count": len(assets),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": [
                {
                    "id": a.id,
                    "ip_address": a.ip_address,
                    "hostname": a.hostname,
                    "asset_type": a.asset_type,
                    "os_guess": a.os_guess,
                    "is_active": a.is_active,
                    "first_seen": a.first_seen.isoformat(),
                    "last_seen": a.last_seen.isoformat(),
                    "metadata": a.metadata_json,
                }
                for a in assets
            ],
        }
    elif resource == "correlations":
        groups = db.query(CorrelationGroup).order_by(CorrelationGroup.created_at.desc()).all()
        return {
            "resource": "correlations",
            "count": len(groups),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": [
                {
                    "id": g.id,
                    "name": g.name,
                    "group_type": g.group_type,
                    "description": g.description,
                    "source_ip": g.source_ip,
                    "target_ip": g.target_ip,
                    "severity": g.severity,
                    "event_count": g.event_count,
                    "correlation_score": g.correlation_score,
                    "hostname": g.hostname,
                    "ip_cidr": g.ip_cidr,
                    "attack_chain_type": g.attack_chain_type,
                    "score_breakdown": g.score_breakdown,
                    "is_resolved": g.is_resolved,
                    "first_seen": g.first_seen.isoformat(),
                    "last_seen": g.last_seen.isoformat(),
                    "created_at": g.created_at.isoformat(),
                    "events": [
                        {
                            "id": e.id,
                            "telemetry_event_id": e.telemetry_event_id,
                            "source_ip": e.source_ip,
                            "target_ip": e.target_ip,
                            "event_type": e.event_type,
                            "severity": e.severity,
                            "message": e.message,
                            "observed_at": e.observed_at.isoformat(),
                            "sequence_order": e.sequence_order,
                            "ml_anomaly_score": e.ml_anomaly_score,
                        }
                        for e in g.events
                    ],
                }
                for g in groups
            ],
        }
    return {"error": f"Unknown resource: {resource}"}
