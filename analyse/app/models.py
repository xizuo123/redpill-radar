import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Content(Base):
    __tablename__ = "content"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    twitter_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    content_text: Mapped[str] = mapped_column(Text)

    age_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    harmful_subcategories: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    labels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_history: Mapped[list | None] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow
    )


class CategoryConfig(Base):
    __tablename__ = "category_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_group: Mapped[str] = mapped_column(String(100), index=True)
    category_value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
