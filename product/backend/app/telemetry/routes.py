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
    get_heartbeats,
    get_latest_heartbeat,
    get_or_create_agent,
    record_event,
    record_heartbeat,
)

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
