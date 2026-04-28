"""Initial road bike platform schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("country", sa.String(64)),
        sa.Column("official_site_url", sa.String(512)),
        sa.Column("logo_url", sa.String(512)),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        *timestamps(),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "source_sites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.BigInteger(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("site_name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(512), nullable=False),
        sa.Column("region", sa.String(64)),
        sa.Column("language", sa.String(32)),
        sa.Column("currency", sa.String(16)),
        sa.Column("scrape_strategy", sa.String(32), nullable=False, server_default="hybrid"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        *timestamps(),
        sa.UniqueConstraint("brand_id", "base_url", name="uq_source_sites_brand_base_url"),
    )

    op.create_table(
        "source_pages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_site_id", sa.BigInteger(), sa.ForeignKey("source_sites.id"), nullable=False),
        sa.Column("page_type", sa.String(32), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        *timestamps(),
    )

    op.create_table(
        "bike_series",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.BigInteger(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("description", sa.Text()),
        sa.Column("source_url", sa.String(1024)),
        *timestamps(),
        sa.UniqueConstraint("brand_id", "slug", name="uq_bike_series_brand_slug"),
    )

    op.create_table(
        "bike_models",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.BigInteger(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("series_id", sa.BigInteger(), sa.ForeignKey("bike_series.id")),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False),
        sa.Column("model_year", sa.Integer()),
        sa.Column("category", sa.String(64)),
        sa.Column("usage_type", sa.String(64)),
        sa.Column("frame_material", sa.String(64)),
        sa.Column("brake_type", sa.String(64)),
        sa.Column("drivetrain_brand", sa.String(64)),
        sa.Column("groupset", sa.String(128)),
        sa.Column("speed_count", sa.Integer()),
        sa.Column("wheel_size", sa.String(64)),
        sa.Column("weight_kg", sa.Numeric(6, 3)),
        sa.Column("price_min", sa.Numeric(12, 2)),
        sa.Column("price_max", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(16)),
        sa.Column("official_url", sa.String(1024)),
        sa.Column("description", sa.Text()),
        sa.Column("raw_summary", postgresql.JSONB()),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        *timestamps(),
        sa.UniqueConstraint("brand_id", "slug", "model_year", name="uq_bike_models_brand_slug_year"),
    )
    op.create_index(
        "idx_bike_models_filters",
        "bike_models",
        ["brand_id", "category", "usage_type", "model_year"],
    )

    op.create_table(
        "bike_variants",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("sku", sa.String(128)),
        sa.Column("color_name", sa.String(128)),
        sa.Column("color_hex", sa.String(32)),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(16)),
        sa.Column("size_options", postgresql.JSONB()),
        sa.Column("availability", sa.String(64)),
        sa.Column("official_url", sa.String(1024)),
        sa.Column("raw_data", postgresql.JSONB()),
        *timestamps(),
        sa.UniqueConstraint("bike_model_id", "sku", "color_name", name="uq_variants_sku_color"),
    )

    op.create_table(
        "bike_images",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("variant_id", sa.BigInteger(), sa.ForeignKey("bike_variants.id")),
        sa.Column("image_url", sa.String(1024), nullable=False),
        sa.Column("image_type", sa.String(32), nullable=False, server_default="gallery"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alt_text", sa.String(256)),
        sa.Column("source_url", sa.String(1024)),
        *timestamps(),
        sa.UniqueConstraint("bike_model_id", "image_url", name="uq_bike_images_model_url"),
    )

    op.create_table(
        "component_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
    )

    op.create_table(
        "bike_components",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("variant_id", sa.BigInteger(), sa.ForeignKey("bike_variants.id")),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("component_categories.id")),
        sa.Column("component_name", sa.String(128), nullable=False),
        sa.Column("component_value", sa.Text(), nullable=False),
        sa.Column("brand", sa.String(128)),
        sa.Column("normalized_value", sa.Text()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *timestamps(),
        sa.UniqueConstraint(
            "bike_model_id",
            "variant_id",
            "category_id",
            "component_name",
            name="uq_bike_components_identity",
        ),
    )

    op.create_table(
        "bike_geometry_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("variant_id", sa.BigInteger(), sa.ForeignKey("bike_variants.id")),
        sa.Column("geometry_image_url", sa.String(1024)),
        sa.Column("raw_data", postgresql.JSONB()),
        *timestamps(),
        sa.UniqueConstraint("bike_model_id", "variant_id", name="uq_geometry_profiles_model_variant"),
    )

    op.create_table(
        "bike_geometry_values",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "geometry_profile_id",
            sa.BigInteger(),
            sa.ForeignKey("bike_geometry_profiles.id"),
            nullable=False,
        ),
        sa.Column("size_label", sa.String(64), nullable=False),
        sa.Column("metric_name", sa.String(128), nullable=False),
        sa.Column("metric_label", sa.String(128), nullable=False),
        sa.Column("value", sa.String(128)),
        sa.Column("unit", sa.String(32)),
        *timestamps(),
        sa.UniqueConstraint(
            "geometry_profile_id",
            "size_label",
            "metric_name",
            name="uq_geometry_values_profile_size_metric",
        ),
    )

    op.create_table(
        "bike_size_recommendations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("size_label", sa.String(64), nullable=False),
        sa.Column("min_height_cm", sa.Integer()),
        sa.Column("max_height_cm", sa.Integer()),
        sa.Column("raw_data", postgresql.JSONB()),
        *timestamps(),
        sa.UniqueConstraint("bike_model_id", "size_label", name="uq_size_recommendations_model_size"),
    )

    op.create_table(
        "crawler_jobs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_site_id", sa.BigInteger(), sa.ForeignKey("source_sites.id"), nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("stats", postgresql.JSONB()),
        *timestamps(),
    )

    op.create_table(
        "crawler_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_site_id", sa.BigInteger(), sa.ForeignKey("source_sites.id"), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("raw_html_path", sa.String(1024)),
        sa.Column("raw_json", postgresql.JSONB()),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_site_id", "url", "content_hash", name="uq_snapshot_hash"),
    )

    op.create_table(
        "source_product_mappings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.BigInteger(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("source_site_id", sa.BigInteger(), sa.ForeignKey("source_sites.id"), nullable=False),
        sa.Column("source_product_id", sa.String(128), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id")),
        sa.Column("variant_id", sa.BigInteger(), sa.ForeignKey("bike_variants.id")),
        sa.Column("raw_data", postgresql.JSONB()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "source_site_id", "source_product_id", name="uq_source_product_site_product"
        ),
    )

    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("bike_model_id", sa.BigInteger(), sa.ForeignKey("bike_models.id"), nullable=False),
        sa.Column("variant_id", sa.BigInteger(), sa.ForeignKey("bike_variants.id")),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table_name in [
        "price_history",
        "source_product_mappings",
        "crawler_snapshots",
        "crawler_jobs",
        "bike_size_recommendations",
        "bike_geometry_values",
        "bike_geometry_profiles",
        "bike_components",
        "component_categories",
        "bike_images",
        "bike_variants",
        "bike_models",
        "bike_series",
        "source_pages",
        "source_sites",
        "brands",
    ]:
        op.drop_table(table_name)
