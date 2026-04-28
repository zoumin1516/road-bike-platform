from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CrawlerJob(Base):
    __tablename__ = "crawler_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_site_id: Mapped[int] = mapped_column(ForeignKey("source_sites.id"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CrawlerSnapshot(Base):
    __tablename__ = "crawler_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_site_id: Mapped[int] = mapped_column(ForeignKey("source_sites.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_html_path: Mapped[str | None] = mapped_column(String(1024))
    raw_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("source_site_id", "url", "content_hash", name="uq_snapshot_hash"),)


class SourceProductMapping(Base):
    __tablename__ = "source_product_mappings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    source_site_id: Mapped[int] = mapped_column(ForeignKey("source_sites.id"), nullable=False)
    source_product_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    bike_model_id: Mapped[int | None] = mapped_column(ForeignKey("bike_models.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("bike_variants.id"))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_site_id", "source_product_id", name="uq_source_product_site_product"
        ),
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("bike_variants.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
