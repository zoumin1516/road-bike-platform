from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Brand(TimestampMixin, Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    country: Mapped[str | None] = mapped_column(String(64))
    official_site_url: Mapped[str | None] = mapped_column(String(512))
    logo_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    source_sites: Mapped[list["SourceSite"]] = relationship(back_populates="brand")
    series: Mapped[list["BikeSeries"]] = relationship(back_populates="brand")
    models: Mapped[list["BikeModel"]] = relationship(back_populates="brand")


class SourceSite(TimestampMixin, Base):
    __tablename__ = "source_sites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    site_name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    region: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(32))
    currency: Mapped[str | None] = mapped_column(String(16))
    scrape_strategy: Mapped[str] = mapped_column(String(32), nullable=False, default="hybrid")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    brand: Mapped[Brand] = relationship(back_populates="source_sites")
    pages: Mapped[list["SourcePage"]] = relationship(back_populates="source_site")

    __table_args__ = (UniqueConstraint("brand_id", "base_url", name="uq_source_sites_brand_base_url"),)


class SourcePage(TimestampMixin, Base):
    __tablename__ = "source_pages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_site_id: Mapped[int] = mapped_column(ForeignKey("source_sites.id"), nullable=False)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    source_site: Mapped[SourceSite] = relationship(back_populates="pages")


class BikeSeries(TimestampMixin, Base):
    __tablename__ = "bike_series"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1024))

    brand: Mapped[Brand] = relationship(back_populates="series")
    models: Mapped[list["BikeModel"]] = relationship(back_populates="series")

    __table_args__ = (UniqueConstraint("brand_id", "slug", name="uq_bike_series_brand_slug"),)


class BikeModel(TimestampMixin, Base):
    __tablename__ = "bike_models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("bike_series.id"))
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False)
    model_year: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(64))
    usage_type: Mapped[str | None] = mapped_column(String(64))
    frame_material: Mapped[str | None] = mapped_column(String(64))
    brake_type: Mapped[str | None] = mapped_column(String(64))
    drivetrain_brand: Mapped[str | None] = mapped_column(String(64))
    groupset: Mapped[str | None] = mapped_column(String(128))
    speed_count: Mapped[int | None] = mapped_column(Integer)
    wheel_size: Mapped[str | None] = mapped_column(String(64))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    price_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    price_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(16))
    official_url: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    raw_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    brand: Mapped[Brand] = relationship(back_populates="models")
    series: Mapped[BikeSeries | None] = relationship(back_populates="models")
    variants: Mapped[list["BikeVariant"]] = relationship(back_populates="bike_model")
    images: Mapped[list["BikeImage"]] = relationship(back_populates="bike_model")
    components: Mapped[list["BikeComponent"]] = relationship(back_populates="bike_model")

    __table_args__ = (
        UniqueConstraint("brand_id", "slug", "model_year", name="uq_bike_models_brand_slug_year"),
        Index("idx_bike_models_filters", "brand_id", "category", "usage_type", "model_year"),
    )


class BikeVariant(TimestampMixin, Base):
    __tablename__ = "bike_variants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128))
    color_name: Mapped[str | None] = mapped_column(String(128))
    color_hex: Mapped[str | None] = mapped_column(String(32))
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(16))
    size_options: Mapped[list[Any] | None] = mapped_column(JSONB)
    availability: Mapped[str | None] = mapped_column(String(64))
    official_url: Mapped[str | None] = mapped_column(String(1024))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    bike_model: Mapped[BikeModel] = relationship(back_populates="variants")

    __table_args__ = (UniqueConstraint("bike_model_id", "sku", "color_name", name="uq_variants_sku_color"),)


class BikeImage(TimestampMixin, Base):
    __tablename__ = "bike_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("bike_variants.id"))
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_type: Mapped[str] = mapped_column(String(32), nullable=False, default="gallery")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alt_text: Mapped[str | None] = mapped_column(String(256))
    source_url: Mapped[str | None] = mapped_column(String(1024))

    bike_model: Mapped[BikeModel] = relationship(back_populates="images")

    __table_args__ = (UniqueConstraint("bike_model_id", "image_url", name="uq_bike_images_model_url"),)


class ComponentCategory(TimestampMixin, Base):
    __tablename__ = "component_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    components: Mapped[list["BikeComponent"]] = relationship(back_populates="category")


class BikeComponent(TimestampMixin, Base):
    __tablename__ = "bike_components"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("bike_variants.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("component_categories.id"))
    component_name: Mapped[str] = mapped_column(String(128), nullable=False)
    component_value: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(128))
    normalized_value: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    bike_model: Mapped[BikeModel] = relationship(back_populates="components")
    category: Mapped[ComponentCategory | None] = relationship(back_populates="components")

    __table_args__ = (
        UniqueConstraint(
            "bike_model_id",
            "variant_id",
            "category_id",
            "component_name",
            name="uq_bike_components_identity",
        ),
    )


class BikeGeometryProfile(TimestampMixin, Base):
    __tablename__ = "bike_geometry_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("bike_variants.id"))
    geometry_image_url: Mapped[str | None] = mapped_column(String(1024))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    values: Mapped[list["BikeGeometryValue"]] = relationship(back_populates="profile")

    __table_args__ = (
        UniqueConstraint("bike_model_id", "variant_id", name="uq_geometry_profiles_model_variant"),
    )


class BikeGeometryValue(TimestampMixin, Base):
    __tablename__ = "bike_geometry_values"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    geometry_profile_id: Mapped[int] = mapped_column(
        ForeignKey("bike_geometry_profiles.id"), nullable=False
    )
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_label: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str | None] = mapped_column(String(128))
    unit: Mapped[str | None] = mapped_column(String(32))

    profile: Mapped[BikeGeometryProfile] = relationship(back_populates="values")

    __table_args__ = (
        UniqueConstraint(
            "geometry_profile_id",
            "size_label",
            "metric_name",
            name="uq_geometry_values_profile_size_metric",
        ),
    )


class BikeSizeRecommendation(TimestampMixin, Base):
    __tablename__ = "bike_size_recommendations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bike_model_id: Mapped[int] = mapped_column(ForeignKey("bike_models.id"), nullable=False)
    size_label: Mapped[str] = mapped_column(String(64), nullable=False)
    min_height_cm: Mapped[int | None] = mapped_column(Integer)
    max_height_cm: Mapped[int | None] = mapped_column(Integer)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("bike_model_id", "size_label", name="uq_size_recommendations_model_size"),
    )
