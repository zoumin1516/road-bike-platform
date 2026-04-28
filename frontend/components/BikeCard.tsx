import Link from "next/link";

import { RemoteImage } from "@/components/RemoteImage";
import type { BikeListItem } from "@/lib/api";

export function BikeCard({ bike }: { bike: BikeListItem }) {
  const meta = [bike.model_year, bike.category, bike.usage_type].filter(Boolean);
  const priceLabel = bike.price_min ? `${bike.currency ?? ""} ${bike.price_min}` : "价格待铸";

  return (
    <article className="card">
      <div className="card-image">
        <RemoteImage
          src={bike.cover_image_url}
          alt={bike.name}
          width={640}
          height={420}
          sizes="(min-width: 1024px) 320px, 100vw"
        />
        <div className="card-image__overlay" />
      </div>
      <div className="card-body">
        <span className="eyebrow">{bike.brand.name}</span>
        <h3>{bike.name}</h3>
        <div className="card-meta">
          {(meta.length ? meta : ["待补充"]).map((item) => (
            <span key={String(item)}>{item}</span>
          ))}
        </div>
        <div className="card-price">{priceLabel}</div>
        <Link className="card-link" href={`/bikes/${bike.id}`}>
          查阅详情
        </Link>
      </div>
    </article>
  );
}
