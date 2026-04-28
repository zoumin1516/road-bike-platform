import Link from "next/link";

import { BikeGallery } from "@/components/BikeGallery";
import { getBike } from "@/lib/api";

type BikeDetailProps = {
  params: Promise<{ id: string }>;
};

export default async function BikeDetailPage({ params }: BikeDetailProps) {
  const { id } = await params;
  const { data: bike } = await getBike(id);
  const galleryImages = bike.images.map((image) => ({
    id: image.id,
    image_url: image.image_url
  }));
  const groupedComponents = groupByCategory(bike.components);
  const meta = [bike.series_name, bike.model_year, bike.category, bike.usage_type]
    .filter(Boolean)
    .join(" · ");
  const priceLabel = bike.price_min ? `${bike.currency ?? ""} ${bike.price_min}` : "价格待铸";

  return (
    <>
      <section className="detail-hero">
        <span className="eyebrow">{bike.brand.name}</span>
        <h1>{bike.name}</h1>
        {meta ? <p className="muted">{meta}</p> : null}
      </section>

      <div className="detail-layout">
        <BikeGallery images={galleryImages} alt={bike.name} />

        <section className="detail-panel">
          <span className="eyebrow">Specification</span>
          <h1>{bike.name}</h1>
          <p className="muted">{meta || "尚未归档"}</p>
          <div className="card-price" style={{ marginTop: 18 }}>
            {priceLabel}
          </div>
          {bike.description ? <p>{bike.description}</p> : null}
          {bike.official_url ? (
            <p>
              <Link
                className="button button--ghost"
                href={bike.official_url}
                target="_blank"
                rel="noreferrer"
              >
                查阅官网原卷
              </Link>
            </p>
          ) : null}

          {bike.variants.length > 0 ? (
            <>
              <h2 style={{ marginTop: 32 }}>颜色 · 变体</h2>
              <ul className="variant-list">
                {bike.variants.map((variant) => (
                  <li key={variant.id}>{variant.color_name || variant.name}</li>
                ))}
              </ul>
            </>
          ) : null}

          {Object.keys(groupedComponents).length > 0 ? (
            <>
              <h2 style={{ marginTop: 36 }}>规格配置</h2>
              {Object.entries(groupedComponents).map(([category, components]) => (
                <div key={category} style={{ marginBottom: 24 }}>
                  <h3 style={{ color: "var(--gold-200)" }}>{category}</h3>
                  <table className="spec-table">
                    <tbody>
                      {components.map((component) => (
                        <tr key={component.id}>
                          <td>{component.component_name}</td>
                          <td>{component.component_value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </>
          ) : null}
        </section>
      </div>
    </>
  );
}

function groupByCategory<T extends { category?: string | null }>(items: T[]) {
  return items.reduce<Record<string, T[]>>((acc, item) => {
    const key = item.category || "其他";
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}
