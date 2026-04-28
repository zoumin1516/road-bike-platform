from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class BrandOut(BaseModel):
    id: int
    name: str
    slug: str
    country: str | None = None
    official_site_url: str | None = None
    logo_url: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class BikeImageOut(BaseModel):
    id: int
    image_url: str
    image_type: str
    position: int
    alt_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BikeVariantOut(BaseModel):
    id: int
    name: str
    sku: str | None = None
    color_name: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    size_options: list[Any] | None = None
    availability: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BikeComponentOut(BaseModel):
    id: int
    category: str | None = None
    component_name: str
    component_value: str
    brand: str | None = None
    normalized_value: str | None = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class BikeListItemOut(BaseModel):
    id: int
    name: str
    slug: str
    model_year: int | None = None
    category: str | None = None
    usage_type: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    currency: str | None = None
    official_url: str | None = None
    brand: BrandOut
    cover_image_url: str | None = None


class BikeDetailOut(BaseModel):
    id: int
    name: str
    slug: str
    model_year: int | None = None
    category: str | None = None
    usage_type: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    currency: str | None = None
    official_url: str | None = None
    description: str | None = None
    raw_summary: dict[str, Any] | None = None
    brand: BrandOut
    series_name: str | None = None
    images: list[BikeImageOut]
    variants: list[BikeVariantOut]
    components: list[BikeComponentOut]
