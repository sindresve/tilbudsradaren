"use client";

import { useEffect, useState } from "react";
import { getProducts, getStores } from "@/lib/api";
import { Product, StoreToggle } from "@/types";

const STORE_LABELS: Record<string, string> = {
  rema: "REMA 1000",
  kiwi: "Kiwi",
  coopExtra: "Coop Extra",
};

function storeLabel(store: string): string {
  return STORE_LABELS[store] ?? store;
}

function formatPrice(value: number | null): string {
  if (value === null) return "—";
  return `${value.toFixed(2)} kr`;
}

function discountPercent(current: number | null, old: number | null): number | null {
  if (current === null || old === null || old <= 0) return null;
  return Math.round(100 - (current / old) * 100);
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [stores, setStores] = useState<StoreToggle[]>([]);
  const [activeStore, setActiveStore] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStores()
      .then(setStores)
      .catch(() => {
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getProducts(activeStore)
      .then(setProducts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [activeStore]);

  const now = new Date();

  return (
    <main className="min-h-screen bg-[#f6f3ec] text-[#1c1a16]">
      <header className="border-b-2 border-dashed border-[#1c1a16]/20 px-6 py-8 sm:px-10">
        <div className="mx-auto max-w-6xl">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-[#8a5a3d]">
            Ukens tilbud
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
            Tilbudsradaren
          </h1>
          <p className="mt-2 text-sm text-[#1c1a16]/60">
            {now.toLocaleDateString("nb-NO", { weekday: "long", day: "numeric", month: "long" })}
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-8 sm:px-10">
        <div className="mb-8 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveStore(undefined)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
              activeStore === undefined
                ? "border-[#1c1a16] bg-[#1c1a16] text-[#f6f3ec]"
                : "border-[#1c1a16]/20 text-[#1c1a16]/70 hover:border-[#1c1a16]/40"
            }`}
          >
            Alle butikker
          </button>
          {stores
            .filter((s) => s.enabled)
            .map((s) => (
              <button
                key={s.store}
                onClick={() => setActiveStore(s.store)}
                className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
                  activeStore === s.store
                    ? "border-[#1c1a16] bg-[#1c1a16] text-[#f6f3ec]"
                    : "border-[#1c1a16]/20 text-[#1c1a16]/70 hover:border-[#1c1a16]/40"
                }`}
              >
                {storeLabel(s.store)}
              </button>
            ))}
        </div>

        {loading && (
          <p className="py-16 text-center text-sm text-[#1c1a16]/50">Henter tilbud …</p>
        )}

        {error && !loading && (
          <div className="rounded-lg border border-[#8a5a3d]/30 bg-[#8a5a3d]/5 px-4 py-3 text-sm text-[#8a5a3d]">
            Klarte ikke å hente data fra serveren. Kjører API-et på port 8000?
            <br />
            <span className="font-mono text-xs">{error}</span>
          </div>
        )}

        {!loading && !error && products.length === 0 && (
          <p className="py-16 text-center text-sm text-[#1c1a16]/50">
            Ingen tilbud funnet for denne uken ennå.
          </p>
        )}

        {!loading && !error && products.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((p) => {
              const pct = discountPercent(p.current_price, p.old_price);
              return (
                <div
                  key={p.id}
                  className="group relative overflow-hidden rounded-lg border border-[#1c1a16]/10 bg-white px-4 py-4 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-mono text-[10px] uppercase tracking-wider text-[#1c1a16]/40">
                        {storeLabel(p.store)}
                        {p.category ? ` · ${p.category}` : ""}
                      </p>
                      <h2 className="mt-1 truncate font-semibold leading-snug">
                        {p.product_name}
                      </h2>
                      {p.brand && (
                        <p className="text-xs text-[#1c1a16]/50">{p.brand}</p>
                      )}
                    </div>
                    {pct !== null && pct > 0 && (
                      <span className="shrink-0 rounded-full bg-[#8a5a3d] px-2 py-1 font-mono text-xs font-bold text-white">
                        -{pct}%
                      </span>
                    )}
                  </div>

                  <div className="mt-3 flex items-baseline gap-2 border-t border-dashed border-[#1c1a16]/10 pt-3">
                    <span className="text-xl font-bold">
                      {formatPrice(p.current_price)}
                    </span>
                    {p.old_price !== null && (
                      <span className="text-sm text-[#1c1a16]/40 line-through">
                        {formatPrice(p.old_price)}
                      </span>
                    )}
                  </div>

                  <div className="mt-1 flex justify-between text-xs text-[#1c1a16]/40">
                    <span>{p.package_size ?? ""}</span>
                    {p.price_per_kg !== null && (
                      <span>{formatPrice(p.price_per_kg)}/{p.unit_type ?? "kg"}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}