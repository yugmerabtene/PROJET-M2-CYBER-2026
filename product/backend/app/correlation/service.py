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

        # Calcul du score temporel et composite
        source_ips = {source_ip}
        target_ips = set(e.get("target_ip", "") for e in evts if e.get("target_ip"))
        temporal_score = _calculate_temporal_risk_score(
            evts, source_ips, target_ips, event_types, severities, window_minutes
        )

        score_data = calculate_composite_score(evts, temporal_score, "ip_source")

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
            correlation_score=score_data["composite_score"],
            score_breakdown=score_data["breakdown"],
        )
        db.add(group)
        db.flush()

        for idx, evt in enumerate(evts):
            correlated = CorrelatedEvent(
                group_id=group.id,
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
                sequence_order=idx,
                ml_anomaly_score=0.0,
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
        setattr(group, "alert_ids", [alert.id])

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

        score_data = calculate_composite_score(window_evts, risk_score, "temporal_burst")

        group = CorrelationGroup(
            name=f"Burst d'activite sur {window_minutes}min (score: {score_data['composite_score']})",
            group_type="temporal_burst",
            description=f"{len(window_evts)} evenements de {len(source_ips)} sources vers {len(target_ips)} cibles en {window_minutes}min",
            source_ip=", ".join(source_ips) if source_ips else None,
            severity=max_severity,
            event_count=len(window_evts),
            first_seen=first_seen,
            last_seen=last_seen,
            correlation_score=score_data["composite_score"],
            score_breakdown=score_data["breakdown"],
        )
        db.add(group)
        db.flush()

        for idx, evt in enumerate(window_evts):
            correlated = CorrelatedEvent(
                group_id=group.id,
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
                sequence_order=idx,
                ml_anomaly_score=0.0,
            )
            db.add(correlated)

        alert = Alert(
            title=f"Correlation temporelle: {len(window_evts)} evenements en {window_minutes}min (score {score_data['composite_score']})",
            description=f"Burst detecte de {len(source_ips)} sources vers {len(target_ips)} cibles. Score de risque: {score_data['composite_score']}/100",
            severity=max_severity,
            rule_name="correlation_temporal",
        )
        db.add(alert)
        db.flush()
        setattr(group, "alert_ids", [alert.id])

        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def calculate_composite_score(
    events: list[dict],
    temporal_score: int,
    group_type: str = "unknown"
) -> dict:
    """
    Score composite (0-100) basé uniquement sur les événements :
    - temporal_score (45%)
    - diversity (30%)
    - severity (25%)
    """
    temporal_contribution = temporal_score * 0.45

    # 3. Diversity score
    unique_types = len(set(e.get("event_type", "") for e in events))
    unique_sources = len(set(e.get("source_ip", "") for e in events if e.get("source_ip")))
    unique_targets = len(set(e.get("target_ip", "") for e in events if e.get("target_ip")))

    diversity_score = min(unique_types * 10, 30) + min(unique_sources * 5, 20) + min(unique_targets * 5, 20)
    diversity_contribution = min(diversity_score, 100) * 0.30

    # 4. Severity score
    severity_weights = {"critical": 25, "high": 18, "medium": 10, "low": 4}
    severity_score = min(sum(severity_weights.get(e.get("severity", ""), 1) for e in events), 30)
    severity_contribution = severity_score * 0.25

    composite = min(int(temporal_contribution + diversity_contribution + severity_contribution), 100)

    return {
        "composite_score": composite,
        "breakdown": {
            "temporal": {"score": temporal_score, "weight": 0.45, "contribution": round(temporal_contribution, 2)},
            "diversity": {"score": diversity_score, "weight": 0.30, "contribution": round(diversity_contribution, 2)},
            "severity": {"score": severity_score, "weight": 0.25, "contribution": round(severity_contribution, 2)},
        }
    }


def _calculate_temporal_risk_score(
    events: list[dict],
    source_ips: set,
    target_ips: set,
    event_types: set,
    severities: list[str],
    window_minutes: int,
) -> int:
    severity_weights = {"critical": 25, "high": 18, "medium": 10, "low": 4, "info": 1}

    score = 0

    event_count_score = min(len(events) * 2, 20)
    score += event_count_score

    severity_score = sum(severity_weights.get(s.lower(), 1) for s in severities)
    severity_score = min(severity_score, 30)
    score += severity_score

    type_diversity_score = min(len(event_types) * 5, 20)
    score += type_diversity_score

    for evt in events:
        attack_type_weights = {
            "network_scan": 12, "brute_force": 15, "malware_detected": 20,
            "privilege_escalation": 18, "data_exfiltration": 22, "traffic_burst": 8,
            "c2_communication": 20, "lateral_movement": 16, "ddos": 14,
        }
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


def get_group_events_with_sequence(db: Session, group_id: int) -> list[dict]:
    events = db.query(CorrelatedEvent).filter(CorrelatedEvent.group_id == group_id).order_by(CorrelatedEvent.sequence_order).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "source_ip": e.source_ip,
            "target_ip": e.target_ip,
            "severity": e.severity,
            "message": e.message,
            "observed_at": e.observed_at.isoformat() if e.observed_at else "",
            "sequence_order": e.sequence_order,
        }
        for e in events
    ]


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
    return {"error": "Feature disabled"}


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


# ========== NOUVEAUX TYPES DE CORRÉLATION ==========

def correlate_by_hostname(db: Session, events: list[dict], min_events: int = 3) -> list[CorrelationGroup]:
    """Regroupe les événements par hostname cible."""
    hostname_events: dict[str, list[dict]] = defaultdict(list)
    for evt in events:
        # Try to get hostname from raw_payload or use source_ip as fallback
        hostname = (evt.get("raw_payload") or {}).get("hostname") or evt.get("source_ip", "")
        if hostname:
            hostname_events[hostname].append(evt)

    groups = []
    for hostname, evts in hostname_events.items():
        if len(evts) < min_events:
            continue

        sorted_evts = sorted(evts, key=lambda e: e.get("observed_at", ""))
        first_seen = sorted_evts[0].get("observed_at", "")
        last_seen = sorted_evts[-1].get("observed_at", "")
        event_types = set(e.get("event_type", "") for e in evts)
        severities = [e.get("severity", "info") for e in evts]
        max_severity = _highest_severity(severities)

        temporal_score = _calculate_temporal_risk_score(
            evts, {hostname}, set(), event_types, severities, 60
        )

        score_data = calculate_composite_score(evts, temporal_score, "hostname_match")

        group = CorrelationGroup(
            name=f"Activité suspecte sur {hostname}",
            group_type="hostname_match",
            description=f"{len(evts)} événements de {len(event_types)} types différents",
            source_ip=evts[0].get("source_ip"),
            target_ip=None,
            severity=max_severity,
            event_count=len(evts),
            first_seen=_parse_dt(first_seen),
            last_seen=_parse_dt(last_seen),
            hostname=hostname,
            correlation_score=score_data["composite_score"],
            score_breakdown=score_data["breakdown"],
        )
        db.add(group)
        db.flush()

        for idx, evt in enumerate(evts):
            correlated = CorrelatedEvent(
                group_id=group.id,
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
                sequence_order=idx,
                ml_anomaly_score=0.0,
            )
            db.add(correlated)

        alert = Alert(
            title=f"Corrélation Hostname: {hostname} - {len(evts)} événements",
            description=f"Activité suspecte corrélée sur {hostname}",
            severity=max_severity,
            source_ip=evts[0].get("source_ip"),
            rule_name="correlation_hostname",
        )
        db.add(alert)
        db.flush()
        setattr(group, "alert_ids", [alert.id])

        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def correlate_by_session(db: Session, events: list[dict], min_events: int = 3, window_minutes: int = 30) -> list[CorrelationGroup]:
    sessions: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for evt in events:
        src = evt.get("source_ip") or ""
        dst = evt.get("target_ip") or ""
        if src and dst:
            sessions[(src, dst)].append(evt)

    groups = []
    for (source_ip, target_ip), evts in sessions.items():
        if len(evts) < min_events:
            continue

        sorted_evts = sorted(evts, key=lambda e: e.get("observed_at", ""))
        first_seen = _parse_dt(sorted_evts[0].get("observed_at", ""))
        last_seen = _parse_dt(sorted_evts[-1].get("observed_at", ""))
        if (last_seen - first_seen) > timedelta(minutes=window_minutes):
            continue

        event_types = set(e.get("event_type", "") for e in sorted_evts)
        if len(event_types) < 2:
            continue

        severities = [e.get("severity", "info") for e in sorted_evts]
        max_severity = _highest_severity(severities)
        temporal_score = _calculate_temporal_risk_score(sorted_evts, {source_ip}, {target_ip}, event_types, severities, window_minutes)
        score_data = calculate_composite_score(sorted_evts, temporal_score, "session_flow")

        group = CorrelationGroup(
            name=f"Session suspecte {source_ip} -> {target_ip}",
            group_type="session_flow",
            description=f"{len(sorted_evts)} événements corrélés sur la même session source → cible.",
            source_ip=source_ip,
            target_ip=target_ip,
            severity=max_severity,
            event_count=len(sorted_evts),
            first_seen=first_seen,
            last_seen=last_seen,
            correlation_score=score_data["composite_score"],
            score_breakdown=score_data["breakdown"],
        )
        db.add(group)
        db.flush()

        for idx, evt in enumerate(sorted_evts):
            db.add(CorrelatedEvent(
                group_id=group.id,
                telemetry_event_id=evt.get("telemetry_event_id") or evt.get("id"),
                source_ip=evt.get("source_ip"),
                target_ip=evt.get("target_ip"),
                event_type=evt.get("event_type", "unknown"),
                severity=evt.get("severity", "info"),
                message=evt.get("message"),
                observed_at=_parse_dt(evt.get("observed_at", "")),
                raw_payload=evt.get("raw_payload"),
                sequence_order=idx,
                ml_anomaly_score=0.0,
            ))

        alert = Alert(
            title=f"Corrélation session {source_ip} -> {target_ip}",
            description=f"Session regroupée avec {len(sorted_evts)} événements et {len(event_types)} types.",
            severity=max_severity,
            source_ip=source_ip,
            target_ip=target_ip,
            rule_name="correlation_session",
        )
        db.add(alert)
        db.flush()
        setattr(group, "alert_ids", [alert.id])
        groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def run_full_correlation_from_db(db: Session, lookback_minutes: int = 120, limit: int = 2000) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
    db_events = (
        db.query(TelemetryEvent)
        .filter(TelemetryEvent.observed_at >= cutoff)
        .order_by(TelemetryEvent.observed_at.desc())
        .limit(limit)
        .all()
    )
    events = [
        {
            "id": e.id,
            "telemetry_event_id": e.id,
            "source_ip": e.source_ip,
            "target_ip": e.target_ip,
            "event_type": e.event_type,
            "severity": e.severity,
            "message": e.message,
            "observed_at": e.observed_at.isoformat() if e.observed_at else "",
            "raw_payload": e.raw_payload,
        }
        for e in db_events
    ]
    if not events:
        return {"events_considered": 0, "created": {"ip_source": 0, "temporal_burst": 0, "hostname_match": 0, "session_flow": 0, "attack_chain": 0}, "groups": []}

    created_ip = correlate_by_ip(db, events, min_events=3, window_minutes=min(lookback_minutes, 60))
    created_temporal = correlate_by_time_window(db, events, window_minutes=10, min_events=5)
    created_hostname = correlate_by_hostname(db, events, min_events=3)
    created_session = correlate_by_session(db, events, min_events=3, window_minutes=30)
    created_chain = detect_attack_chains(db, events)
    groups = [*created_ip, *created_temporal, *created_hostname, *created_session, *created_chain]

    return {
        "events_considered": len(events),
        "created": {
            "ip_source": len(created_ip),
            "temporal_burst": len(created_temporal),
            "hostname_match": len(created_hostname),
            "session_flow": len(created_session),
            "attack_chain": len(created_chain),
        },
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "group_type": g.group_type,
                "severity": g.severity,
                "event_count": g.event_count,
                "correlation_score": g.correlation_score,
            }
            for g in groups
        ],
    }


def detect_attack_chains(db: Session, events: list[dict]) -> list[CorrelationGroup]:
    """Détecte des séquences logiques dans les événements."""
    ATTACK_CHAIN_PATTERNS = {
        "recon_to_exploit": {
            "sequence": ["network_scan", "port_scan", "brute_force", "privilege_escalation"],
            "max_time_between_steps": 300,  # 5 minutes
            "description": "Reconnaissance → Exploitation"
        },
        "data_breach": {
            "sequence": ["brute_force", "suspicious_login", "privilege_escalation", "data_exfiltration"],
            "max_time_between_steps": 600,  # 10 minutes
            "description": "Brute force → Exfiltration de données"
        },
        "lateral_movement": {
            "sequence": ["compromised_host", "lateral_movement", "c2_communication"],
            "max_time_between_steps": 180,
            "description": "Mouvement latéral → C2"
        }
    }

    sorted_events = sorted(events, key=lambda e: e.get("observed_at", ""))
    groups = []

    for pattern_name, pattern in ATTACK_CHAIN_PATTERNS.items():
        sequences = _find_sequences(sorted_events, pattern["sequence"], pattern["max_time_between_steps"])

        for seq in sequences:
            # Create a group of type attack_chain
            group = CorrelationGroup(
                name=f"Chaîne d'attaque: {pattern['description']}",
                group_type="attack_chain",
                attack_chain_type=pattern_name,
                description=f"Séquence détectée: {' → '.join(pattern['sequence'])}",
                severity=_calculate_chain_severity(seq),
                event_count=len(seq),
                first_seen=_parse_dt(seq[0].get("observed_at")),
                last_seen=_parse_dt(seq[-1].get("observed_at")),
                correlation_score=_calculate_chain_score(seq, pattern),
                hostname=None,
            )
            db.add(group)
            db.flush()

            # Add events with sequence order
            for idx, evt in enumerate(seq):
                correlated = CorrelatedEvent(
                    group_id=group.id,
                    source_ip=evt.get("source_ip"),
                    target_ip=evt.get("target_ip"),
                    event_type=evt.get("event_type", "unknown"),
                    severity=evt.get("severity", "info"),
                    message=evt.get("message"),
                    observed_at=_parse_dt(evt.get("observed_at", "")),
                    raw_payload=evt.get("raw_payload"),
                    sequence_order=idx,
                    ml_anomaly_score=0.0,
                )
                db.add(correlated)

            alert = Alert(
                title=f"Chaîne d'attaque détectée: {pattern['description']}",
                description=f"Séquence logique: {' → '.join(pattern['sequence'])}",
                severity=group.severity,
                source_ip=seq[0].get("source_ip"),
                rule_name="attack_chain_detected",
            )
            db.add(alert)
            db.flush()
            setattr(group, "alert_ids", [alert.id])

            groups.append(group)

    db.commit()
    for g in groups:
        db.refresh(g)
    return groups


def _find_sequences(events: list[dict], pattern: list[str], max_time_diff: int) -> list[list[dict]]:
    """Trouve des séquences correspondant au pattern."""
    sequences = []
    n = len(pattern)

    for i in range(len(events) - n + 1):
        sequence = []
        valid = True

        for j in range(n):
            if events[i + j].get("event_type") != pattern[j]:
                valid = False
                break
            if j > 0:
                # Vérifier le temps entre les étapes
                t1 = _parse_dt(events[i + j - 1].get("observed_at"))
                t2 = _parse_dt(events[i + j].get("observed_at"))
                if (t2 - t1).total_seconds() > max_time_diff:
                    valid = False
                    break
            sequence.append(events[i + j])

        if valid and sequence:
            sequences.append(sequence)

    return sequences


def _calculate_chain_severity(seq: list[dict]) -> str:
    """Calcule la sévérité d'une chaîne d'attaque."""
    severities = [e.get("severity", "info") for e in seq]
    return _highest_severity(severities)


def _calculate_chain_score(seq: list[dict], pattern: dict) -> int:
    """Score spécifique pour une chaîne d'attaque."""
    base_score = 60  # Base for chain detection

    # Bonus for critical steps
    critical_steps = sum(1 for e in seq if e.get("severity") == "critical")
    base_score += critical_steps * 10

    # Bonus for chain length
    base_score += len(seq) * 5

    return min(base_score, 100)


def create_manual_group(db: Session, event_ids: list[int], group_name: str, group_type: str, username: str) -> CorrelationGroup:
    """Permet à l'analyste de regrouper manuellement des événements."""
    events = db.query(TelemetryEvent).filter(TelemetryEvent.id.in_(event_ids)).all()
    if not events:
        raise CorrelationError("No events found")

    sorted_events = sorted(events, key=lambda e: e.observed_at or datetime.now(timezone.utc))
    source_ips = set(e.source_ip for e in events if e.source_ip)
    target_ips = set(e.target_ip for e in events if e.target_ip)
    event_types = set(e.event_type for e in events)

    temporal_score = 50  # Default for manual
    score_data = calculate_composite_score(
        [{"event_type": e.event_type, "severity": e.severity, "source_ip": e.source_ip, "target_ip": e.target_ip} for e in events],
        temporal_score,
        group_type
    )

    group = CorrelationGroup(
        name=group_name,
        group_type=group_type,
        description=f"Groupe manuel: {len(events)} événements",
        source_ip=", ".join(source_ips) if source_ips else None,
        target_ip=", ".join(target_ips) if target_ips else None,
        severity=_highest_severity([e.severity for e in events]),
        event_count=len(events),
        first_seen=sorted_events[0].observed_at,
        last_seen=sorted_events[-1].observed_at,
        correlation_score=score_data["composite_score"],
        score_breakdown=score_data["breakdown"],
    )
    db.add(group)
    db.flush()

    for idx, evt in enumerate(sorted_events):
        correlated = CorrelatedEvent(
            group_id=group.id,
            telemetry_event_id=evt.id,
            source_ip=evt.source_ip,
            target_ip=evt.target_ip,
            event_type=evt.event_type,
            severity=evt.severity,
            message=evt.message,
            observed_at=evt.observed_at,
            raw_payload=evt.raw_payload,
            sequence_order=idx,
            ml_anomaly_score=0.0,
        )
        db.add(correlated)

    alert = Alert(
        title=f"Groupe manuel: {group_name}",
        description=f"Créé par {username}",
        severity=group.severity,
        source_ip=group.source_ip,
        rule_name="manual_correlation",
    )
    db.add(alert)
    db.flush()
    setattr(group, "alert_ids", [alert.id])

    db.commit()
    db.refresh(group)
    return group
