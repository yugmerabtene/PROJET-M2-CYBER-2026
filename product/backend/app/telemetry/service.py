from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.telemetry.models import Agent, Heartbeat, TelemetryEvent
from app.telemetry.schemas import HeartbeatPayload, EventPayload


class TelemetryError(Exception):
    pass


def get_or_create_agent(db: Session, payload: HeartbeatPayload | EventPayload) -> Agent:
    agent = db.query(Agent).filter(Agent.sensor_id == payload.agent_id).first()
    if agent is None:
        agent = Agent(
            sensor_id=payload.agent_id,
            hostname=getattr(payload, "hostname", "unknown"),
            ip_address=getattr(payload, "ip_address", None),
            mode=getattr(payload, "mode", "fallback_active"),
            interfaces=getattr(payload, "interfaces", None),
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
    return agent


def update_agent_info(db: Session, agent: Agent, payload: HeartbeatPayload) -> None:
    if payload.hostname:
        agent.hostname = payload.hostname
    if payload.ip_address:
        agent.ip_address = payload.ip_address
    if payload.mode:
        agent.mode = payload.mode
    if payload.interfaces is not None:
        agent.interfaces = payload.interfaces
    agent.is_active = True


def record_heartbeat(db: Session, agent: Agent, payload: HeartbeatPayload) -> Heartbeat:
    update_agent_info(db, agent, payload)
    try:
        sent_at = datetime.fromisoformat(payload.sent_at.replace("Z", "+00:00"))
    except ValueError:
        sent_at = datetime.now(timezone.utc)

    heartbeat = Heartbeat(
        agent_id=agent.id,
        status=payload.status,
        sent_at=sent_at,
        raw_payload=payload.model_dump(),
    )
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    db.add(heartbeat)
    db.commit()
    db.refresh(heartbeat)
    return heartbeat


def record_event(db: Session, agent: Agent, payload: EventPayload) -> TelemetryEvent:
    try:
        observed_at = datetime.fromisoformat(payload.observed_at.replace("Z", "+00:00"))
    except ValueError:
        observed_at = datetime.now(timezone.utc)

    event = TelemetryEvent(
        agent_id=agent.id,
        source_ip=payload.source_ip or None,
        target_ip=payload.target_ip or None,
        event_type=payload.event_type,
        severity=payload.severity,
        message=payload.message,
        observed_at=observed_at,
        raw_payload=payload.raw_payload,
    )
    agent.last_heartbeat_at = datetime.now(timezone.utc)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_latest_heartbeat(db: Session, agent_id: int | None = None) -> Heartbeat | None:
    query = db.query(Heartbeat).order_by(Heartbeat.sent_at.desc())
    if agent_id is not None:
        query = query.filter(Heartbeat.agent_id == agent_id)
    return query.first()


def get_heartbeats(db: Session, limit: int = 50) -> list[Heartbeat]:
    return (
        db.query(Heartbeat)
        .order_by(Heartbeat.sent_at.desc())
        .limit(limit)
        .all()
    )


def get_events(
    db: Session,
    limit: int = 100,
    event_type: str | None = None,
    severity: str | None = None,
) -> list[TelemetryEvent]:
    query = db.query(TelemetryEvent).order_by(TelemetryEvent.observed_at.desc())
    if event_type:
        query = query.filter(TelemetryEvent.event_type == event_type)
    if severity:
        query = query.filter(TelemetryEvent.severity == severity)
    return query.limit(limit).all()


def get_agents(db: Session) -> list[Agent]:
    return db.query(Agent).order_by(Agent.last_heartbeat_at.desc()).all()


def get_agent_by_id(db: Session, agent_id: int) -> Agent | None:
    return db.query(Agent).filter(Agent.id == agent_id).first()
