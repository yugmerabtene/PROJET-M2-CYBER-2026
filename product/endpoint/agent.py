"""DevinciWatch endpoint agent with realistic honeypot services.

This endpoint does two things:
- exposes real lab services (HTTP, fake SSH, fake TLS banner) that can be scanned/attacked
- observes these interactions and forwards telemetry events to the SOC API
"""

from __future__ import annotations

import json
import os
import queue
import socket
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


HONEYPOT_PORTS = {
    22: {"service": "ssh", "banner": b"SSH-2.0-OpenSSH_8.9p1 Debian-3\r\n"},
    443: {"service": "tls", "banner": b"HTTP/1.1 400 Bad Request\r\nServer: nginx\r\n\r\n"},
    8080: {"service": "http-alt", "banner": b""},
    8443: {"service": "tls-alt", "banner": b"HTTP/1.1 400 Bad Request\r\nServer: nginx\r\n\r\n"},
}
HTTP_PORTS = (80, 8080)


@dataclass
class AgentConfig:
    api_url: str
    sensor_id: str
    interval_seconds: int
    agent_ingest_key: str


event_queue: queue.Queue[dict[str, Any]] = queue.Queue()
metrics_lock = threading.Lock()
runtime_metrics: dict[str, Any] = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "heartbeat_sent": 0,
    "events_sent": 0,
    "connections_seen": 0,
    "login_attempts": 0,
    "network_scans_detected": 0,
    "traffic_bursts_detected": 0,
    "last_event_type": None,
    "last_interaction_at": None,
    "honeypot_ports": [22, 80, 443, 8080, 8443],
}


def read_meminfo() -> dict[str, int]:
    meminfo: dict[str, int] = {}
    proc = Path("/proc/meminfo")
    if not proc.exists():
        return meminfo
    for line in proc.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        try:
            meminfo[key.strip()] = int(value.strip().split()[0])
        except (ValueError, IndexError):
            continue
    return meminfo


def read_system_metrics() -> dict[str, Any]:
    meminfo = read_meminfo()
    mem_total_kb = meminfo.get("MemTotal", 0)
    mem_available_kb = meminfo.get("MemAvailable", 0)
    mem_used_kb = max(mem_total_kb - mem_available_kb, 0)
    mem_percent = round((mem_used_kb / mem_total_kb) * 100, 2) if mem_total_kb else 0
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1, load5, load15 = 0.0, 0.0, 0.0
    return {
        "cpu_count": os.cpu_count() or 0,
        "load_1m": round(load1, 2),
        "load_5m": round(load5, 2),
        "load_15m": round(load15, 2),
        "mem_total_mb": round(mem_total_kb / 1024, 2),
        "mem_used_mb": round(mem_used_kb / 1024, 2),
        "mem_available_mb": round(mem_available_kb / 1024, 2),
        "mem_used_percent": mem_percent,
    }


def bump_metric(name: str, amount: int = 1) -> None:
    with metrics_lock:
        runtime_metrics[name] = int(runtime_metrics.get(name, 0) or 0) + amount


def set_metric(name: str, value: Any) -> None:
    with metrics_lock:
        runtime_metrics[name] = value


def snapshot_metrics() -> dict[str, Any]:
    with metrics_lock:
        snapshot = dict(runtime_metrics)
    snapshot["system"] = read_system_metrics()
    return snapshot


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
    bump_metric("heartbeat_sent")


def send_event(cfg: AgentConfig, event_type: str, severity: str, message: str, payload: dict[str, Any]) -> None:
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
    bump_metric("events_sent")
    set_metric("last_event_type", event_type)


def enqueue_interaction(kind: str, remote_ip: str, remote_port: int, local_port: int, extra: dict[str, Any] | None = None) -> None:
    bump_metric("connections_seen")
    set_metric("last_interaction_at", datetime.now(timezone.utc).isoformat())
    event_queue.put(
        {
            "kind": kind,
            "remote_ip": remote_ip,
            "remote_port": remote_port,
            "local_port": local_port,
            "ts": time.time(),
            **(extra or {}),
        }
    )


class LabHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "DevinciWatchLab/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _record(self, method: str) -> None:
        enqueue_interaction(
            "http",
            self.client_address[0],
            self.client_address[1],
            self.server.server_port,
            {
                "method": method,
                "path": self.path,
                "user_agent": self.headers.get("User-Agent", ""),
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        self._record("GET")
        parsed = urlparse(self.path)
        pages = {
            "/": "<html><body><h1>DevinciWatch Lab</h1><a href='/login'>login</a><a href='/admin'>admin</a></body></html>",
            "/login": "<html><body><form method='post' action='/login'><input name='username'><input name='password' type='password'><button>Login</button></form></body></html>",
            "/admin": "<html><body><h1>Admin Panel</h1><p>Restricted</p></body></html>",
            "/health": "ok",
        }
        body = pages.get(parsed.path, "<html><body><h1>404</h1></body></html>")
        status = 200 if parsed.path in pages else 404
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Server", "nginx/1.24")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_HEAD(self) -> None:  # noqa: N802
        self._record("HEAD")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Server", "nginx/1.24")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="ignore") if length > 0 else ""
        params = parse_qs(body)
        self._record("POST")

        if self.path == "/login":
            username = params.get("username", [""])[0]
            enqueue_interaction(
                "login_attempt",
                self.client_address[0],
                self.client_address[1],
                self.server.server_port,
                {
                    "username": username,
                    "path": self.path,
                    "user_agent": self.headers.get("User-Agent", ""),
                },
            )
            self.send_response(401)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Invalid credentials")
            return

        self.send_response(404)
        self.end_headers()


class MetricsHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "DevinciWatchMetrics/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps(
            {
                "status": "ok",
                "service": "serveur-endpoint",
                "metrics": snapshot_metrics(),
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_http_service(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), LabHTTPRequestHandler)
    server.serve_forever()


def run_tcp_banner_service(port: int, banner: bytes) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(64)
    while True:
        conn, addr = sock.accept()
        remote_ip, remote_port = addr[0], addr[1]
        enqueue_interaction("tcp", remote_ip, remote_port, port, {})
        conn.settimeout(1.0)
        try:
            if banner:
                conn.sendall(banner)
            try:
                sample = conn.recv(256)
            except socket.timeout:
                sample = b""
            if port == 22 and sample:
                enqueue_interaction("ssh_attempt", remote_ip, remote_port, port, {"sample": sample.decode("utf-8", errors="ignore")[:120]})
        except OSError:
            pass
        finally:
            conn.close()


def start_lab_services() -> None:
    for port in HTTP_PORTS:
        t = threading.Thread(target=run_http_service, args=(port,), daemon=True)
        t.start()
    for port, config in HONEYPOT_PORTS.items():
        if port in HTTP_PORTS:
            continue
        t = threading.Thread(target=run_tcp_banner_service, args=(port, config["banner"]), daemon=True)
        t.start()
    metrics_server = ThreadingHTTPServer(("0.0.0.0", 9101), MetricsHTTPRequestHandler)
    threading.Thread(target=metrics_server.serve_forever, daemon=True).start()


def flush_interactions(cfg: AgentConfig, recent: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = time.time()
    recent = [item for item in recent if now - item["ts"] < 120]

    while True:
        try:
            interaction = event_queue.get_nowait()
        except queue.Empty:
            break
        recent.append(interaction)

        src = interaction["remote_ip"]
        port = interaction["local_port"]
        ua = interaction.get("user_agent", "")
        path = interaction.get("path", "")

        if interaction["kind"] in {"http", "tcp"}:
            send_event(
                cfg,
                event_type="suspicious_connection",
                severity="medium",
                message=f"Connexion observée sur le service {port} depuis {src}",
                payload={"source_ip": src, "connection": interaction},
            )

        if interaction["kind"] == "login_attempt":
            bump_metric("login_attempts")
            send_event(
                cfg,
                event_type="brute_force",
                severity="critical",
                message=f"Tentative d'authentification détectée sur /login depuis {src}",
                payload={"source_ip": src, "connection": interaction},
            )

        if any(tool in ua.lower() for tool in ("nikto", "ffuf", "httpx", "sqlmap")) or path not in {"", "/", "/health", "/login", "/admin"}:
            bump_metric("network_scans_detected")
            send_event(
                cfg,
                event_type="network_scan",
                severity="high",
                message=f"Énumération web détectée depuis {src} vers {path or '/'}",
                payload={"source_ip": src, "connection": interaction},
            )

    by_ip: dict[str, set[int]] = {}
    ssh_by_ip: dict[str, int] = {}
    for item in recent:
        src = item["remote_ip"]
        by_ip.setdefault(src, set()).add(item["local_port"])
        if item["local_port"] == 22:
            ssh_by_ip[src] = ssh_by_ip.get(src, 0) + 1

    for src, ports in by_ip.items():
        if len(ports) >= 3:
            bump_metric("network_scans_detected")
            send_event(
                cfg,
                event_type="network_scan",
                severity="high",
                message=f"Scan multi-ports détecté depuis {src} ({len(ports)} ports)",
                payload={"source_ip": src, "ports": sorted(ports)},
            )

    for src, attempts in ssh_by_ip.items():
        if attempts >= 3:
            send_event(
                cfg,
                event_type="brute_force",
                severity="critical",
                message=f"Multiples tentatives SSH détectées depuis {src} ({attempts} connexions)",
                payload={"source_ip": src, "attempts": attempts, "port": 22},
            )

    if len(recent) >= 20:
        top_src = recent[-1]["remote_ip"]
        bump_metric("traffic_bursts_detected")
        send_event(
            cfg,
            event_type="traffic_burst",
            severity="high",
            message=f"Rafale de connexions détectée ({len(recent)} interactions récentes)",
            payload={"source_ip": top_src, "connection_count": len(recent)},
        )

    return recent


def run_loop() -> None:
    cfg = load_config()
    mode = detect_mode()
    interfaces = list_interfaces()
    recent_interactions: list[dict[str, Any]] = []

    start_lab_services()
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
        recent_interactions = flush_interactions(cfg, recent_interactions)
        time.sleep(cfg.interval_seconds)


if __name__ == "__main__":
    run_loop()
