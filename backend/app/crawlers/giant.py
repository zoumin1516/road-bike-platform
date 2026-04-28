from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from slugify import slugify

from app.crawlers.base import BrandCrawler, NormalizedBike, RawBikeDetail, SourceProduct


class GiantCrawler(BrandCrawler):
    brand_slug = "giant"
    brand_name = "Giant"
    base_url = "https://www.giant.com.cn"
    listing_url = "https://www.giant.com.cn/index.php/index/bike_finder.html"
    detail_api_url = "https://www.giant.com.cn/index.php/index/get_bike_info?id={bike_id}"

    def crawl_listing(self) -> list[SourceProduct]:
        html = self.fetch_text(self.listing_url)
        soup = BeautifulSoup(html, "html.parser")
        products: list[SourceProduct] = []

        for series_el in soup.select(".list_bikeseries .item_bikeseries.s_powertype_manpower"):
            series_name = text_or_none(series_el.select_one(".bikeseries_title .title"))
            for item in series_el.select(".item_bike"):
                link = item.select_one(".item_bike_box[href]")
                if not link:
                    continue
                href = urljoin(self.base_url, link.get("href", ""))
                bike_id = extract_query_id(href)
                if not bike_id:
                    continue

                title_el = item.select_one(".title")
                badges = [clean_text(badge.get_text(" ")) for badge in item.select(".badge")]
                title = title_without_badges(title_el, badges) if title_el else ""
                category = text_or_none(item.select_one(".subtitle"))
                image_el = item.select_one(".cover[data-lazybgimg]")
                image_url = (
                    strip_giant_image_suffix(image_el.get("data-lazybgimg")) if image_el else None
                )
                colors = [
                    clean_text(color.get("data-tag", ""))
                    for color in item.select(".item_modelcolor[data-tag]")
                    if clean_text(color.get("data-tag", ""))
                ]

                products.append(
                    SourceProduct(
                        source_product_id=bike_id,
                        source_url=href,
                        title=title,
                        brand_slug=self.brand_slug,
                        series_name=series_name,
                        category=category,
                        tags=badges,
                        image_url=image_url,
                        raw_data={
                            "colors": colors,
                            "class": item.get("class", []),
                            "data_tag": item.get("data-tag"),
                            "listing_category": category,
                        },
                    )
                )

        deduped: dict[str, SourceProduct] = {}
        for product in products:
            deduped[product.source_product_id] = product
        return list(deduped.values())

    def crawl_detail(self, source_product: SourceProduct) -> RawBikeDetail:
        detail_json = self.fetch_json(
            self.detail_api_url.format(bike_id=source_product.source_product_id),
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": source_product.source_url,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        detail_html = self.fetch_text(source_product.source_url)
        components = parse_component_tables(detail_html)
        return RawBikeDetail(
            source_product=source_product,
            detail_json=detail_json,
            detail_html=detail_html,
            components=components,
        )

    def normalize(self, raw_detail: RawBikeDetail) -> NormalizedBike:
        data = raw_detail.detail_json
        source = raw_detail.source_product
        name = data.get("name") or source.title
        images = parse_json_list(data.get("imgs"))
        image_items = normalize_images(data.get("img"), images, source.source_url)
        variants = normalize_color_variants(data, source.source_url)
        geometry, size_recommendations = normalize_geometry(data.get("frameGeometryImport"))

        category = data.get("surfaceLabelName") or source.category
        usage_type = data.get("levelLabelName")

        return NormalizedBike(
            brand_name=self.brand_name,
            brand_slug=self.brand_slug,
            source_site={
                "site_name": "Giant 中国官网",
                "base_url": self.base_url,
                "country": "China",
                "region": "CN",
                "language": "zh-CN",
                "currency": "CNY",
                "scrape_strategy": "hybrid",
            },
            source_product_id=source.source_product_id,
            source_url=source.source_url,
            series_name=data.get("bikeModelName") or source.series_name,
            name=name,
            slug=slugify(f"{name}-{source.source_product_id}"),
            model_year=int(data["year"]) if str(data.get("year", "")).isdigit() else None,
            category=category,
            usage_type=usage_type,
            price_min=data.get("priceMin") or data.get("sellPrice") or data.get("marketPrice"),
            price_max=data.get("priceMax") or data.get("sellPrice") or data.get("marketPrice"),
            currency="CNY",
            description=data.get("describe"),
            images=image_items,
            variants=variants,
            components=raw_detail.components,
            geometry=geometry,
            size_recommendations=size_recommendations,
            raw_summary={
                "source": "giant_get_bike_info",
                "source_product": source.raw_data,
                "categoryName": data.get("categoryName"),
                "surfaceName": data.get("surfaceName"),
                "levelName": data.get("levelName"),
                "modelFamilyName": data.get("modelFamilyName"),
                "bikeModelName": data.get("bikeModelName"),
                "shopOnlineStatus": data.get("shopOnlineStatus"),
            },
        )


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def text_or_none(node: Any) -> str | None:
    if not node:
        return None
    text = clean_text(node.get_text(" "))
    return text or None


def title_without_badges(title_el: Any, badges: list[str]) -> str:
    text = clean_text(title_el.get_text(" "))
    for badge in badges:
        text = re.sub(rf"^{re.escape(badge)}\s*", "", text).strip()
    return text


def extract_query_id(url: str) -> str | None:
    match = re.search(r"[?&]id=(\d+)", url)
    return match.group(1) if match else None


def strip_giant_image_suffix(url: str | None) -> str | None:
    if not url:
        return None
    return re.sub(r"@!.*$", "", url)


def parse_json_list(value: str | list[Any] | None) -> list[dict[str, Any]]:
    if not value:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in parsed if isinstance(item, dict)]


def normalize_images(
    cover_url: str | None, image_items: list[dict[str, Any]], source_url: str
) -> list[dict[str, Any]]:
    urls: list[str] = []
    if cover_url:
        urls.append(strip_giant_image_suffix(cover_url) or cover_url)
    for item in image_items:
        image_url = item.get("img")
        if image_url:
            urls.append(strip_giant_image_suffix(image_url) or image_url)

    deduped = list(dict.fromkeys(urls))
    return [
        {
            "image_url": url,
            "image_type": "cover" if index == 0 else "gallery",
            "position": index,
            "source_url": source_url,
        }
        for index, url in enumerate(deduped)
    ]


def normalize_color_variants(data: dict[str, Any], source_url: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    seen_keys: set[tuple[str | None, str | None]] = set()
    for color in data.get("colorImgList") or []:
        color_name = color.get("name")
        sku = str(data.get("productId")) if data.get("productId") else None
        variant_key = (sku, color_name)
        if variant_key in seen_keys:
            continue
        seen_keys.add(variant_key)
        variants.append(
            {
                "name": data.get("name"),
                "sku": sku,
                "color_name": color_name,
                "price": data.get("sellPrice") or data.get("priceMin"),
                "currency": "CNY",
                "official_url": source_url,
                "raw_data": color,
            }
        )
    if not variants:
        variants.append(
            {
                "name": data.get("name"),
                "sku": str(data.get("productId")) if data.get("productId") else None,
                "price": data.get("sellPrice") or data.get("priceMin"),
                "currency": "CNY",
                "official_url": source_url,
                "raw_data": {"source": "fallback_single_variant"},
            }
        )
    return variants


def parse_component_tables(detail_html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(detail_html, "html.parser")
    components: list[dict[str, str]] = []
    for table_index, table in enumerate(soup.select("table")):
        rows = table.select("tr")
        category = None
        for row in rows:
            cells = [clean_text(cell.get_text(" ")) for cell in row.select("th,td")]
            cells = [cell for cell in cells if cell]
            if not cells:
                continue
            if len(cells) == 1:
                category = cells[0]
                continue
            name, value = cells[0], " ".join(cells[1:])
            if name and value:
                components.append(
                    {
                        "category": category or f"规格表 {table_index + 1}",
                        "name": name,
                        "value": value,
                        "raw_text": " | ".join(cells),
                    }
                )
    return components


def normalize_geometry(
    frame_geometry_import: str | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if not frame_geometry_import:
        return None, []
    try:
        raw = json.loads(frame_geometry_import)
    except json.JSONDecodeError:
        return {"raw_data": {"frameGeometryImport": frame_geometry_import}, "values": []}, []

    values: list[dict[str, Any]] = []
    nav = raw.get("geometricParametersNav") or {}
    for metric_row in raw.get("geometricParametersArr") or []:
        metric_label = metric_row.get("A")
        if not metric_label:
            continue
        metric_name = slugify(metric_label, separator="_")
        for size_key in nav.keys():
            if size_key in metric_row:
                values.append(
                    {
                        "size_label": size_key,
                        "metric_name": metric_name,
                        "metric_label": metric_label,
                        "value": metric_row.get(size_key),
                    }
                )

    size_recommendations = []
    for item in raw.get("suitableHeightArr") or []:
        size_label = item.get("A")
        if not size_label:
            continue
        size_recommendations.append(
            {
                "size_label": size_label,
                "min_height_cm": int_or_none(item.get("最小身高（cm）")),
                "max_height_cm": int_or_none(item.get("最大身高（cm）")),
                "raw_data": item,
            }
        )

    return (
        {
            "image_url": raw.get("imgUrl"),
            "raw_data": raw,
            "values": values,
        },
        size_recommendations,
    )


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
