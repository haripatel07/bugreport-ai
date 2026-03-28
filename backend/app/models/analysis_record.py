"""SQLAlchemy persistence models for analyzed bug records."""

from datetime import datetime

from sqlalchemy import ForeignKey, JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AnalysisRecord(Base):
    """Persisted result of one analysis/recommendation request."""

    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_type: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    environment: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    processed_input: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bug_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    root_cause_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    similar_bugs: Mapped[list | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
