from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, JSON, Integer, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.correlation.association import AlertCorrelationAssociation


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

    # NOUVEAUX CHAMPS
    correlation_score: Mapped[float] = mapped_column(default=0.0, nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    ip_cidr: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    attack_chain_type: Mapped[str] = mapped_column(String(64), nullable=True)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)

    events: Mapped[list["CorrelatedEvent"]] = relationship(back_populates="group", lazy="selectin", cascade="all, delete-orphan")
    
    # Many-to-many with Alert - use string reference to avoid circular import
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="correlation_groups",
        secondary=AlertCorrelationAssociation.__tablename__
    )


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

    # NOUVEAUX CHAMPS
    sequence_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ml_anomaly_score: Mapped[float] = mapped_column(default=0.0, nullable=False)

    group: Mapped["CorrelationGroup"] = relationship(back_populates="events")
