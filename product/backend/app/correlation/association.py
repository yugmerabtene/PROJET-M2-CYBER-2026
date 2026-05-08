from datetime import datetime, timezone

from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AlertCorrelationAssociation(Base):
    __tablename__ = "alert_correlation_assoc"

    alert_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alerts.id"), primary_key=True
    )
    correlation_group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("correlation_groups.id"), primary_key=True
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
