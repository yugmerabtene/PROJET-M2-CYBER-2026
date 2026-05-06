"""DevinciWatch — Real-time updates via Server-Sent Events (SSE)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


class ConnectionManager:
    """Manages SSE client connections and broadcasts."""

    def __init__(self) -> None:
        self.active_queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.active_queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self.active_queues:
            self.active_queues.remove(q)

    async def broadcast(self, event_type: str, data: dict) -> None:
        payload = json.dumps({"type": event_type, "data": data, "ts": datetime.now(timezone.utc).isoformat()})
        for q in list(self.active_queues):
            try:
                await q.put(payload)
            except Exception:
                pass


manager = ConnectionManager()


def notify(event_type: str, data: dict) -> None:
    """Synchronous helper to schedule async broadcast."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(manager.broadcast(event_type, data))
        else:
            asyncio.run(manager.broadcast(event_type, data))
    except Exception:
        pass


def send_dashboard_update() -> None:
    """Trigger a dashboard data refresh for all SSE clients."""
    from app.core.database import SessionLocal
    from app.telemetry.service import get_agents, get_events
    from app.alerts.service import get_alerts
    from app.correlation.service import get_correlation_summary

    db = SessionLocal()
    try:
        events = get_events(db, limit=1000)
        alerts = get_alerts(db, limit=1000)
        agents = get_agents(db)

        active_alerts = [a for a in alerts if a.status in ("new", "acknowledged", "investigating")]
        critical = sum(1 for a in active_alerts if a.severity == "critical")
        high = sum(1 for a in active_alerts if a.severity == "high")

        corr_summary = get_correlation_summary(db)

        data = {
            "total_events": len(events),
            "total_alerts": len(active_alerts),
            "total_assets": 0,
            "total_agents": len([a for a in agents if a.is_active]),
            "total_correlations": corr_summary.get("active_groups", 0),
            "critical_alerts": critical,
            "high_alerts": high,
            "alerts": [
                {
                    "id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "status": a.status,
                    "source_ip": a.source_ip,
                    "target_ip": a.target_ip,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in alerts[-10:]
            ],
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "source_ip": e.source_ip,
                    "target_ip": e.target_ip,
                    "message": e.message,
                    "observed_at": e.observed_at.isoformat() if e.observed_at else None,
                }
                for e in events[-10:]
            ],
        }

        # Get assets count
        from app.assets.service import get_assets
        assets = get_assets(db, active_only=True)
        data["total_assets"] = len(assets)

        notify("dashboard", data)
    except Exception:
        pass
    finally:
        db.close()


@router.get("/events/stream")
async def sse_stream():
    """Server-Sent Events endpoint for real-time dashboard updates."""

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = manager.subscribe()
        try:
            # Send initial data
            send_dashboard_update()
            await asyncio.sleep(0.1)

            # Stream events
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
