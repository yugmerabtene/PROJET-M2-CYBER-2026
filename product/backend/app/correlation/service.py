from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy.orm import Session

from app.correlation.models import CorrelationGroup, CorrelatedEvent
from app.alerts.models import Alert
from app.telemetry.models import TelemetryEvent


class CorrelationError(Exception):
    pass


def correlate_by_ip(db: Session, events: list[dict], min_events: int = 3, window_minutes: int = 60) -> list[CorrelationGroup]:
    ip_events: dict[str, list[dict]] = defaultdict(list)
    for evt in events:
        src = evt.get("source_ip", "")
        if src:
            ip_events[src].append(evt)

    groups = []
    for source_ip, evts in ip_events.items():
        if len(evts) < min_events:
            continue

        sorted_evts = sorted(evts, key=lambda e: e.get("observed_at", ""))
        first_seen = sorted_evts[0].get("observed_at", "")
        last_seen = sorted_evts[-1].get("observed_at", "")
        event_types = set(e.get("event_type", "") for e in evts)
        severities = [e.get("severity", "info") for e in evts]
        max_severity = _highest_severity(severities)

        group = CorrelationGroup(
            name=f"Activite suspecte depuis {source_ip}",
            group_type="ip_source",
            description=f"{len(evts)} evenements de {len(event_types)} types differents",
            source_ip=source_ip,
            target_ip=None,
            severity=max_severity,
            event_count=len(evts),
            first_seen=_parse_dt(first_seen),
            last_seen=_parse_dt(last_seen),
            alert_ids=[],
        )
        db.add(group)
        db.flush()

        for evt in evts:
            correlated = CorrelatedEvent(
                group_id=group.id,
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
            )
            db.add(correlated)

        alert = Alert(
            title=f"Correlation IP: {source_ip} - {len(evts)} evenements",
            description=f"Activite suspecte correlee depuis {source_ip}",
            severity=max_severity,
            source_ip=source_ip,
            rule_name="correlation_ip",
        )
        db.add(alert)
        db.flush()
        group.alert_ids = [alert.id]

        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def correlate_by_time_window(db: Session, events: list[dict], window_minutes: int = 10, min_events: int = 5) -> list[CorrelationGroup]:
    if not events:
        return []

    sorted_events = sorted(events, key=lambda e: e.get("observed_at", ""))
    windows = []
    current_window = [sorted_events[0]]

    for evt in sorted_events[1:]:
        prev_time = _parse_dt(current_window[-1].get("observed_at", ""))
        curr_time = _parse_dt(evt.get("observed_at", ""))
        if curr_time - prev_time <= timedelta(minutes=window_minutes):
            current_window.append(evt)
        else:
            if len(current_window) >= min_events:
                windows.append(current_window)
            current_window = [evt]

    if len(current_window) >= min_events:
        windows.append(current_window)

    groups = []
    for window_evts in windows:
        first_seen = _parse_dt(window_evts[0].get("observed_at", ""))
        last_seen = _parse_dt(window_evts[-1].get("observed_at", ""))
        source_ips = set(e.get("source_ip", "") for e in window_evts if e.get("source_ip"))
        target_ips = set(e.get("target_ip", "") for e in window_evts if e.get("target_ip"))
        event_types = set(e.get("event_type", "") for e in window_evts)
        severities = [e.get("severity", "info") for e in window_evts]
        max_severity = _highest_severity(severities)
        risk_score = _calculate_temporal_risk_score(window_evts, source_ips, target_ips, event_types, severities, window_minutes)

        group = CorrelationGroup(
            name=f"Burst d'activite sur {window_minutes}min (score: {risk_score})",
            group_type="temporal_burst",
            description=f"{len(window_evts)} evenements de {len(source_ips)} sources vers {len(target_ips)} cibles en {window_minutes}min",
            source_ip=", ".join(source_ips) if source_ips else None,
            severity=max_severity,
            event_count=len(window_evts),
            first_seen=first_seen,
            last_seen=last_seen,
            alert_ids=[],
        )
        db.add(group)
        db.flush()

        for evt in window_evts:
            correlated = CorrelatedEvent(
                group_id=group.id,
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
            )
            db.add(correlated)

        alert = Alert(
            title=f"Correlation temporelle: {len(window_evts)} evenements en {window_minutes}min (score {risk_score})",
            description=f"Burst detecte de {len(source_ips)} sources vers {len(target_ips)} cibles. Score de risque: {risk_score}/100",
            severity=max_severity,
            rule_name="correlation_temporal",
        )
        db.add(alert)
        db.flush()
        group.alert_ids = [alert.id]

        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def _calculate_temporal_risk_score(
    events: list[dict],
    source_ips: set,
    target_ips: set,
    event_types: set,
    severities: list[str],
    window_minutes: int,
) -> int:
    severity_weights = {"critical": 25, "high": 18, "medium": 10, "low": 4, "info": 1}
    attack_type_weights = {
        "network_scan": 12, "brute_force": 15, "malware_detected": 20,
        "privilege_escalation": 18, "data_exfiltration": 22, "traffic_burst": 8,
        "c2_communication": 20, "lateral_movement": 16, "ddos": 14,
    }

    score = 0

    event_count_score = min(len(events) * 2, 20)
    score += event_count_score

    severity_score = sum(severity_weights.get(s.lower(), 1) for s in severities)
    severity_score = min(severity_score, 30)
    score += severity_score

    type_diversity_score = min(len(event_types) * 5, 20)
    score += type_diversity_score

    for evt in events:
        etype = evt.get("event_type", "")
        score += attack_type_weights.get(etype, 2)
    score = min(score, 100)

    if len(source_ips) >= 3:
        score = min(score + 5, 100)
    if len(target_ips) >= 3:
        score = min(score + 5, 100)

    return min(score, 100)


def get_correlation_groups(db: Session, active_only: bool = True, group_type: str | None = None, severity: str | None = None) -> list[CorrelationGroup]:
    query = db.query(CorrelationGroup).order_by(CorrelationGroup.created_at.desc())
    if active_only:
        query = query.filter(CorrelationGroup.is_resolved.is_(False))
    if group_type:
        query = query.filter(CorrelationGroup.group_type == group_type)
    if severity:
        query = query.filter(CorrelationGroup.severity == severity)
    return query.all()


def get_group_by_id(db: Session, group_id: int) -> CorrelationGroup | None:
    return db.query(CorrelationGroup).filter(CorrelationGroup.id == group_id).first()


def get_group_events(db: Session, group_id: int) -> list[CorrelatedEvent]:
    return db.query(CorrelatedEvent).filter(CorrelatedEvent.group_id == group_id).order_by(CorrelatedEvent.observed_at).all()


def resolve_group(db: Session, group_id: int) -> CorrelationGroup | None:
    group = db.query(CorrelationGroup).filter(CorrelationGroup.id == group_id).first()
    if group is None:
        return None
    group.is_resolved = True
    db.commit()
    db.refresh(group)
    return group


def get_correlation_summary(db: Session) -> dict:
    groups = db.query(CorrelationGroup).all()
    active = [g for g in groups if not g.is_resolved]
    resolved = [g for g in groups if g.is_resolved]

    by_type = defaultdict(int)
    by_severity = defaultdict(int)
    ip_counts = defaultdict(int)
    for g in groups:
        by_type[g.group_type] += 1
        by_severity[g.severity] += 1
        if g.source_ip:
            for ip in g.source_ip.split(","):
                ip_counts[ip.strip()] += 1

    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_groups": len(groups),
        "active_groups": len(active),
        "resolved_groups": len(resolved),
        "by_type": dict(by_type),
        "by_severity": dict(by_severity),
        "top_source_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
    }


def enrich_with_ml_scores(db: Session, group_id: int) -> dict:
    group = db.query(CorrelationGroup).filter(CorrelationGroup.id == group_id).first()
    if group is None:
        return {"error": "Group not found"}

    correlated_events = db.query(CorrelatedEvent).filter(CorrelatedEvent.group_id == group_id).all()
    if not correlated_events:
        return {"group_id": group_id, "ml_enriched": False, "reason": "No events"}

    events = [
        {
            "source_ip": e.source_ip,
            "target_ip": e.target_ip,
            "event_type": e.event_type,
            "severity": e.severity,
            "message": e.message,
            "observed_at": e.observed_at.isoformat() if e.observed_at else "",
        }
        for e in correlated_events
    ]

    from app.ml.service import anomaly_detector
    anomaly_detector.fit(events)
    results = anomaly_detector.predict(events)

    anomaly_count = sum(1 for r in results if r["is_anomaly"])
    avg_score = sum(r["anomaly_score"] for r in results) / len(results) if results else 0

    ml_severity_boost = 0
    if avg_score > 0.7:
        ml_severity_boost = 2
    elif avg_score > 0.5:
        ml_severity_boost = 1

    if ml_severity_boost > 0:
        severity_order = ["low", "medium", "high", "critical"]
        current_idx = severity_order.index(group.severity) if group.severity in severity_order else 0
        new_idx = min(current_idx + ml_severity_boost, len(severity_order) - 1)
        group.severity = severity_order[new_idx]
        db.commit()

    return {
        "group_id": group_id,
        "ml_enriched": True,
        "total_events": len(results),
        "anomaly_count": anomaly_count,
        "avg_anomaly_score": round(avg_score, 3),
        "severity_boost": ml_severity_boost,
        "new_severity": group.severity,
    }


def _highest_severity(severities: list[str]) -> str:
    order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    max_val = 0
    result = "info"
    for s in severities:
        val = order.get(s.lower(), 1)
        if val > max_val:
            max_val = val
            result = s
    return result


def _parse_dt(dt_str: str) -> datetime:
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)
