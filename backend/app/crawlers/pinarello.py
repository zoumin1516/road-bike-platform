from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import unquote, urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup, Tag
from slugify import slugify

from app.crawlers.base import BrandCrawler, NormalizedBike, RawBikeDetail, SourceProduct


class PinarelloCrawler(BrandCrawler):
    brand_slug = "pinarello"
    brand_name = "Pinarello"
    base_url = "https://pinarello.com"
    listing_url = "https://pinarello.com/china/zh/bikes/%E5%85%AC%E8%B7%AF%E8%BD%A6"

    def crawl_listing(self) -> list[SourceProduct]:
        html = self.fetch_text_with_retry(self.listing_url)
        soup = BeautifulSoup(html, "html.parser")
        products: list[SourceProduct] = []

        for card in soup.select(".cat-item"):
            link = card.select_one("a.cat-item-name[href]")
            if not isinstance(link, Tag):
                continue
            title = clean_text(link.select_one(".h4").get_text(" ", strip=True))
            href = repair_listing_url(to_absolute_url(self.base_url, link.get("href")), title)
            product_id = source_product_id_from_url(href)
            if not product_id or not title:
                continue

            products.append(
                SourceProduct(
                    source_product_id=product_id,
                    source_url=href,
                    title=title,
                    brand_slug=self.brand_slug,
                    series_name=series_name_from_url(href),
                    category="ROAD",
                    tags=tags_from_url(href),
                    image_url=card_image_url(card, self.base_url),
                    raw_data=parse_listing_card(card, href),
                )
            )

        deduped: dict[str, SourceProduct] = {}
        for product in products:
            deduped[product.source_product_id] = product
        return list(deduped.values())

    def crawl_detail(self, source_product: SourceProduct) -> RawBikeDetail:
        html = self.fetch_text_with_retry(source_product.source_url)
        soup = BeautifulSoup(html, "html.parser")
        detail_json = parse_detail_page(soup, source_product.source_url, self.base_url)
        detail_json["listing"] = source_product.raw_data
        return RawBikeDetail(
            source_product=source_product,
            detail_json=detail_json,
            detail_html=html,
            components=parse_components(soup),
        )

    def normalize(self, raw_detail: RawBikeDetail) -> NormalizedBike:
        source = raw_detail.source_product
        detail = raw_detail.detail_json
        name = detail.get("name") or source.title

        return NormalizedBike(
            brand_name=self.brand_name,
            brand_slug=self.brand_slug,
            source_site={
                "site_name": "Pinarello 中国官网",
                "base_url": self.base_url,
                "country": "Italy",
                "region": "CN",
                "language": "zh-CN",
                "currency": "CNY",
                "scrape_strategy": "html",
            },
            source_product_id=source.source_product_id,
            source_url=source.source_url,
            series_name=detail.get("series_name") or source.series_name,
            name=name,
            slug=slugify(f"{name}-{source.source_product_id}"),
            model_year=model_year_from_text(name, detail.get("variants") or []),
            category="ROAD",
            usage_type=detail.get("usage_type"),
            price_min=None,
            price_max=None,
            currency="CNY",
            description=detail.get("description"),
            images=detail.get("images") or [],
            variants=detail.get("variants") or [],
            components=raw_detail.components,
            geometry=detail.get("geometry"),
            raw_summary={
                "source": "pinarello_html",
                "listing": source.raw_data,
                "breadcrumb": detail.get("breadcrumb"),
                "subtitle": detail.get("subtitle"),
            },
        )

    def fetch_text_with_retry(self, url: str, attempts: int = 3) -> str:
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self.fetch_text(url)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(1 + attempt)
        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to fetch {url}")


def parse_listing_card(card: Tag, href: str) -> dict[str, Any]:
    link = card.select_one("a.cat-item-name")
    title = clean_text(link.select_one(".h4").get_text(" ", strip=True)) if link else None
    subtitle = ""
    if link:
        subtitle = clean_text(link.get_text(" ", strip=True).replace(title or "", "", 1))
    variant_images = [
        {
            "alt": clean_text(img.get("alt")),
            "image_url": img.get("src"),
        }
        for img in card.select(".cat-item-colors img[src]")
    ]
    features = [
        clean_text(item.get_text(" ", strip=True))
        for item in card.select(".cat-item-feat")
        if clean_text(item.get_text(" ", strip=True))
    ]
    return {
        "source_url": href,
        "title": title,
        "subtitle": subtitle,
        "features": features,
        "variant_images": variant_images,
        "image_url": card_image_url(card, PinarelloCrawler.base_url),
    }


def parse_detail_page(soup: BeautifulSoup, source_url: str, base_url: str) -> dict[str, Any]:
    breadcrumb = [
        clean_text(link.get_text(" ", strip=True))
        for link in soup.select(".product__top .breadcrumb a")
    ]
    name = text_or_none(soup.select_one(".product__mtitle"))
    subtitle = text_or_none(soup.select_one(".product__top + h3, .product-emo h3"))
    if not subtitle:
        subtitle = text_or_none(soup.select_one(".product-emo"))

    return {
        "name": name,
        "subtitle": subtitle,
        "breadcrumb": breadcrumb,
        "series_name": breadcrumb[-1] if breadcrumb else series_name_from_url(source_url),
        "usage_type": usage_type_from_breadcrumb(breadcrumb),
        "description": description_from_page(soup),
        "images": normalize_images(soup, source_url, base_url),
        "variants": normalize_variants(soup, source_url, name),
        "geometry": normalize_geometry(soup, source_url, base_url),
    }


def parse_components(soup: BeautifulSoup) -> list[dict[str, str]]:
    section = soup.select_one(".product-components")
    if not isinstance(section, Tag):
        return []

    components: list[dict[str, str]] = []
    for title in section.select(".components-title"):
        category = clean_text(title.get_text(" ", strip=True))
        sibling = title.find_next_sibling()
        while isinstance(sibling, Tag) and "components-title" not in sibling.get("class", []):
            for item in sibling.select(".col-lg-4"):
                name = text_or_none(item.select_one("strong"))
                value_node = item.select_one(".color--dark-gray")
                value = text_or_none(value_node)
                if name and value:
                    components.append(
                        {
                            "category": category,
                            "name": name,
                            "value": value,
                            "raw_text": clean_text(item.get_text(" ", strip=True)),
                        }
                    )
            sibling = sibling.find_next_sibling()
    return components


def normalize_images(
    soup: BeautifulSoup, source_url: str, base_url: str
) -> list[dict[str, Any]]:
    image_urls: list[str] = []
    for item in soup.select(".product-hero-views a[data-full], .main-gallery__photo[data-image]"):
        url = item.get("data-full") or item.get("data-image")
        if url:
            image_urls.append(to_absolute_url(base_url, url))
    for img in soup.select(".bike-hero img[src], .product-emo img[src]"):
        image_urls.append(to_absolute_url(base_url, img.get("src")))

    return [
        {
            "image_url": url,
            "image_type": "cover" if index == 0 else "gallery",
            "position": index,
            "source_url": source_url,
        }
        for index, url in enumerate(dict.fromkeys(image_urls))
    ]


def normalize_variants(
    soup: BeautifulSoup, source_url: str, product_name: str | None
) -> list[dict[str, Any]]:
    desc_by_variation = {
        item.get("data-variation"): clean_text(item.get_text(" ", strip=True))
        for item in soup.select(".product-hero-desc__var[data-variation]")
    }
    variants: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for item in soup.select(".product-hero-vars a[data-gallery]"):
        img = item.select_one("img")
        variation = item.get("data-gallery")
        sku = item.get("data-locally") or variation
        color_text = desc_by_variation.get(variation) or clean_text(img.get("alt")) if img else None
        color_name = color_name_from_text(color_text)
        key = (sku, color_name)
        if key in seen:
            continue
        seen.add(key)
        variants.append(
            {
                "name": clean_text(img.get("alt")) if img else product_name,
                "sku": sku,
                "color_name": color_name,
                "currency": "CNY",
                "official_url": source_url,
                "raw_data": {
                    "variation": variation,
                    "description": color_text,
                    "image_url": img.get("src") if img else None,
                },
            }
        )

    if not variants:
        variants.append(
            {
                "name": product_name,
                "sku": source_product_id_from_url(source_url),
                "currency": "CNY",
                "official_url": source_url,
                "raw_data": {},
            }
        )
    return variants


def normalize_geometry(
    soup: BeautifulSoup, source_url: str, base_url: str
) -> dict[str, Any] | None:
    section = soup.select_one(".product-geometry")
    if not isinstance(section, Tag):
        return None
    table = section.select_one("table")
    if not isinstance(table, Tag):
        return None

    headers = [clean_text(item.get_text(" ", strip=True)) for item in table.select("thead th")]
    values: list[dict[str, Any]] = []
    size_index = headers.index("CC") if "CC" in headers else 0
    for row in table.select("tbody tr"):
        cells = [clean_text(item.get_text(" ", strip=True)) for item in row.select("td")]
        if not cells or len(cells) != len(headers):
            continue
        size_label = cells[size_index]
        for index, header in enumerate(headers):
            if index == size_index:
                continue
            values.append(
                {
                    "size_label": size_label,
                    "metric_name": slugify(header) or header,
                    "metric_label": header,
                    "value": cells[index],
                    "unit": unit_from_metric(header),
                }
            )

    image = section.select_one("img[src]")
    return {
        "image_url": to_absolute_url(base_url, image.get("src")) if image else None,
        "values": values,
        "raw_data": {
            "source_url": source_url,
            "headers": headers,
        },
    }


def card_image_url(card: Tag, base_url: str) -> str | None:
    image = card.select_one(".cat-item-imgwrap img[src]") or card.select_one("img[src]")
    return to_absolute_url(base_url, image.get("src")) if image else None


def repair_listing_url(url: str, title: str) -> str:
    title_upper = title.upper()
    if title_upper.startswith("DOGMA F RED ETAP AXS"):
        if "/%E7%AB%9E%E8%B5%9B/" in url and "/new-dogma-f/" not in url:
            return url.replace(
                "/%E7%AB%9E%E8%B5%9B/",
                "/%E7%AB%9E%E8%B5%9B/new-dogma-f/",
                1,
            )
        if "/竞赛/" in url and "/new-dogma-f/" not in url:
            return url.replace("/竞赛/", "/竞赛/new-dogma-f/", 1)
    return url


def description_from_page(soup: BeautifulSoup) -> str | None:
    parts: list[str] = []
    for selector in [".product-emo", ".product__endTxt"]:
        text = text_or_none(soup.select_one(selector))
        if text:
            parts.append(text)
    return "\n\n".join(dict.fromkeys(parts)) or None


def source_product_id_from_url(url: str) -> str:
    path = unquote(urlparse(url).path).strip("/")
    parts = [part for part in path.split("/") if part]
    if not parts:
        return slugify(url)
    return slugify("-".join(parts[-2:])) if len(parts) >= 2 else slugify(parts[-1])


def series_name_from_url(url: str) -> str | None:
    parts = [part for part in unquote(urlparse(url).path).split("/") if part]
    return parts[-2].replace("-", " ").title() if len(parts) >= 2 else None


def tags_from_url(url: str) -> list[str]:
    parts = [part for part in unquote(urlparse(url).path).split("/") if part]
    return [part for part in parts if part in {"竞赛", "耐力", "超级电动"}]


def usage_type_from_breadcrumb(breadcrumb: list[str]) -> str | None:
    for item in breadcrumb:
        if item in {"竞赛", "耐力", "超级电动"}:
            return item
    return None


def color_name_from_text(value: str | None) -> str | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(" - ") if part.strip()]
    return parts[-1] if len(parts) > 1 else value


def model_year_from_text(name: str, variants: list[dict[str, Any]]) -> int | None:
    candidates = [name]
    candidates.extend(str(variant.get("name") or "") for variant in variants)
    for candidate in candidates:
        match = re.search(r"\bMY(\d{2})\b", candidate, flags=re.IGNORECASE)
        if match:
            return 2000 + int(match.group(1))
    return None


def unit_from_metric(metric: str) -> str | None:
    match = re.search(r"\[([^\]]+)\]", metric)
    return match.group(1) if match else None


def text_or_none(node: Tag | None) -> str | None:
    if not node:
        return None
    return clean_text(node.get_text(" ", strip=True)) or None


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def to_absolute_url(base_url: str, url: str | None) -> str:
    absolute_url = urljoin(base_url, url or "")
    parsed = urlparse(absolute_url)
    normalized_path = re.sub(r"/{2,}", "/", parsed.path)
    return urlunparse(parsed._replace(path=normalized_path))
