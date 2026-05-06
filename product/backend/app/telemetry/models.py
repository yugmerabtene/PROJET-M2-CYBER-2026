from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="fallback_active")
    interfaces: Mapped[list] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    heartbeats: Mapped[list["Heartbeat"]] = relationship(back_populates="agent", lazy="selectin")
    events: Mapped[list["TelemetryEvent"]] = relationship(back_populates="agent", lazy="selectin")


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="alive")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="heartbeats")


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="events")
