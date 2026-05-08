from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, JSON, Integer, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.correlation.association import AlertCorrelationAssociation

# Table d'association many-to-many
alert_correlation_assoc = Table(
    "alert_correlation_assoc",
    Base.metadata,
    Column("alert_id", Integer, ForeignKey("alerts.id"), primary_key=True),
    Column("correlation_group_id", Integer, ForeignKey("correlation_groups.id"), primary_key=True),
    Column("linked_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="new", index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    target_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relation many-to-many avec CorrelationGroup
    correlation_groups: Mapped[list["CorrelationGroup"]] = relationship(
        "CorrelationGroup",
        back_populates="alerts",
        secondary=alert_correlation_assoc
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="alert_rel", lazy="selectin")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    alert: Mapped[int | None] = mapped_column(Integer, ForeignKey("alerts.id"), nullable=True)
    alert_rel: Mapped["Alert | None"] = relationship(back_populates="audit_logs")
