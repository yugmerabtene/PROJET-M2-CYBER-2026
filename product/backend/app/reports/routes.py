from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from urllib.request import urlopen
import json
import os
from pathlib import Path
import redis

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.reports.schemas import DashboardSummary, AssetBreakdown, AlertBreakdown, EventBreakdown, ExportResponse
from app.reports.service import (
    get_dashboard_summary,
    get_alert_breakdown,
    get_event_breakdown,
    get_asset_breakdown,
    export_alerts_csv,
    export_events_csv,
    export_assets_csv,
    export_correlations_csv,
    export_json,
    export_pdf,
)

router = APIRouter()


def fetch_internal_health(url: str) -> dict:
    try:
        with urlopen(url, timeout=2) as resp:  # nosec B310
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


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


def local_system_metrics() -> dict:
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


@router.get("/dashboard", response_model=DashboardSummary, summary="Synthese du dashboard SOC")
def dashboard_summary(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_dashboard_summary(db)


@router.get("/dashboard/alerts", response_model=AlertBreakdown, summary="Repartition des alertes")
def alert_breakdown(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_alert_breakdown(db)


@router.get("/dashboard/events", response_model=EventBreakdown, summary="Repartition des evenements")
def event_breakdown(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_event_breakdown(db)


@router.get("/dashboard/assets", response_model=AssetBreakdown, summary="Repartition des actifs")
def asset_breakdown(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return get_asset_breakdown(db)


@router.get("/docker-health", summary="Etat logique des services Docker")
def docker_health(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    services = []

    postgres_status = "ok"
    postgres_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        postgres_status = "error"
        postgres_error = str(exc)
    services.append({
        "name": "postgres",
        "status": postgres_status,
        "metrics": {"query": "SELECT 1"},
        "error": postgres_error,
    })

    redis_status = "ok"
    redis_error = None
    redis_metrics = {}
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        pong = client.ping()
        info = client.info(section="server")
        redis_metrics = {
            "ping": pong,
            "redis_version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
        }
    except Exception as exc:
        redis_status = "error"
        redis_error = str(exc)
    services.append({
        "name": "redis",
        "status": redis_status,
        "metrics": redis_metrics,
        "error": redis_error,
    })

    endpoint = fetch_internal_health("http://serveur-endpoint:9101/health")
    services.append({
        "name": "serveur-endpoint",
        "status": endpoint.get("status", "error"),
        "metrics": endpoint.get("metrics", {}),
        "error": endpoint.get("error"),
    })

    attacker = fetch_internal_health("http://serveur-attacker:9102/health")
    services.append({
        "name": "serveur-attacker",
        "status": attacker.get("status", "error"),
        "metrics": attacker.get("metrics", {}),
        "error": attacker.get("error"),
    })

    dashboard = get_dashboard_summary(db)
    services.append({
        "name": "serveur-soc",
        "status": "ok",
        "metrics": {
            "total_events": dashboard.get("total_events", 0),
            "active_alerts": dashboard.get("active_alerts", 0),
            "total_assets": dashboard.get("total_assets", 0),
            "total_agents": dashboard.get("total_agents", 0),
            "total_correlations": dashboard.get("total_correlations", 0),
            **local_system_metrics(),
        },
        "error": None,
    })

    overall = "ok" if all(service["status"] == "ok" for service in services) else "degraded"
    return {"status": overall, "services": services}


@router.get("/export/alerts/csv", summary="Export alertes en CSV")
def export_alerts_to_csv(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    csv_data = export_alerts_csv(db)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=alerts.csv"})


@router.get("/export/events/csv", summary="Export evenements en CSV")
def export_events_to_csv(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    csv_data = export_events_csv(db)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=events.csv"})


@router.get("/export/assets/csv", summary="Export actifs en CSV")
def export_assets_to_csv(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    csv_data = export_assets_csv(db)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=assets.csv"})


@router.get("/export/correlations/csv", summary="Export correlations en CSV")
def export_correlations_to_csv(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    csv_data = export_correlations_csv(db)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=correlations.csv"})


@router.get("/export/{resource}/json", summary="Export en JSON")
def export_to_json(
    resource: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if resource not in ("alerts", "events", "assets", "correlations"):
        raise HTTPException(status_code=400, detail=f"Resource '{resource}' non exportable en JSON")
    return export_json(db, resource)


@router.get("/export/{resource}/pdf", summary="Export en PDF")
def export_to_pdf(
    resource: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if resource not in ("alerts", "events", "assets", "correlations"):
        raise HTTPException(status_code=400, detail=f"Resource '{resource}' non exportable en PDF")
    pdf_data = export_pdf(db, resource)
    return Response(content=pdf_data, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={resource}.pdf"})
