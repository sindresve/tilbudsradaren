export interface Product {
  id: number;
  product_name: string;
  brand: string | null;
  category: string | null;
  current_price: number | null;
  old_price: number | null;
  price_per_kg: number | null;
  unit_type: string | null;
  package_size: string | null;
  source_image: string | null;
  store: string;
  year: number;
  week: number;
  catalog_created_at: string;
}

export interface StoreToggle {
  store: string;
  enabled: number; // sqlite boolean: 0 or 1
}