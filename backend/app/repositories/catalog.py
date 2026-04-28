from __future__ import annotations

from decimal import Decimal
from typing import Any

from slugify import slugify
from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.crawlers.base import NormalizedBike
from app.models import (
    BikeComponent,
    BikeGeometryProfile,
    BikeGeometryValue,
    BikeImage,
    BikeModel,
    BikeSeries,
    BikeSizeRecommendation,
    BikeVariant,
    Brand,
    ComponentCategory,
    PriceHistory,
    SourceProductMapping,
    SourceSite,
)


def decimal_or_none(value: str | int | float | Decimal | None) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


class CatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_brands(self) -> list[Brand]:
        return list(self.db.scalars(select(Brand).order_by(Brand.name)))

    def get_brand_by_slug(self, slug: str) -> Brand | None:
        return self.db.scalar(select(Brand).where(Brand.slug == slug))

    def list_bikes(
        self,
        *,
        brand_slug: str | None = None,
        category: str | None = None,
        usage_type: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BikeModel], int]:
        stmt: Select[tuple[BikeModel]] = (
            select(BikeModel)
            .options(selectinload(BikeModel.brand), selectinload(BikeModel.images))
            .order_by(BikeModel.updated_at.desc())
        )
        count_stmt = select(func.count(BikeModel.id))
        if brand_slug:
            stmt = stmt.join(BikeModel.brand).where(Brand.slug == brand_slug)
            count_stmt = count_stmt.join(BikeModel.brand).where(Brand.slug == brand_slug)
        if category:
            stmt = stmt.where(BikeModel.category == category)
            count_stmt = count_stmt.where(BikeModel.category == category)
        if usage_type:
            stmt = stmt.where(BikeModel.usage_type == usage_type)
            count_stmt = count_stmt.where(BikeModel.usage_type == usage_type)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(BikeModel.name.ilike(like))
            count_stmt = count_stmt.where(BikeModel.name.ilike(like))
        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(stmt.limit(limit).offset(offset)))
        return items, total

    def get_bike(self, bike_id: int) -> BikeModel | None:
        return self.db.scalar(
            select(BikeModel)
            .options(
                selectinload(BikeModel.brand),
                selectinload(BikeModel.series),
                selectinload(BikeModel.variants),
                selectinload(BikeModel.images),
                selectinload(BikeModel.components).selectinload(BikeComponent.category),
            )
            .where(BikeModel.id == bike_id)
        )

    def upsert_normalized_bike(self, bike: NormalizedBike) -> BikeModel:
        brand = self._upsert_brand(bike.brand_name, bike.brand_slug, bike.source_site)
        source_site = self._upsert_source_site(brand, bike.source_site)
        series = self._upsert_series(brand, bike.series_name, bike.source_url)
        model = self._upsert_bike_model(brand, series, bike)

        self._replace_variants(model, bike)
        self._replace_images(model, bike)
        self._replace_components(model, bike)
        self._replace_geometry(model, bike)
        self._replace_size_recommendations(model, bike)
        self._upsert_source_mapping(brand, source_site, model, bike)
        self._append_price_history(model, bike)
        self.db.flush()
        return model

    def _upsert_brand(self, name: str, slug: str, source_site: dict[str, Any]) -> Brand:
        stmt = (
            insert(Brand)
            .values(
                name=name,
                slug=slug,
                country=source_site.get("country"),
                official_site_url=source_site.get("base_url"),
                status="active",
            )
            .on_conflict_do_update(
                index_elements=[Brand.slug],
                set_={"name": name, "official_site_url": source_site.get("base_url")},
            )
            .returning(Brand)
        )
        return self.db.scalar(stmt)

    def _upsert_source_site(self, brand: Brand, source_site: dict[str, Any]) -> SourceSite:
        stmt = (
            insert(SourceSite)
            .values(
                brand_id=brand.id,
                site_name=source_site["site_name"],
                base_url=source_site["base_url"],
                region=source_site.get("region"),
                language=source_site.get("language"),
                currency=source_site.get("currency"),
                scrape_strategy=source_site.get("scrape_strategy", "hybrid"),
                status="active",
            )
            .on_conflict_do_update(
                constraint="uq_source_sites_brand_base_url",
                set_={
                    "site_name": source_site["site_name"],
                    "region": source_site.get("region"),
                    "language": source_site.get("language"),
                    "currency": source_site.get("currency"),
                },
            )
            .returning(SourceSite)
        )
        return self.db.scalar(stmt)

    def _upsert_series(self, brand: Brand, series_name: str | None, source_url: str) -> BikeSeries | None:
        if not series_name:
            return None
        series_slug = slugify(series_name)
        stmt = (
            insert(BikeSeries)
            .values(brand_id=brand.id, name=series_name, slug=series_slug, source_url=source_url)
            .on_conflict_do_update(
                constraint="uq_bike_series_brand_slug",
                set_={"name": series_name, "source_url": source_url},
            )
            .returning(BikeSeries)
        )
        return self.db.scalar(stmt)

    def _upsert_bike_model(
        self, brand: Brand, series: BikeSeries | None, bike: NormalizedBike
    ) -> BikeModel:
        stmt = (
            insert(BikeModel)
            .values(
                brand_id=brand.id,
                series_id=series.id if series else None,
                name=bike.name,
                slug=bike.slug,
                model_year=bike.model_year,
                category=bike.category,
                usage_type=bike.usage_type,
                price_min=decimal_or_none(bike.price_min),
                price_max=decimal_or_none(bike.price_max),
                currency=bike.currency,
                official_url=bike.source_url,
                description=bike.description,
                raw_summary=bike.raw_summary,
                status="active",
            )
            .on_conflict_do_update(
                constraint="uq_bike_models_brand_slug_year",
                set_={
                    "series_id": series.id if series else None,
                    "name": bike.name,
                    "category": bike.category,
                    "usage_type": bike.usage_type,
                    "price_min": decimal_or_none(bike.price_min),
                    "price_max": decimal_or_none(bike.price_max),
                    "currency": bike.currency,
                    "official_url": bike.source_url,
                    "description": bike.description,
                    "raw_summary": bike.raw_summary,
                },
            )
            .returning(BikeModel)
        )
        return self.db.scalar(stmt)

    def _replace_variants(self, model: BikeModel, bike: NormalizedBike) -> None:
        self.db.query(BikeVariant).filter(BikeVariant.bike_model_id == model.id).delete()
        for variant in bike.variants:
            self.db.add(
                BikeVariant(
                    bike_model_id=model.id,
                    name=variant.get("name") or bike.name,
                    sku=variant.get("sku"),
                    color_name=variant.get("color_name"),
                    color_hex=variant.get("color_hex"),
                    price=decimal_or_none(variant.get("price")),
                    currency=variant.get("currency") or bike.currency,
                    size_options=variant.get("size_options"),
                    availability=variant.get("availability"),
                    official_url=variant.get("official_url") or bike.source_url,
                    raw_data=variant.get("raw_data"),
                )
            )

    def _replace_images(self, model: BikeModel, bike: NormalizedBike) -> None:
        self.db.query(BikeImage).filter(BikeImage.bike_model_id == model.id).delete()
        for index, image in enumerate(bike.images):
            self.db.add(
                BikeImage(
                    bike_model_id=model.id,
                    image_url=image["image_url"],
                    image_type=image.get("image_type", "gallery"),
                    position=image.get("position", index),
                    alt_text=image.get("alt_text"),
                    source_url=image.get("source_url") or bike.source_url,
                )
            )

    def _replace_components(self, model: BikeModel, bike: NormalizedBike) -> None:
        self.db.query(BikeComponent).filter(BikeComponent.bike_model_id == model.id).delete()
        for index, component in enumerate(bike.components):
            category = self._upsert_component_category(component.get("category") or "其他", index)
            self.db.add(
                BikeComponent(
                    bike_model_id=model.id,
                    category_id=category.id,
                    component_name=component["name"],
                    component_value=component["value"],
                    raw_text=component.get("raw_text"),
                    sort_order=index,
                )
            )

    def _upsert_component_category(self, name: str, sort_order: int) -> ComponentCategory:
        stmt = (
            insert(ComponentCategory)
            .values(name=name, slug=slugify(name), sort_order=sort_order)
            .on_conflict_do_update(index_elements=[ComponentCategory.slug], set_={"name": name})
            .returning(ComponentCategory)
        )
        return self.db.scalar(stmt)

    def _replace_geometry(self, model: BikeModel, bike: NormalizedBike) -> None:
        self.db.query(BikeGeometryValue).filter(
            BikeGeometryValue.geometry_profile_id.in_(
                select(BikeGeometryProfile.id).where(BikeGeometryProfile.bike_model_id == model.id)
            )
        ).delete(synchronize_session=False)
        self.db.query(BikeGeometryProfile).filter(BikeGeometryProfile.bike_model_id == model.id).delete()
        if not bike.geometry:
            return
        profile = BikeGeometryProfile(
            bike_model_id=model.id,
            geometry_image_url=bike.geometry.get("image_url"),
            raw_data=bike.geometry.get("raw_data"),
        )
        self.db.add(profile)
        self.db.flush()
        for value in bike.geometry.get("values", []):
            self.db.add(
                BikeGeometryValue(
                    geometry_profile_id=profile.id,
                    size_label=value["size_label"],
                    metric_name=value["metric_name"],
                    metric_label=value["metric_label"],
                    value=value.get("value"),
                    unit=value.get("unit"),
                )
            )

    def _replace_size_recommendations(self, model: BikeModel, bike: NormalizedBike) -> None:
        self.db.query(BikeSizeRecommendation).filter(
            BikeSizeRecommendation.bike_model_id == model.id
        ).delete()
        for item in bike.size_recommendations:
            self.db.add(
                BikeSizeRecommendation(
                    bike_model_id=model.id,
                    size_label=item["size_label"],
                    min_height_cm=item.get("min_height_cm"),
                    max_height_cm=item.get("max_height_cm"),
                    raw_data=item.get("raw_data"),
                )
            )

    def _upsert_source_mapping(
        self, brand: Brand, source_site: SourceSite, model: BikeModel, bike: NormalizedBike
    ) -> None:
        stmt = (
            insert(SourceProductMapping)
            .values(
                brand_id=brand.id,
                source_site_id=source_site.id,
                source_product_id=bike.source_product_id,
                source_url=bike.source_url,
                bike_model_id=model.id,
                raw_data=bike.raw_summary,
            )
            .on_conflict_do_update(
                constraint="uq_source_product_site_product",
                set_={"source_url": bike.source_url, "bike_model_id": model.id, "raw_data": bike.raw_summary},
            )
        )
        self.db.execute(stmt)

    def _append_price_history(self, model: BikeModel, bike: NormalizedBike) -> None:
        price = decimal_or_none(bike.price_min or bike.price_max)
        if not price or not bike.currency:
            return
        self.db.add(
            PriceHistory(
                bike_model_id=model.id,
                price=price,
                currency=bike.currency,
                source_url=bike.source_url,
            )
        )
