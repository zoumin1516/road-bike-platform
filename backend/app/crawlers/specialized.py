from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
from slugify import slugify

from app.crawlers.base import BrandCrawler, NormalizedBike, RawBikeDetail, SourceProduct


class SpecializedCrawler(BrandCrawler):
    brand_slug = "specialized"
    brand_name = "Specialized"
    base_url = "https://www.specialized.com.cn"
    listing_url = "https://www.specialized.com.cn/cn/zh/shop/bikes"
    product_search_url = "https://www.specialized.com.cn/rest/v2/SBCChina/products/search"
    product_detail_url = "https://www.specialized.com.cn/rest/v2/SBCChina/products/{product_code}"
    specs_url = "https://www.specialized.com.cn/cn/zh/pdp/{product_code}/specs"
    geometry_url = "https://www.specialized.com.cn/cn/zh/pdp/{product_code}/geos"
    scene7_url = "https://assets.specialized.com/i/specialized/"
    road_bike_query = ":relevance:archived:false:isBike:true:group:自行车:categoryProperty:公路"

    def crawl_listing(self) -> list[SourceProduct]:
        products: list[SourceProduct] = []
        current_page = 0
        while True:
            params = urlencode(
                {
                    "query": self.road_bike_query,
                    "fields": "DEFAULT",
                    "pageSize": 100,
                    "currentPage": current_page,
                }
            )
            payload = self.fetch_json(
                f"{self.product_search_url}?{params}",
                headers={"Accept": "application/json"},
            )
            for item in payload.get("products") or []:
                product_code = extract_product_code(item)
                if not product_code:
                    continue
                products.append(
                    SourceProduct(
                        source_product_id=product_code,
                        source_url=to_absolute_url(self.base_url, item.get("url")),
                        title=item.get("name") or item.get("title") or product_code,
                        brand_slug=self.brand_slug,
                        series_name=item.get("productFamily"),
                        category="ROAD",
                        tags=[item.get("group"), item.get("productFamily")],
                        image_url=listing_image_url(item, self.scene7_url),
                        raw_data=item,
                    )
                )

            pagination = payload.get("pagination") or {}
            if current_page + 1 >= int(pagination.get("totalPages") or 0):
                break
            current_page += 1

        deduped: dict[str, SourceProduct] = {}
        for product in products:
            deduped[product.source_product_id] = product
        return list(deduped.values())

    def crawl_detail(self, source_product: SourceProduct) -> RawBikeDetail:
        product_code = source_product.source_product_id
        product = self.fetch_json(
            self.product_detail_url.format(product_code=product_code),
            headers={"Accept": "application/json"},
        )
        specs = self.fetch_json(
            self.specs_url.format(product_code=product_code),
            headers={"Accept": "application/json"},
        )
        geometry = self.fetch_json(
            self.geometry_url.format(product_code=product_code),
            headers={"Accept": "application/json"},
        )
        detail_html = self.fetch_text(source_product.source_url)
        return RawBikeDetail(
            source_product=source_product,
            detail_json={"product": product, "specs": specs, "geometry": geometry},
            detail_html=detail_html,
            components=parse_specs(specs),
        )

    def normalize(self, raw_detail: RawBikeDetail) -> NormalizedBike:
        source = raw_detail.source_product
        product = raw_detail.detail_json.get("product") or {}
        specs = raw_detail.detail_json.get("specs") or {}
        geometry_json = raw_detail.detail_json.get("geometry") or {}
        name = product.get("name") or source.title
        variants = normalize_variants(product, source.source_url)
        prices = [variant.get("price") for variant in variants if variant.get("price") is not None]
        geometry = normalize_geometry(geometry_json)

        return NormalizedBike(
            brand_name=self.brand_name,
            brand_slug=self.brand_slug,
            source_site={
                "site_name": "Specialized 中国官网",
                "base_url": self.base_url,
                "country": "China",
                "region": "CN",
                "language": "zh-CN",
                "currency": "CNY",
                "scrape_strategy": "api",
            },
            source_product_id=source.source_product_id,
            source_url=source.source_url,
            series_name=product.get("productFamily") or source.series_name,
            name=name,
            slug=slugify(f"{name}-{source.source_product_id}"),
            model_year=int_or_none(product.get("modelYear")),
            category="ROAD",
            usage_type=usage_type_from_product(product),
            price_min=str(min(prices)) if prices else None,
            price_max=str(max(prices)) if prices else None,
            currency="CNY",
            description=html_to_text(product.get("description")),
            images=normalize_images(product, self.scene7_url, source.source_url),
            variants=variants,
            components=raw_detail.components,
            geometry=geometry,
            raw_summary={
                "source": "specialized_occ",
                "listing": source.raw_data,
                "productFamily": product.get("productFamily"),
                "group": product.get("group"),
                "archived": product.get("archived"),
                "specModelName": (specs.get("responseObject") or {}).get("modelName"),
            },
        )


def extract_product_code(item: dict[str, Any]) -> str | None:
    if item.get("url"):
        match = re.search(r"/p/(\d+)", item["url"])
        if match:
            return match.group(1)
    code = item.get("code")
    if isinstance(code, str) and "-" in code:
        return code.rsplit("-", 1)[-1]
    return str(code) if code else None


def to_absolute_url(base_url: str, url: str | None) -> str:
    return urljoin(base_url, url or "")


def listing_image_url(item: dict[str, Any], scene7_url: str) -> str | None:
    variant = first_variant(item)
    image_id = variant.get("plpImageID") or qualifier_value(variant, "product")
    return scene7_image_url(scene7_url, image_id, "wid=800&fmt=webp")


def normalize_images(
    product: dict[str, Any], scene7_url: str, source_url: str
) -> list[dict[str, Any]]:
    image_urls: list[str] = []
    for color in product.get("colors") or []:
        sorted_images = sorted(
            color.get("images") or [], key=lambda item: item.get("displayOrder") or 0
        )
        for image in sorted_images:
            image_url = image.get("mobileHRImageURL") or image.get("mobileImageURL")
            if not image_url:
                image_url = scene7_image_url(scene7_url, image.get("code"), "wid=1200&fmt=webp")
            if image_url:
                image_urls.append(image_url)
    if not image_urls:
        image_url = scene7_image_url(scene7_url, product.get("scene7Id"), "wid=1200&fmt=webp")
        if image_url:
            image_urls.append(image_url)

    return [
        {
            "image_url": url,
            "image_type": "cover" if index == 0 else "gallery",
            "position": index,
            "source_url": source_url,
        }
        for index, url in enumerate(dict.fromkeys(image_urls))
    ]


def normalize_variants(product: dict[str, Any], source_url: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    color_names = color_name_by_code(product)
    seen: set[str] = set()
    for color in product.get("colors") or []:
        price = price_value(color.get("price") or color.get("priceData"))
        variants.append(
            {
                "name": product.get("name"),
                "sku": color.get("code"),
                "color_name": color.get("name") or color_names.get(color.get("code")),
                "price": price,
                "currency": "CNY",
                "official_url": color_url(source_url, color.get("code")),
                "raw_data": color,
            }
        )
        if color.get("code"):
            seen.add(color["code"])

    for variant in product.get("variantOptions") or []:
        if variant.get("code") in seen:
            continue
        price = price_value(variant.get("priceData"))
        variants.append(
            {
                "name": product.get("name"),
                "sku": variant.get("code"),
                "color_name": color_names.get(variant.get("code"))
                or qualifier_value(variant, "colorName"),
                "color_hex": first_color_hex(qualifier_value(variant, "color")),
                "price": price,
                "currency": "CNY",
                "official_url": f"{source_url}?color={variant.get('code')}",
                "raw_data": variant,
            }
        )
        if variant.get("code"):
            seen.add(variant["code"])

    if not variants:
        variants.append(
            {
                "name": product.get("name"),
                "sku": product.get("code"),
                "price": price_value(product.get("price") or product.get("priceData")),
                "currency": "CNY",
                "official_url": source_url,
                "raw_data": {"source": "fallback_single_variant"},
            }
        )
    return variants


def parse_specs(specs: dict[str, Any]) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    response = specs.get("responseObject") or {}
    for group in response.get("specs") or []:
        category = group.get("name") or "规格"
        for spec in group.get("specs") or []:
            name = spec.get("name")
            value = spec.get("description")
            if name and value:
                components.append(
                    {
                        "category": category,
                        "name": name,
                        "value": value,
                        "raw_text": f"{category} | {name} | {value}",
                    }
                )
    return components


def normalize_geometry(geometry_json: dict[str, Any]) -> dict[str, Any] | None:
    response = geometry_json.get("responseObject") or {}
    geos = response.get("geos") or {}
    size_headers = geos.get("sizeHeaders") or []
    rows = geos.get("rows") or []
    if not size_headers or not rows:
        return None

    values = []
    for row in rows:
        metric_label = row.get("name")
        metric_name = slugify(metric_label or "", separator="_")
        for index, size_label in enumerate(size_headers):
            row_values = row.get("value") or []
            if index < len(row_values):
                values.append(
                    {
                        "size_label": size_label,
                        "metric_name": metric_name,
                        "metric_label": metric_label,
                        "value": row_values[index],
                    }
                )
    return {"raw_data": response, "values": values}


def color_url(source_url: str, color_code: str | None) -> str:
    return f"{source_url}?color={color_code}" if color_code else source_url


def usage_type_from_product(product: dict[str, Any]) -> str | None:
    for item in product.get("analyticsData") or []:
        if item.get("facetType") == "experience":
            values = item.get("value") or []
            return values[0] if values else None
    return None


def first_variant(item: dict[str, Any]) -> dict[str, Any]:
    variants = item.get("variantOptions") or []
    return variants[0] if variants else {}


def qualifier_value(variant: dict[str, Any], qualifier: str) -> str | None:
    for item in variant.get("variantOptionQualifiers") or []:
        if item.get("qualifier") == qualifier:
            value = item.get("value")
            if value:
                return value
            image = item.get("image") or {}
            return image.get("url")
    return None


def color_name_by_code(product: dict[str, Any]) -> dict[str, str]:
    names = {}
    for variant in product.get("variantOptions") or []:
        code = variant.get("code")
        color_name = qualifier_value(variant, "colorName")
        if code and color_name:
            names[code] = color_name.strip("[]")
    return names


def first_color_hex(value: str | None) -> str | None:
    if not value:
        return None
    colors = value.replace("[", "").replace("]", "").split(",")
    return colors[0] if colors and colors[0] else None


def scene7_image_url(scene7_url: str, image_id: str | None, query: str) -> str | None:
    if not image_id:
        return None
    if image_id.startswith("http"):
        return image_id
    return f"{scene7_url}{image_id}?{query}"


def price_value(price: dict[str, Any] | None) -> float | None:
    if not price:
        return None
    value = price.get("value")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def html_to_text(value: str | None) -> str | None:
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
