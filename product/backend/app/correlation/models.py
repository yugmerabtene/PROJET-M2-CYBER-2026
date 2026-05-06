from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, JSON, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CorrelationGroup(Base):
    __tablename__ = "correlation_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alert_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    events: Mapped[list["CorrelatedEvent"]] = relationship(back_populates="group", lazy="selectin", cascade="all, delete-orphan")


class CorrelatedEvent(Base):
    __tablename__ = "correlated_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("correlation_groups.id"), nullable=False, index=True)
    telemetry_event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    group: Mapped["CorrelationGroup"] = relationship(back_populates="events")
