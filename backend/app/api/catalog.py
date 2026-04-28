from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    BikeComponentOut,
    BikeDetailOut,
    BikeImageOut,
    BikeListItemOut,
    BikeVariantOut,
    BrandOut,
)
from app.schemas.common import pagination

router = APIRouter()


@router.get("/brands")
def list_brands(db: Session = Depends(get_db)) -> dict:
    repo = CatalogRepository(db)
    return {"items": [BrandOut.model_validate(item) for item in repo.list_brands()]}


@router.get("/bikes")
def list_bikes(
    brand: str | None = None,
    category: str | None = None,
    usage_type: str | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    repo = CatalogRepository(db)
    offset = (page - 1) * page_size
    items, total = repo.list_bikes(
        brand_slug=brand,
        category=category,
        usage_type=usage_type,
        keyword=keyword,
        limit=page_size,
        offset=offset,
    )
    return {
        "items": [bike_list_item(item) for item in items],
        "pagination": pagination(page, page_size, total),
        "filters": {
            "brand": brand,
            "category": category,
            "usage_type": usage_type,
            "keyword": keyword,
        },
    }


@router.get("/bikes/{bike_id}")
def get_bike(bike_id: int, db: Session = Depends(get_db)) -> dict:
    repo = CatalogRepository(db)
    bike = repo.get_bike(bike_id)
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")
    return {"data": bike_detail(bike)}


@router.get("/compare")
def compare_bikes(ids: str, db: Session = Depends(get_db)) -> dict:
    repo = CatalogRepository(db)
    parsed_ids = [int(item) for item in ids.split(",") if item.strip().isdigit()]
    bikes = [repo.get_bike(bike_id) for bike_id in parsed_ids[:4]]
    return {"items": [bike_detail(bike) for bike in bikes if bike]}


@router.get("/search")
def search_bikes(
    q: str = Query(min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    repo = CatalogRepository(db)
    offset = (page - 1) * page_size
    items, total = repo.list_bikes(keyword=q, limit=page_size, offset=offset)
    return {
        "items": [bike_list_item(item) for item in items],
        "pagination": pagination(page, page_size, total),
        "filters": {"q": q},
    }


def bike_list_item(bike) -> BikeListItemOut:
    cover = next((image.image_url for image in bike.images if image.image_type == "cover"), None)
    if not cover and bike.images:
        cover = bike.images[0].image_url
    return BikeListItemOut(
        id=bike.id,
        name=bike.name,
        slug=bike.slug,
        model_year=bike.model_year,
        category=bike.category,
        usage_type=bike.usage_type,
        price_min=bike.price_min,
        price_max=bike.price_max,
        currency=bike.currency,
        official_url=bike.official_url,
        brand=BrandOut.model_validate(bike.brand),
        cover_image_url=cover,
    )


def bike_detail(bike) -> BikeDetailOut:
    components = []
    for component in sorted(bike.components, key=lambda item: item.sort_order):
        components.append(
            BikeComponentOut(
                id=component.id,
                category=component.category.name if component.category else None,
                component_name=component.component_name,
                component_value=component.component_value,
                brand=component.brand,
                normalized_value=component.normalized_value,
                sort_order=component.sort_order,
            )
        )
    return BikeDetailOut(
        id=bike.id,
        name=bike.name,
        slug=bike.slug,
        model_year=bike.model_year,
        category=bike.category,
        usage_type=bike.usage_type,
        price_min=bike.price_min,
        price_max=bike.price_max,
        currency=bike.currency,
        official_url=bike.official_url,
        description=bike.description,
        raw_summary=bike.raw_summary,
        brand=BrandOut.model_validate(bike.brand),
        series_name=bike.series.name if bike.series else None,
        images=[BikeImageOut.model_validate(image) for image in bike.images],
        variants=[BikeVariantOut.model_validate(variant) for variant in bike.variants],
        components=components,
    )
