"""DevinciWatch — agent de collecte côté endpoint (serveur-endpoint).

Responsabilités MVP :
- émettre un heartbeat périodique vers l'API SOC
- collecter les compteurs d'interface réseau
- détecter les connexions réseau entrantes suspectes
- envoyer les événements vers l'API SOC
"""

from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass
class AgentConfig:
    api_url: str
    sensor_id: str
    interval_seconds: int
    agent_ingest_key: str


def load_config() -> AgentConfig:
    hostname = socket.gethostname().replace(" ", "-").lower()
    return AgentConfig(
        api_url=os.getenv("DEVINCIWATCH_API_URL", "http://127.0.0.1:8000").rstrip("/"),
        sensor_id=os.getenv("DEVINCIWATCH_SENSOR_ID", f"sensor-{hostname}"),
        interval_seconds=int(os.getenv("DEVINCIWATCH_INTERVAL_SECONDS", "10")),
        agent_ingest_key=os.getenv("DEVINCIWATCH_AGENT_INGEST_KEY", "devinciwatch-agent-key-change-me"),
    )


def detect_mode() -> str:
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
        s.close()
        return "passive_full"
    except (PermissionError, OSError):
        pass
    if Path("/proc/net/dev").exists():
        return "passive_lite"
    return "fallback_active"


def list_interfaces() -> list[str]:
    base = Path("/sys/class/net")
    if not base.exists():
        return []
    return [
        p.name for p in base.iterdir()
        if p.name != "lo" and not p.name.startswith(("docker", "veth", "br-", "virbr", "tun", "tap"))
    ]


def read_interface_counters() -> dict[str, dict[str, int]]:
    proc = Path("/proc/net/dev")
    if not proc.exists():
        return {}
    counters: dict[str, dict[str, int]] = {}
    for line in proc.read_text(encoding="utf-8", errors="ignore").splitlines()[2:]:
        if ":" not in line:
            continue
        iface, data = line.split(":", 1)
        parts = data.split()
        if len(parts) >= 16:
            counters[iface.strip()] = {"rx_bytes": int(parts[0]), "tx_bytes": int(parts[8])}
    return counters


def read_tcp_connections() -> list[dict[str, Any]]:
    """Lire /proc/net/tcp pour détecter des connexions suspectes."""
    proc = Path("/proc/net/tcp")
    if not proc.exists():
        return []

    connections = []
    for line in proc.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            local_hex, remote_hex, state = parts[1], parts[2], parts[3]
            local_port = int(local_hex.split(":")[1], 16)
            remote_ip_hex, remote_port_hex = remote_hex.split(":")
            remote_port = int(remote_port_hex, 16)
            # Convertir l'IP hexadécimale (little-endian) en notation décimale
            remote_ip = ".".join(str(int(remote_ip_hex[i:i+2], 16)) for i in (6, 4, 2, 0))
            connections.append({
                "local_port": local_port,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "state": state,
            })
        except (ValueError, IndexError):
            continue
    return connections


def post_json(url: str, payload: dict[str, Any], key: str, timeout: int = 5) -> bool:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        with urlopen(req, timeout=timeout) as resp:  # nosec B310
            return 200 <= resp.status < 300
    except (URLError, Exception):
        return False


def send_heartbeat(cfg: AgentConfig, mode: str, interfaces: list[str]) -> None:
    payload = {
        "agent_id": cfg.sensor_id,
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "status": "alive",
        "mode": mode,
        "interfaces": interfaces,
        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    post_json(f"{cfg.api_url}/telemetry/heartbeat", payload, cfg.agent_ingest_key)


def send_event(cfg: AgentConfig, event_type: str, severity: str, message: str, payload: dict) -> None:
    event = {
        "agent_id": cfg.sensor_id,
        "source_ip": payload.get("source_ip", ""),
        "target_ip": socket.gethostbyname(socket.gethostname()),
        "event_type": event_type,
        "severity": severity,
        "message": message,
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "raw_payload": payload,
    }
    post_json(f"{cfg.api_url}/telemetry/events", event, cfg.agent_ingest_key)


def detect_suspicious_connections(cfg: AgentConfig, previous: list[dict]) -> list[dict]:
    """Comparer les connexions TCP actuelles avec les précédentes pour détecter des nouveautés."""
    current = read_tcp_connections()
    prev_keys = {(c["remote_ip"], c["remote_port"]) for c in previous}
    suspicious = []
    for conn in current:
        key = (conn["remote_ip"], conn["remote_port"])
        if key not in prev_keys and conn["remote_ip"] not in ("0.0.0.0", "127.0.0.1"):
            suspicious.append(conn)
            send_event(
                cfg,
                event_type="suspicious_connection",
                severity="medium",
                message=f"Nouvelle connexion entrante depuis {conn['remote_ip']}:{conn['remote_port']}",
                payload={"source_ip": conn["remote_ip"], "connection": conn},
            )
    return current


def run_loop() -> None:
    cfg = load_config()
    mode = detect_mode()
    interfaces = list_interfaces()
    previous_connections: list[dict] = []
    connection_tracker: list[dict] = []
    port_scan_window: list[float] = []
    ssh_attempt_times: list[float] = []

    print(f"[agent] démarré — sensor={cfg.sensor_id} mode={mode} api={cfg.api_url}")

    while True:
        send_heartbeat(cfg, mode, interfaces)

        counters = read_interface_counters()
        send_event(
            cfg,
            event_type="interface_counters",
            severity="info",
            message="Snapshot compteurs interfaces réseau",
            payload={"mode": mode, "interfaces": counters},
        )

        current_connections = read_tcp_connections()

        # Detect suspicious new connections
        prev_keys = {(c["remote_ip"], c["remote_port"]) for c in connection_tracker}
        for conn in current_connections:
            key = (conn["remote_ip"], conn["remote_port"])
            if key not in prev_keys and conn["remote_ip"] not in ("0.0.0.0", "127.0.0.1"):
                send_event(
                    cfg,
                    event_type="suspicious_connection",
                    severity="high",
                    message=f"Nouvelle connexion entrante depuis {conn['remote_ip']}:{conn['remote_port']}",
                    payload={"source_ip": conn["remote_ip"], "connection": conn},
                )
                connection_tracker.append(conn)

        # Detect port scans (multiple ports in short window)
        now = time.time()
        port_scan_window = [t for t in port_scan_window if now - t < 30]
        ssh_attempt_times = [t for t in ssh_attempt_times if now - t < 60]

        # Track connection attempts to different ports
        active_ports = {(c["remote_ip"], c["remote_port"]) for c in current_connections}
        if len(active_ports) > 5:
            send_event(
                cfg,
                event_type="network_scan",
                severity="high",
                message=f"Scan détecté: {len(active_ports)} ports actifs",
                payload={"source_ip": "external", "active_ports": len(active_ports), "ports": [c["remote_port"] for c in current_connections[:20]]},
            )

        # Detect SSH brute force (many connection attempts to port 22)
        ssh_attempts = [c for c in current_connections if c.get("local_port") == 22 or c.get("remote_port") == 22]
        if len(ssh_attempts) >= 3:
            for _ in range(min(3, len(ssh_attempts) - len(ssh_attempt_times))):
                ssh_attempt_times.append(now)
            send_event(
                cfg,
                event_type="brute_force",
                severity="critical",
                message=f"Tentatives SSH brute force détectées ({len(ssh_attempts)} connexions)",
                payload={"source_ip": "external", "attempts": len(ssh_attempts), "port": 22},
            )

        # Detect traffic burst (high volume of connections)
        if len(current_connections) > 15:
            send_event(
                cfg,
                event_type="traffic_burst",
                severity="high",
                message=f"Rafale de connexions détectée ({len(current_connections)} connexions)",
                payload={"source_ip": "external", "connection_count": len(current_connections)},
            )

        previous_connections = current_connections
        time.sleep(cfg.interval_seconds)


if __name__ == "__main__":
    run_loop()
