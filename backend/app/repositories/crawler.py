from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import CrawlerSnapshot, SourceSite


class CrawlerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_snapshot(
        self,
        *,
        source_site: SourceSite,
        url: str,
        content_hash: str,
        raw_html_path: str | None = None,
        raw_json: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        stmt = (
            insert(CrawlerSnapshot)
            .values(
                source_site_id=source_site.id,
                url=url,
                content_hash=content_hash,
                raw_html_path=raw_html_path,
                raw_json=raw_json,
            )
            .on_conflict_do_nothing(constraint="uq_snapshot_hash")
        )
        self.db.execute(stmt)
