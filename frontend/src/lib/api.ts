import { Catalog, Product, StoreToggle, AllergyToggle } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ConfigSettings {
  gemini_api_key_set: boolean;
  gemini_api_key_preview: string | null;
  postal_code: string;
  email_to: string;
  discord_webhook_url: string;
  webhook_enabled: boolean;
  smtp_enabled: boolean;
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  weekly_budget: string;
}

export interface SettingsResponse {
  stores: StoreToggle[];
  allergies: AllergyToggle[];
  staples: [];
  config: ConfigSettings;
}

export interface SettingsPatchPayload {
  stores?: Record<string, boolean>;
  allergies?: Record<string, boolean>;
  gemini_api_key?: string;
}

export async function getSettings(): Promise<SettingsResponse> {
  const res = await fetch(`${API_URL}/api/settings`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load settings: ${res.status}`);
  return res.json();
}

export async function testNotification(channel: 'email' | 'discord'): Promise<{ success: boolean }> {
  const res = await fetch(`${API_URL}/api/settings/test-notification`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channel }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Ukjent feil' }));
    throw new Error(err.detail ?? 'Klarte ikke å sende testvarsel');
  }
  return res.json();
}

export async function patchSettings(
  payload: SettingsPatchPayload
): Promise<SettingsResponse> {
  const res = await fetch(`${API_URL}/api/settings`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to update settings: ${res.status}`);
  return res.json();
}

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