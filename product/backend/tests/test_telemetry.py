from datetime import datetime, timezone

from app.telemetry.service import (
    get_or_create_agent,
    record_heartbeat,
    record_event,
    get_latest_heartbeat,
    get_heartbeats,
    get_events,
    get_agents,
    get_agent_by_id,
)
from app.telemetry.schemas import HeartbeatPayload, EventPayload


def test_get_or_create_agent(db_session):
    payload = HeartbeatPayload(
        agent_id="sensor-test-01",
        hostname="test-host",
        ip_address="10.0.0.1",
        mode="passive_lite",
        interfaces=["eth0"],
        sent_at=datetime.now(timezone.utc).isoformat(),
    )
    agent = get_or_create_agent(db_session, payload)
    assert agent.sensor_id == "sensor-test-01"
    assert agent.hostname == "test-host"

    agent2 = get_or_create_agent(db_session, payload)
    assert agent2.id == agent.id


def test_record_heartbeat(db_session):
    payload = HeartbeatPayload(
        agent_id="sensor-hb-01",
        hostname="hb-host",
        ip_address="10.0.0.2",
        status="alive",
        mode="passive_full",
        interfaces=["eth0", "eth1"],
        sent_at="2026-05-06T10:00:00Z",
    )
    agent = get_or_create_agent(db_session, payload)
    heartbeat = record_heartbeat(db_session, agent, payload)

    assert heartbeat.agent_id == agent.id
    assert heartbeat.status == "alive"
    assert heartbeat.raw_payload is not None


def test_record_event(db_session):
    event_payload = EventPayload(
        agent_id="sensor-ev-01",
        source_ip="192.168.1.50",
        target_ip="10.0.0.5",
        event_type="suspicious_connection",
        severity="medium",
        message="Test event",
        observed_at="2026-05-06T10:05:00Z",
        raw_payload={"test": True},
    )
    agent = get_or_create_agent(db_session, event_payload)
    event = record_event(db_session, agent, event_payload)

    assert event.agent_id == agent.id
    assert event.event_type == "suspicious_connection"
    assert event.severity == "medium"


def test_get_latest_heartbeat(db_session):
    payload = HeartbeatPayload(
        agent_id="sensor-latest",
        hostname="latest-host",
        sent_at="2026-05-06T10:00:00Z",
    )
    agent = get_or_create_agent(db_session, payload)
    record_heartbeat(db_session, agent, payload)

    latest = get_latest_heartbeat(db_session)
    assert latest is not None
    assert latest.agent_id == agent.id


def test_get_events_filtered(db_session):
    payloads = [
        EventPayload(
            agent_id="sensor-filter",
            source_ip="10.0.0.1",
            event_type="scan",
            severity="high",
            message="Scan event",
            observed_at="2026-05-06T10:00:00Z",
        ),
        EventPayload(
            agent_id="sensor-filter",
            source_ip="10.0.0.2",
            event_type="heartbeat_extra",
            severity="info",
            message="Info event",
            observed_at="2026-05-06T10:01:00Z",
        ),
    ]
    agent = get_or_create_agent(db_session, payloads[0])
    for p in payloads:
        record_event(db_session, agent, p)

    high_events = get_events(db_session, severity="high")
    assert len(high_events) == 1
    assert high_events[0].severity == "high"

    all_events = get_events(db_session)
    assert len(all_events) >= 2


def test_get_agents(db_session):
    payload = HeartbeatPayload(
        agent_id="sensor-list",
        hostname="list-host",
        sent_at="2026-05-06T10:00:00Z",
    )
    get_or_create_agent(db_session, payload)
    agents = get_agents(db_session)
    assert len(agents) > 0
    assert any(a.sensor_id == "sensor-list" for a in agents)


def test_agent_lifecycle(db_session):
    payload = HeartbeatPayload(
        agent_id="sensor-lifecycle",
        hostname="lifecycle-host",
        ip_address="10.0.0.99",
        sent_at="2026-05-06T10:00:00Z",
    )
    agent = get_or_create_agent(db_session, payload)
    assert agent.is_active is True

    record_heartbeat(db_session, agent, payload)
    assert agent.last_heartbeat_at is not None

    fetched = get_agent_by_id(db_session, agent.id)
    assert fetched is not None
    assert fetched.sensor_id == "sensor-lifecycle"
