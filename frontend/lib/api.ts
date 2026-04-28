const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Brand = {
  id: number;
  name: string;
  slug: string;
  country?: string | null;
  official_site_url?: string | null;
};

export type BikeListItem = {
  id: number;
  name: string;
  slug: string;
  model_year?: number | null;
  category?: string | null;
  usage_type?: string | null;
  price_min?: string | null;
  price_max?: string | null;
  currency?: string | null;
  official_url?: string | null;
  brand: Brand;
  cover_image_url?: string | null;
};

export type BikeDetail = BikeListItem & {
  description?: string | null;
  raw_summary?: Record<string, unknown> | null;
  series_name?: string | null;
  images: Array<{ id: number; image_url: string; image_type: string; position: number }>;
  variants: Array<{
    id: number;
    name: string;
    sku?: string | null;
    color_name?: string | null;
    price?: string | null;
    currency?: string | null;
  }>;
  components: Array<{
    id: number;
    category?: string | null;
    component_name: string;
    component_value: string;
    sort_order: number;
  }>;
};

export type Page<T> = {
  items: T[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
  filters: Record<string, unknown>;
};

export async function getBrands(): Promise<{ items: Brand[] }> {
  return getJson("/api/brands");
}

export async function getBikes(params: Record<string, string | number | undefined> = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return getJson<Page<BikeListItem>>(`/api/bikes?${query}`);
}

export async function getBike(id: string | number): Promise<{ data: BikeDetail }> {
  return getJson(`/api/bikes/${id}`);
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    next: { revalidate: 60 }
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}
