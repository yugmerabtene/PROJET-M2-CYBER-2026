import ipaddress
import socket
from datetime import datetime, timezone

from pydantic import BaseModel


class DiscoveryResult(BaseModel):
    ip_address: str
    is_alive: bool
    open_ports: list[int]
    services: dict[int, str]
    hostname: str | None
    discovered_at: str


def ping_host(ip: str, timeout: float = 1.0) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, 80))
        sock.close()
        return result == 0
    except (socket.error, OSError):
        return False


def scan_ports(ip: str, ports: list[int], timeout: float = 0.5) -> list[int]:
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
        except (socket.error, OSError):
            continue
    return open_ports


def guess_service(port: int) -> str:
    services = {
        21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
        80: "http", 110: "pop3", 143: "imap", 443: "https", 993: "imaps",
        995: "pop3s", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
        5900: "vnc", 6379: "redis", 8080: "http-alt", 8443: "https-alt",
        9200: "elasticsearch", 27017: "mongodb",
    }
    return services.get(port, f"unknown-{port}")


def discover_single_host(ip: str, ports: list[int] | None = None) -> DiscoveryResult:
    if ports is None:
        ports = [22, 80, 443, 3306, 5432, 8080]

    is_alive = ping_host(ip)
    open_ports = scan_ports(ip, ports) if is_alive else []
    services = {p: guess_service(p) for p in open_ports}

    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        hostname = None

    return DiscoveryResult(
        ip_address=ip,
        is_alive=is_alive,
        open_ports=open_ports,
        services=services,
        hostname=hostname,
        discovered_at=datetime.now(timezone.utc).isoformat(),
    )


def discover_network_range(ip_range: str, ports: list[int] | None = None) -> list[DiscoveryResult]:
    try:
        network = ipaddress.ip_network(ip_range, strict=False)
    except ValueError:
        return []

    if ports is None:
        ports = [22, 80, 443]

    results = []
    for ip in network.hosts():
        result = discover_single_host(str(ip), ports)
        results.append(result)

    return results
