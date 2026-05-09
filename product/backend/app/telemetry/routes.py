from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_agent
from app.telemetry.schemas import (
    AgentResponse,
    EventPayload,
    HeartbeatPayload,
    HeartbeatResponse,
    TelemetryEventResponse,
)
from app.telemetry.service import (
    TelemetryError,
    get_agent_by_id,
    get_agents,
    get_events,
    get_event_by_id,
    get_heartbeats,
    get_latest_heartbeat,
    get_or_create_agent,
    record_event,
    record_heartbeat,
)
from app.alerts.service import evaluate_detection_rules

router = APIRouter()


@router.post(
    "/heartbeat",
    response_model=HeartbeatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un heartbeat d'agent",
)
def ingest_heartbeat(
    payload: HeartbeatPayload,
    db: Session = Depends(get_db),
    _agent=Depends(require_agent),
):
    try:
        agent = get_or_create_agent(db, payload)
        heartbeat = record_heartbeat(db, agent, payload)
        return heartbeat
    except TelemetryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/events",
    response_model=TelemetryEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrer un événement de télémétrie",
)
def ingest_event(
    payload: EventPayload,
    db: Session = Depends(get_db),
    _agent=Depends(require_agent),
):
    try:
        agent = get_or_create_agent(db, payload)
        event = record_event(db, agent, payload)

        # Broadcast real-time update
        from app.core.realtime import send_dashboard_update
        send_dashboard_update()

        # Trigger alert evaluation for recent events from same source IP
        if payload.source_ip:
            recent_events = get_events(db, limit=20, event_type=None, severity=None)
            events_dict = [
                {
                    "source_ip": e.source_ip,
                    "target_ip": e.target_ip,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "message": e.message,
                    "raw_payload": e.raw_payload,
                }
                for e in recent_events
                if e.source_ip
            ]
            evaluate_detection_rules(db, events_dict)

        return event
    except TelemetryError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/heartbeat",
    response_model=HeartbeatResponse | None,
    summary="Dernier heartbeat enregistré",
)
def get_last_heartbeat(
    agent_id: int | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_latest_heartbeat(db, agent_id)


@router.get(
    "/heartbeats",
    response_model=list[HeartbeatResponse],
    summary="Liste des heartbeats",
)
def list_heartbeats(
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_heartbeats(db, limit)


@router.get(
    "/events",
    response_model=list[TelemetryEventResponse],
    summary="Liste des événements de télémétrie",
)
def list_events(
    limit: int = Query(100, le=1000),
    event_type: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_events(db, limit, event_type, severity)


@router.get(
    "/events/{event_id}",
    summary="Detail enrichi d'un evenement de telemetrique",
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    event = get_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evenement introuvable")

    from app.alerts.models import Alert
    from app.correlation.models import CorrelatedEvent, CorrelationGroup

    related_alerts = (
        db.query(Alert)
        .filter(
            ((Alert.source_ip == event.source_ip) & (Alert.source_ip.is_not(None)))
            | ((Alert.target_ip == event.target_ip) & (Alert.target_ip.is_not(None)))
        )
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    correlated = (
        db.query(CorrelatedEvent)
        .filter(
            (CorrelatedEvent.telemetry_event_id == event.id)
            | (
                (CorrelatedEvent.source_ip == event.source_ip)
                & (CorrelatedEvent.event_type == event.event_type)
            )
        )
        .all()
    )
    group_ids = list({c.group_id for c in correlated})
    related_correlations = (
        db.query(CorrelationGroup)
        .filter(CorrelationGroup.id.in_(group_ids))
        .all()
        if group_ids
        else []
    )

    similar_events = (
        db.query(type(event))
        .filter(
            type(event).id != event.id,
            type(event).event_type == event.event_type,
            ((type(event).source_ip == event.source_ip) & (type(event).source_ip.is_not(None)))
            | ((type(event).target_ip == event.target_ip) & (type(event).target_ip.is_not(None))),
        )
        .order_by(type(event).observed_at.desc())
        .limit(10)
        .all()
    )

    return {
        "id": event.id,
        "agent_id": event.agent_id,
        "agent": {
            "id": event.agent.id,
            "sensor_id": event.agent.sensor_id,
            "hostname": event.agent.hostname,
            "ip_address": event.agent.ip_address,
            "mode": event.agent.mode,
            "last_heartbeat_at": event.agent.last_heartbeat_at,
        } if event.agent else None,
        "source_ip": event.source_ip,
        "target_ip": event.target_ip,
        "event_type": event.event_type,
        "severity": event.severity,
        "message": event.message,
        "observed_at": event.observed_at,
        "received_at": event.received_at,
        "raw_payload": event.raw_payload,
        "related_alerts": [
            {
                "id": a.id,
                "title": a.title,
                "severity": a.severity,
                "status": a.status,
                "rule_name": a.rule_name,
                "created_at": a.created_at,
            }
            for a in related_alerts
        ],
        "related_correlations": [
            {
                "id": g.id,
                "group_type": g.group_type,
                "severity": g.severity,
                "event_count": g.event_count,
                "correlation_score": g.correlation_score,
                "is_resolved": g.is_resolved,
            }
            for g in related_correlations
        ],
        "similar_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "severity": e.severity,
                "source_ip": e.source_ip,
                "target_ip": e.target_ip,
                "message": e.message,
                "observed_at": e.observed_at,
            }
            for e in similar_events
        ],
    }


@router.get(
    "/agents",
    response_model=list[AgentResponse],
    summary="Liste des agents enregistrés",
)
def list_agents(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_agents(db)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Détail d'un agent",
)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    agent = get_agent_by_id(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent introuvable")
    return agent
