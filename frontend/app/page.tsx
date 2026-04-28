import Link from "next/link";
import type { ReactNode } from "react";

import { BikeCard } from "@/components/BikeCard";
import { getBikes, getBrands } from "@/lib/api";

type HomeProps = {
  searchParams?: Promise<{
    brand?: string;
    category?: string;
    usage_type?: string;
    keyword?: string;
    page?: string;
    page_size?: string;
  }>;
};

export default async function Home({ searchParams }: HomeProps) {
  const params = (await searchParams) ?? {};
  const page = toPositiveInt(params.page, 1);
  const pageSize = toPositiveInt(params.page_size, 20);
  const [brands, bikes] = await Promise.all([
    getBrands().catch(() => ({ items: [] })),
    getBikes({
      brand: params.brand,
      category: params.category,
      usage_type: params.usage_type,
      keyword: params.keyword,
      page,
      page_size: pageSize
    }).catch(() => ({
      items: [],
      pagination: { page: 1, page_size: pageSize, total: 0, total_pages: 0 },
      filters: {}
    }))
  ]);
  const pagination = bikes.pagination;
  const totalPages = pagination.total_pages;
  const currentPage = Math.min(pagination.page, Math.max(totalPages, 1));

  return (
    <>
      <section className="hero">
        <Ornament className="hero__decor hero__decor--top" />
        <div className="hero__inner">
          <span className="hero__subtitle">Road Bike Codex</span>
          <h1 className="hero__title">公路车数据圣典</h1>
          <p className="hero__lead">
            从五大品牌官网铸造而来：车型、价格、配置、几何与图片，统一收录于一卷。
            为追风者点亮信息盲区，为收藏家校准每一颗螺丝的来路。
          </p>
          <div className="hero__cta">
            <Link className="button button--primary" href="#bike-list">
              进入车型大厅
            </Link>
            <Link className="button button--ghost" href="/brands">
              查阅品牌图鉴
            </Link>
          </div>
          <div className="hero__stats">
            <div className="stat-tile">
              <strong>{brands.items.length}</strong>
              <span>已接入品牌</span>
            </div>
            <div className="stat-tile">
              <strong>{pagination.total}</strong>
              <span>标准化车型</span>
            </div>
            <div className="stat-tile">
              <strong>每日</strong>
              <span>定时同步</span>
            </div>
          </div>
        </div>
        <Ornament className="hero__decor hero__decor--bottom" />
      </section>

      <section className="section" id="bike-list">
        <header className="section-heading">
          <div>
            <span className="eyebrow">Catalog</span>
            <h2>公路车列阵</h2>
          </div>
          <span className="muted">{pagination.total} 件已收录</span>
        </header>

        <form className="filters" role="search">
          <select name="brand" defaultValue={params.brand ?? ""} aria-label="品牌">
            <option value="">全部品牌</option>
            {brands.items.map((brand) => (
              <option key={brand.slug} value={brand.slug}>
                {brand.name}
              </option>
            ))}
          </select>
          <select name="category" defaultValue={params.category ?? ""} aria-label="路况">
            <option value="">全部路况</option>
            <option value="ROAD">ROAD</option>
            <option value="CROSS/GRAVEL">CROSS / GRAVEL</option>
          </select>
          <select name="usage_type" defaultValue={params.usage_type ?? ""} aria-label="用途">
            <option value="">全部用途</option>
            <option value="PERFORMANCE">PERFORMANCE</option>
            <option value="SPORT">SPORT</option>
            <option value="LIFESTYLE">LIFESTYLE</option>
          </select>
          <input
            name="keyword"
            placeholder="TCR / Propel / Defy"
            defaultValue={params.keyword ?? ""}
            aria-label="关键词"
          />
          <select name="page_size" defaultValue={String(pageSize)} aria-label="每页">
            <option value="12">每页 12</option>
            <option value="20">每页 20</option>
            <option value="40">每页 40</option>
          </select>
          <button type="submit">出征</button>
        </form>

        {bikes.items.length > 0 ? (
          <div className="grid">
            {bikes.items.map((bike) => (
              <BikeCard key={bike.id} bike={bike} />
            ))}
          </div>
        ) : (
          <div className="empty-state">没有符合条件的战车</div>
        )}

        <nav className="pagination" aria-label="商品分页">
          <span className="pagination-summary">
            共 {pagination.total} 件 ·{" "}
            {totalPages > 0 ? `第 ${currentPage} / ${totalPages} 卷` : "暂无分页"}
          </span>
          <div className="pagination-actions">
            <PaginationLink
              disabled={currentPage <= 1}
              href={buildPageHref(params, currentPage - 1, pageSize)}
            >
              上一卷
            </PaginationLink>
            <PaginationLink
              disabled={totalPages === 0 || currentPage >= totalPages}
              href={buildPageHref(params, currentPage + 1, pageSize)}
            >
              下一卷
            </PaginationLink>
          </div>
        </nav>
      </section>
    </>
  );
}

function PaginationLink({
  children,
  disabled,
  href
}: {
  children: ReactNode;
  disabled: boolean;
  href: string;
}) {
  if (disabled) {
    return <span className="pagination-link disabled">{children}</span>;
  }
  return (
    <Link className="pagination-link" href={href}>
      {children}
    </Link>
  );
}

function Ornament({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 960 24"
      fill="none"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ornament-gold" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor="#d4a857" stopOpacity="0" />
          <stop offset="0.4" stopColor="#f8b700" stopOpacity="0.85" />
          <stop offset="0.5" stopColor="#fff5cd" stopOpacity="1" />
          <stop offset="0.6" stopColor="#f8b700" stopOpacity="0.85" />
          <stop offset="1" stopColor="#d4a857" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0 12H400" stroke="url(#ornament-gold)" strokeWidth="1" />
      <path d="M560 12H960" stroke="url(#ornament-gold)" strokeWidth="1" />
      <path
        d="M460 12L480 4L500 12L480 20Z"
        fill="#0d141d"
        stroke="#f8b700"
        strokeWidth="1"
      />
      <circle cx="480" cy="12" r="2" fill="#fff5cd" />
    </svg>
  );
}

function buildPageHref(
  params: NonNullable<Awaited<HomeProps["searchParams"]>>,
  page: number,
  pageSize: number
) {
  const query = new URLSearchParams();
  (["brand", "category", "usage_type", "keyword"] as const).forEach((key) => {
    const value = params[key];
    if (value) query.set(key, value);
  });
  if (page > 1) query.set("page", String(page));
  if (pageSize !== 20) query.set("page_size", String(pageSize));
  const queryString = query.toString();
  return queryString ? `/?${queryString}#bike-list` : "/#bike-list";
}

function toPositiveInt(value: string | undefined, fallback: number) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}
