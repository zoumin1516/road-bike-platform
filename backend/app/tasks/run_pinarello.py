from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.crawlers.base import SnapshotStore
from app.crawlers.pinarello import PinarelloCrawler
from app.db.session import SessionLocal
from app.models import Brand, CrawlerJob, SourceSite
from app.repositories.catalog import CatalogRepository
from app.repositories.crawler import CrawlerRepository


def run(limit: int | None = None) -> dict[str, int]:
    crawler = PinarelloCrawler()
    snapshot_store = SnapshotStore()
    products = crawler.crawl_listing()
    if limit:
        products = products[:limit]

    stats = {"listing_count": len(products), "imported": 0, "failed": 0}
    with SessionLocal() as db:
        source_site = ensure_pinarello_source_site(db, crawler)
        job = CrawlerJob(
            source_site_id=source_site.id,
            job_type="full_sync" if limit is None else "limited_sync",
            status="running",
            started_at=datetime.now(UTC),
            stats={"limit": limit, "listing_count": len(products)},
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        catalog_repo = CatalogRepository(db)
        crawler_repo = CrawlerRepository(db)
        try:
            for product in products:
                try:
                    raw_detail = crawler.crawl_detail(product)
                    normalized = crawler.normalize(raw_detail)
                    catalog_repo.upsert_normalized_bike(normalized)
                    db.flush()

                    if raw_detail.detail_html:
                        digest, path = snapshot_store.save_text(
                            crawler.brand_slug,
                            product.source_product_id,
                            "detail",
                            raw_detail.detail_html,
                        )
                        crawler_repo.save_snapshot(
                            source_site=source_site,
                            url=product.source_url,
                            content_hash=digest,
                            raw_html_path=path,
                        )
                    crawler_repo.save_snapshot(
                        source_site=source_site,
                        url=product.source_url,
                        content_hash=snapshot_store.content_hash(raw_detail.detail_json),
                        raw_json=raw_detail.detail_json,
                    )
                    stats["imported"] += 1
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    stats["failed"] += 1
                    print(f"[pinarello] failed product={product.source_product_id}: {exc}")
                else:
                    db.commit()
            job.status = "success" if stats["failed"] == 0 else "partial_success"
            job.finished_at = datetime.now(UTC)
            job.stats = stats
            db.commit()
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.finished_at = datetime.now(UTC)
            job.error_message = str(exc)
            job.stats = stats
            db.add(job)
            db.commit()
            raise
    return stats


def ensure_pinarello_source_site(db, crawler: PinarelloCrawler) -> SourceSite:
    brand = db.scalar(select(Brand).where(Brand.slug == crawler.brand_slug))
    if not brand:
        brand_stmt = (
            insert(Brand)
            .values(
                name=crawler.brand_name,
                slug=crawler.brand_slug,
                country="Italy",
                official_site_url=crawler.base_url,
                status="active",
            )
            .on_conflict_do_update(
                index_elements=[Brand.slug],
                set_={"name": crawler.brand_name, "official_site_url": crawler.base_url},
            )
            .returning(Brand)
        )
        brand = db.scalar(brand_stmt)

    site_stmt = (
        insert(SourceSite)
        .values(
            brand_id=brand.id,
            site_name="Pinarello 中国官网",
            base_url=crawler.base_url,
            region="CN",
            language="zh-CN",
            currency="CNY",
            scrape_strategy="html",
            status="active",
        )
        .on_conflict_do_update(
            constraint="uq_source_sites_brand_base_url",
            set_={
                "site_name": "Pinarello 中国官网",
                "region": "CN",
                "language": "zh-CN",
                "currency": "CNY",
            },
        )
        .returning(SourceSite)
    )
    source_site = db.scalar(site_stmt)
    db.flush()
    return source_site


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Pinarello China road bike products.")
    parser.add_argument("--limit", type=int, default=None, help="Limit products for a smoke run.")
    args = parser.parse_args()
    print(json.dumps(run(limit=args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
