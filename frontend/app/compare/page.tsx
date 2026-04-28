import { BikeCard } from "@/components/BikeCard";
import { getBike, getBikes } from "@/lib/api";

export default async function ComparePage({
  searchParams
}: {
  searchParams?: Promise<{ ids?: string }>;
}) {
  const params = (await searchParams) ?? {};
  const ids = params.ids?.split(",").filter(Boolean) ?? [];
  const bikes = ids.length
    ? await Promise.all(
        ids.slice(0, 4).map((id) => getBike(id).then((response) => response.data))
      )
    : [];
  const fallback = await getBikes({ page_size: 4 }).catch(() => ({ items: [] }));
  const display = bikes.length ? bikes : fallback.items;

  return (
    <>
      <section className="detail-hero">
        <span className="eyebrow">Compare</span>
        <h1>车型对决</h1>
        <p className="muted">
          通过 <code>?ids=1,2,3</code> 召唤至多 4 台战车同台比试，否则展示最新铸造的车型作为候选。
        </p>
      </section>

      <section className="section">
        {display.length > 0 ? (
          <div className="grid">
            {display.map((bike) => (
              <BikeCard key={bike.id} bike={bike} />
            ))}
          </div>
        ) : (
          <div className="empty-state">竞技场暂无车型</div>
        )}
      </section>
    </>
  );
}
