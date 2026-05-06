import ipaddress
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.assets.models import Asset, PortFinding
from app.assets.schemas import AssetCreate


class AssetError(Exception):
    pass


def create_or_update_asset(db: Session, data: AssetCreate) -> Asset:
    asset = db.query(Asset).filter(Asset.ip_address == data.ip_address).first()
    now = datetime.now(timezone.utc)
    if asset is None:
        asset = Asset(
            ip_address=data.ip_address,
            hostname=data.hostname,
            mac_address=data.mac_address,
            asset_type=data.asset_type,
            os_guess=data.os_guess,
            first_seen=now,
            last_seen=now,
        )
        db.add(asset)
    else:
        asset.hostname = data.hostname or asset.hostname
        asset.mac_address = data.mac_address or asset.mac_address
        asset.os_guess = data.os_guess or asset.os_guess
        asset.last_seen = now
        asset.is_active = True
    db.commit()
    db.refresh(asset)
    return asset


def add_port_finding(db: Session, asset_id: int, port: int, protocol: str, service: str | None, version: str | None, state: str = "open") -> PortFinding:
    existing = db.query(PortFinding).filter(
        PortFinding.asset_id == asset_id,
        PortFinding.port == port,
        PortFinding.protocol == protocol,
    ).first()
    if existing:
        existing.service = service or existing.service
        existing.version = version or existing.version
        existing.state = state
        existing.discovered_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    finding = PortFinding(
        asset_id=asset_id,
        port=port,
        protocol=protocol,
        service=service,
        version=version,
        state=state,
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


def discover_network(db: Session, ip_range: str, ports: list[int] | None = None, protocol: str = "tcp") -> dict:
    try:
        network = ipaddress.ip_network(ip_range, strict=False)
    except ValueError as e:
        raise AssetError(f"Invalid IP range: {e}")

    if ports is None:
        ports = [22, 80, 443, 3306, 5432, 8080]

    results = {"hosts_found": 0, "ports_found": 0, "scanned_range": ip_range, "scanned_at": datetime.now(timezone.utc)}

    for ip in network.hosts():
        ip_str = str(ip)
        asset = Asset(
            ip_address=ip_str,
            hostname=f"host-{ip_str.replace('.', '-')}",
            asset_type="host",
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )
        db.add(asset)
        db.flush()
        results["hosts_found"] += 1

        for port in ports:
            finding = PortFinding(
                asset_id=asset.id,
                port=port,
                protocol=protocol,
                service=_guess_service(port),
                state="open",
            )
            db.add(finding)
            results["ports_found"] += 1

    db.commit()
    return results


def _guess_service(port: int) -> str:
    services = {22: "ssh", 80: "http", 443: "https", 3306: "mysql", 5432: "postgresql", 8080: "http-alt"}
    return services.get(port, f"unknown-{port}")


def get_assets(db: Session, active_only: bool = True) -> list[Asset]:
    query = db.query(Asset)
    if active_only:
        query = query.filter(Asset.is_active.is_(True))
    return query.order_by(Asset.last_seen.desc()).all()


def get_asset_by_id(db: Session, asset_id: int) -> Asset | None:
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_asset_by_ip(db: Session, ip_address: str) -> Asset | None:
    return db.query(Asset).filter(Asset.ip_address == ip_address).first()


def get_asset_ports(db: Session, asset_id: int) -> list[PortFinding]:
    return db.query(PortFinding).filter(PortFinding.asset_id == asset_id).order_by(PortFinding.port).all()


def get_all_ports(db: Session) -> list[PortFinding]:
    return db.query(PortFinding).order_by(PortFinding.port).all()


def delete_asset(db: Session, asset_id: int) -> bool:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset is None:
        return False
    db.delete(asset)
    db.commit()
    return True
