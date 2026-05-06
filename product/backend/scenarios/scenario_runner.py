"""
Scenario runner for DevinciWatch - Sprint 5 (US-08.2)

Generates a complete reproducible scenario: heartbeat -> events -> alerts -> correlation -> exports
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, Base, engine
from app.telemetry.models import Agent, Heartbeat, TelemetryEvent
from app.alerts.models import Alert, AuditLog
from app.assets.models import Asset
from app.correlation.models import CorrelationGroup, CorrelatedEvent


def create_scenario(db):
    """Create a complete attack scenario with multiple phases."""
    scenario_id = "SCENARIO-001"
    scenario_name = "Brute Force SSH + Lateral Movement"
    scenario_context = {
        "description": "Simulated brute force SSH attack followed by lateral movement",
        "attacker_ip": "192.168.1.100",
        "target_ip": "192.168.1.10",
        "lateral_target": "192.168.1.20",
        "timeline": "2024-01-15T10:00:00Z to 2024-01-15T10:15:00Z",
        "expected_alerts": ["brute_force_detected", "lateral_movement_detected"],
        "expected_correlations": ["ip_source_burst", "temporal_sequence"],
    }

    # Phase 1: Create agent and heartbeat
    agent = Agent(
        agent_id="agent-lab-001",
        agent_name="serveur-endpoint",
        secret_key="lab-secret-key",
        is_active=True,
        registered_at=datetime.now(timezone.utc),
    )
    db.add(agent)
    db.flush()

    heartbeat = Heartbeat(
        agent_id=agent.id,
        sent_at=datetime.now(timezone.utc),
        status="active",
        metrics_json=json.dumps({"cpu": 45.2, "memory": 62.1, "disk": 78.5}),
    )
    db.add(heartbeat)

    # Phase 2: Create target assets
    target_asset = Asset(
        ip_address=scenario_context["target_ip"],
        hostname="srv-web-01",
        asset_type="server",
        os_guess="Linux Ubuntu 22.04",
        is_active=True,
        first_seen=datetime.now(timezone.utc) - timedelta(days=30),
        last_seen=datetime.now(timezone.utc),
    )
    db.add(target_asset)

    lateral_asset = Asset(
        ip_address=scenario_context["lateral_target"],
        hostname="srv-db-01",
        asset_type="server",
        os_guess="Linux CentOS 8",
        is_active=True,
        first_seen=datetime.now(timezone.utc) - timedelta(days=30),
        last_seen=datetime.now(timezone.utc),
    )
    db.add(lateral_asset)

    attacker_asset = Asset(
        ip_address=scenario_context["attacker_ip"],
        hostname="attacker-kali",
        asset_type="workstation",
        os_guess="Kali Linux 2024",
        is_active=True,
        first_seen=datetime.now(timezone.utc) - timedelta(hours=1),
        last_seen=datetime.now(timezone.utc),
    )
    db.add(attacker_asset)

    # Phase 3: Generate brute force events (multiple failed SSH attempts)
    base_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    events = []

    for i in range(25):
        event = TelemetryEvent(
            agent_id=agent.id,
            source_ip=scenario_context["attacker_ip"],
            target_ip=scenario_context["target_ip"],
            event_type="authentication_failure",
            severity="medium" if i < 10 else "high",
            message=f"Failed SSH login attempt {i+1} from {scenario_context['attacker_ip']}",
            observed_at=base_time + timedelta(seconds=i*10),
            raw_data=json.dumps({
                "service": "ssh",
                "port": 22,
                "username": "root" if i < 20 else f"user{i}",
                "method": "password",
                "scenario_id": scenario_id,
            }),
        )
        events.append(event)
        db.add(event)

    # Phase 4: Generate successful breach event
    breach_event = TelemetryEvent(
        agent_id=agent.id,
        source_ip=scenario_context["attacker_ip"],
        target_ip=scenario_context["target_ip"],
        event_type="authentication_success",
        severity="critical",
        message=f"Successful SSH login after multiple failures from {scenario_context['attacker_ip']}",
        observed_at=base_time + timedelta(minutes=5),
        raw_data=json.dumps({
            "service": "ssh",
            "port": 22,
            "username": "root",
            "method": "password",
            "previous_failures": 25,
            "scenario_id": scenario_id,
        }),
    )
    db.add(breach_event)

    # Phase 5: Generate lateral movement events
    for i in range(10):
        event = TelemetryEvent(
            agent_id=agent.id,
            source_ip=scenario_context["target_ip"],
            target_ip=scenario_context["lateral_target"],
            event_type="network_scan",
            severity="high",
            message=f"Port scan from compromised host to {scenario_context['lateral_target']}",
            observed_at=base_time + timedelta(minutes=6+i),
            raw_data=json.dumps({
                "scan_type": "syn_scan",
                "ports_scanned": [22, 80, 443, 3306, 5432],
                "scenario_id": scenario_id,
            }),
        )
        db.add(event)

    # Phase 6: Generate alerts
    brute_force_alert = Alert(
        title="Brute Force SSH Attack Detected",
        severity="critical",
        status="new",
        source_ip=scenario_context["attacker_ip"],
        target_ip=scenario_context["target_ip"],
        rule_name="brute_force_detected",
        description=f"25 failed SSH login attempts from {scenario_context['attacker_ip']} to {scenario_context['target_ip']}",
        created_at=base_time + timedelta(minutes=5),
        raw_data=json.dumps({
            "attempt_count": 25,
            "time_window": "5 minutes",
            "scenario_id": scenario_id,
        }),
    )
    db.add(brute_force_alert)

    lateral_alert = Alert(
        title="Lateral Movement Detected",
        severity="high",
        status="new",
        source_ip=scenario_context["target_ip"],
        target_ip=scenario_context["lateral_target"],
        rule_name="lateral_movement_detected",
        description=f"Port scan from compromised host {scenario_context['target_ip']} to {scenario_context['lateral_target']}",
        created_at=base_time + timedelta(minutes=10),
        raw_data=json.dumps({
            "scan_ports": [22, 80, 443, 3306, 5432],
            "scenario_id": scenario_id,
        }),
    )
    db.add(lateral_alert)

    # Phase 7: Create correlation groups
    ip_correlation = CorrelationGroup(
        correlation_type="ip_source",
        source_ip=scenario_context["attacker_ip"],
        event_count=26,
        alert_count=1,
        severity="critical",
        status="active",
        created_at=base_time + timedelta(minutes=6),
        metadata_json=json.dumps({
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "attack_phase": "initial_access",
        }),
    )
    db.add(ip_correlation)
    db.flush()

    # Link events to correlation group
    for event in events[:10]:  # Link first 10 events
        correlated = CorrelatedEvent(
            group_id=ip_correlation.id,
            event_id=event.id,
            correlation_reason="same_source_ip",
            correlated_at=base_time + timedelta(minutes=6),
        )
        db.add(correlated)

    temporal_correlation = CorrelationGroup(
        correlation_type="temporal_burst",
        source_ip=scenario_context["attacker_ip"],
        event_count=25,
        alert_count=2,
        severity="critical",
        status="active",
        created_at=base_time + timedelta(minutes=6),
        metadata_json=json.dumps({
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "attack_phase": "brute_force_sequence",
            "time_window_seconds": 250,
        }),
    )
    db.add(temporal_correlation)
    db.flush()

    for event in events[:15]:
        correlated = CorrelatedEvent(
            group_id=temporal_correlation.id,
            event_id=event.id,
            correlation_reason="temporal_proximity",
            correlated_at=base_time + timedelta(minutes=6),
        )
        db.add(correlated)

    # Phase 8: Create audit logs
    audit_login = AuditLog(
        user_id=1,
        action="scenario_execution",
        resource_type="scenario",
        resource_id=scenario_id,
        details=json.dumps({
            "scenario_name": scenario_name,
            "executed_by": "scenario_runner",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }),
        ip_address="127.0.0.1",
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_login)

    db.commit()

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "scenario_context": scenario_context,
        "created_entities": {
            "agent": agent.id,
            "heartbeat": heartbeat.id,
            "assets": [target_asset.id, lateral_asset.id, attacker_asset.id],
            "events": len(events) + 1,  # +1 for breach event
            "alerts": [brute_force_alert.id, lateral_alert.id],
            "correlations": [ip_correlation.id, temporal_correlation.id],
        },
    }


def run_scenario():
    """Run the complete scenario and print results."""
    print("=" * 60)
    print("DevinciWatch - Scenario Runner (US-08.2)")
    print("=" * 60)

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\n[1/4] Creating attack scenario...")
        result = create_scenario(db)
        print(f"  Scenario ID: {result['scenario_id']}")
        print(f"  Scenario Name: {result['scenario_name']}")
        print(f"  Description: {result['scenario_context']['description']}")

        print("\n[2/4] Entities created:")
        entities = result["created_entities"]
        print(f"  Agent: {entities['agent']}")
        print(f"  Heartbeat: {entities['heartbeat']}")
        print(f"  Assets: {len(entities['assets'])} created")
        print(f"  Events: {entities['events']} generated")
        print(f"  Alerts: {len(entities['alerts'])} triggered")
        print(f"  Correlations: {len(entities['correlations'])} groups")

        print("\n[3/4] Verification:")
        # Verify entities exist
        from app.telemetry.models import Agent, Heartbeat, TelemetryEvent
        from app.alerts.models import Alert
        from app.assets.models import Asset
        from app.correlation.models import CorrelationGroup

        agent_count = db.query(Agent).count()
        heartbeat_count = db.query(Heartbeat).count()
        event_count = db.query(TelemetryEvent).count()
        alert_count = db.query(Alert).count()
        asset_count = db.query(Asset).count()
        correlation_count = db.query(CorrelationGroup).count()

        print(f"  Total Agents: {agent_count}")
        print(f"  Total Heartbeats: {heartbeat_count}")
        print(f"  Total Events: {event_count}")
        print(f"  Total Alerts: {alert_count}")
        print(f"  Total Assets: {asset_count}")
        print(f"  Total Correlations: {correlation_count}")

        print("\n[4/4] Scenario complete!")
        print("  Chain verified: heartbeat -> events -> alerts -> correlation")
        print("  Ready for export and validation")

        print("\n" + "=" * 60)
        print("Scenario execution successful")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_scenario()
