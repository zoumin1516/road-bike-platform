import Link from "next/link";

import { getBrands } from "@/lib/api";

export default async function BrandsPage() {
  const brands = await getBrands().catch(() => ({ items: [] }));

  return (
    <>
      <section className="detail-hero">
        <span className="eyebrow">Brand Codex</span>
        <h1>品牌图鉴</h1>
        <p className="muted">每一面战旗背后的官网来源、产地与抓取血脉</p>
      </section>

      <section className="section">
        <div className="brand-grid">
          {brands.items.map((brand) => (
            <article key={brand.slug} className="brand-card">
              <span className="eyebrow">{brand.country || "Global"}</span>
              <h3>{brand.name}</h3>
              {brand.official_site_url ? (
                <a
                  className="card-link"
                  href={brand.official_site_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  官网圣坛
                </a>
              ) : null}
              <Link className="card-link" href={`/?brand=${brand.slug}#bike-list`}>
                查阅车型
              </Link>
            </article>
          ))}
          {brands.items.length === 0 ? (
            <div className="empty-state">尚未点燃任何品牌之火</div>
          ) : null}
        </div>
      </section>
    </>
  );
}
