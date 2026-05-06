from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.ml.service import anomaly_detector
from app.telemetry.models import TelemetryEvent

router = APIRouter()


@router.post("/ml-detect", summary="Detect anomalies using ML")
def detect_anomalies(
    events: list[dict] | None = None,
    use_database: bool = True,
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if events is None and use_database:
        db_events = (
            db.query(TelemetryEvent)
            .order_by(TelemetryEvent.observed_at.desc())
            .limit(limit)
            .all()
        )
        events = [
            {
                "source_ip": e.source_ip,
                "target_ip": e.target_ip,
                "event_type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "observed_at": e.observed_at.isoformat() if e.observed_at else "",
            }
            for e in db_events
        ]

    if not events:
        return {"results": [], "summary": {"total": 0, "anomalies": 0, "anomaly_rate": 0.0, "avg_score": 0.0}}

    anomaly_detector.fit(events)
    results = anomaly_detector.predict(events)
    summary = anomaly_detector.get_anomaly_summary(events)

    output = []
    for r in results:
        evt = r["event"]
        output.append({
            "source_ip": evt.get("source_ip"),
            "target_ip": evt.get("target_ip"),
            "event_type": evt.get("event_type"),
            "severity": evt.get("severity"),
            "message": evt.get("message"),
            "observed_at": evt.get("observed_at"),
            "anomaly_score": r["anomaly_score"],
            "is_anomaly": r["is_anomaly"],
        })

    return {"results": output, "summary": summary}
