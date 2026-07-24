import { Product, StoreToggle } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getProducts(store?: string): Promise<Product[]> {
  const url = new URL(`${API_URL}/api/products`);
  if (store) url.searchParams.set("store", store);

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load products: ${res.status}`);
  return res.json();
}

export async function getStores(): Promise<StoreToggle[]> {
  const res = await fetch(`${API_URL}/api/stores`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load stores: ${res.status}`);
  return res.json();
}