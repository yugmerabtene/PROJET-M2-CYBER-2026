from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.deps import get_current_user
from app.core.database import SessionLocal
from app.alerts.models import AuditLog

router = APIRouter()


class AuditLogSchema(BaseModel):
    id: int
    action: str
    actor: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/logs", response_model=list[AuditLogSchema])
def get_audit_logs(
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get audit log entries."""
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs
    finally:
        db.close()


@router.get("/logs/{log_id}", response_model=AuditLogSchema)
def get_audit_log(
    log_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific audit log entry."""
    db = SessionLocal()
    try:
        log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Audit log not found")
        return log
    finally:
        db.close()
