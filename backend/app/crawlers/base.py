from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


@dataclass(slots=True)
class SourceProduct:
    source_product_id: str
    source_url: str
    title: str
    brand_slug: str
    series_name: str | None = None
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    image_url: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RawBikeDetail:
    source_product: SourceProduct
    detail_json: dict[str, Any]
    detail_html: str | None = None
    components: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class NormalizedBike:
    brand_name: str
    brand_slug: str
    source_site: dict[str, Any]
    source_product_id: str
    source_url: str
    series_name: str | None
    name: str
    slug: str
    model_year: int | None = None
    category: str | None = None
    usage_type: str | None = None
    price_min: str | None = None
    price_max: str | None = None
    currency: str | None = None
    description: str | None = None
    images: list[dict[str, Any]] = field(default_factory=list)
    variants: list[dict[str, Any]] = field(default_factory=list)
    components: list[dict[str, Any]] = field(default_factory=list)
    geometry: dict[str, Any] | None = None
    size_recommendations: list[dict[str, Any]] = field(default_factory=list)
    raw_summary: dict[str, Any] = field(default_factory=dict)


class BrandCrawler(ABC):
    brand_slug: str
    brand_name: str
    base_url: str

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(
            headers={
                "User-Agent": settings.crawler_user_agent,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            timeout=30,
            follow_redirects=True,
        )

    def fetch_text(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        response = self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def fetch_json(self, url: str, *, headers: dict[str, str] | None = None) -> Any:
        response = self.client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def crawl_listing(self) -> list[SourceProduct]:
        raise NotImplementedError

    @abstractmethod
    def crawl_detail(self, source_product: SourceProduct) -> RawBikeDetail:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_detail: RawBikeDetail) -> NormalizedBike:
        raise NotImplementedError


class SnapshotStore:
    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir or settings.snapshot_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def content_hash(self, content: str | bytes | dict[str, Any] | list[Any]) -> str:
        if isinstance(content, bytes):
            payload = content
        elif isinstance(content, str):
            payload = content.encode("utf-8")
        else:
            payload = json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def save_text(self, brand_slug: str, source_product_id: str, kind: str, text: str) -> tuple[str, str]:
        digest = self.content_hash(text)
        path = self.root_dir / brand_slug / source_product_id
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"{kind}-{digest[:12]}.html"
        file_path.write_text(text, encoding="utf-8")
        return digest, str(file_path)
