import { Catalog, Product, StoreToggle } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getProducts(
  store?: string,
  year?: number,
  week?: number
): Promise<Product[]> {
  const url = new URL(`${API_URL}/api/products`);
  if (store) url.searchParams.set("store", store);
  if (year && week) {
    url.searchParams.set("year", String(year));
    url.searchParams.set("week", String(week));
  }

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load products: ${res.status}`);
  return res.json();
}

export async function getStores(): Promise<StoreToggle[]> {
  const res = await fetch(`${API_URL}/api/stores`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load stores: ${res.status}`);
  return res.json();
}

export async function getCatalogs(store?: string): Promise<Catalog[]> {
  const url = new URL(`${API_URL}/api/catalogs`);
  if (store) url.searchParams.set("store", store);

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load catalogs: ${res.status}`);
  return res.json();
}