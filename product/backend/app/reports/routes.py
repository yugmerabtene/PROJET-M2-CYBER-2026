from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.reports.schemas import DashboardSummary, AssetBreakdown, AlertBreakdown, EventBreakdown, ExportResponse
from app.reports.service import (
    get_dashboard_summary,
    get_alert_breakdown,
    get_event_breakdown,
    get_asset_breakdown,
    export_alerts_csv,
    export_events_csv,
    export_assets_csv,
    export_json,
)

router = APIRouter()


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


@router.get("/export/{resource}/json", summary="Export en JSON")
def export_to_json(
    resource: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if resource not in ("alerts", "events"):
        raise HTTPException(status_code=400, detail=f"Resource '{resource}' non exportable en JSON")
    return export_json(db, resource)
