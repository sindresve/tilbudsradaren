"use client";

import { useEffect, useState } from "react";
import { getProducts, getStores } from "@/lib/api";
import { Product, StoreToggle } from "@/types";
import Navbar from "@/components/Navbar";
import Modal from "@/components/SettingsModal";

const STORE_LABELS: Record<string, string> = {
  rema: "REMA 1000",
  kiwi: "Kiwi",
  coopExtra: "Coop Extra",
};

function storeLabel(store: string): string {
  return STORE_LABELS[store] ?? store;
}

function formatPrice(value: number | null): string {
  if (value === null) return "Ingen pris oppgitt";
  if (value === 0.00) return "Ingen pris oppgitt";
  return `${value.toFixed(2)} kr`;
}

function effectiveDiscount(p: Product): number | null {
  if (p.discount_percent !== null) return Math.round(p.discount_percent);
  return discountPercent(p.current_price, p.old_price);
}

function discountPercent(current: number | null, old: number | null): number | null {
  if (current === null || old === null || old <= 0) return null;
  return Math.round(100 - (current / old) * 100);
}

type SortOption = "none" | "price-asc" | "price-desc";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [stores, setStores] = useState<StoreToggle[]>([]);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  // Sidebar filters
  const [selectedStores, setSelectedStores] = useState<Set<string>>(new Set());
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");

  // Top bar filters
  const [onSaleOnly, setOnSaleOnly] = useState(false);
  const [sortOption, setSortOption] = useState<SortOption>("none");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStores()
      .then((s) => {
        setStores(s);
        // Default: all enabled stores selected.
        setSelectedStores(new Set(s.filter((x) => x.enabled).map((x) => x.store)));
      })
      .catch(() => {
        // Store list is optional decoration for the filter bar — fail quietly.
      });
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    // Fetch everything once; store/category filtering happens client-side alongside the other filters.
    getProducts()
      .then(setProducts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const now = new Date();

  function toggleStore(store: string) {
    setSelectedStores((prev) => {
      const next = new Set(prev);
      if (next.has(store)) {
        next.delete(store);
      } else {
        next.add(store);
      }
      return next;
    });
  }

  function toggleCategory(category: string) {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }

  // Categories present in the current result set, for the category checkbox list.
  const categories = Array.from(
    new Set(products.map((p) => p.category).filter((c): c is string => Boolean(c)))
  ).sort((a, b) => a.localeCompare(b, "nb"));

  // Default all categories to checked once we know what they are (only runs once,
  // right after products first load — after that the user's own choices take over).
  useEffect(() => {
    if (categories.length > 0 && selectedCategories.size === 0 && !loading) {
      setSelectedCategories(new Set(categories));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const min = minPrice.trim() === "" ? null : Number(minPrice);
  const max = maxPrice.trim() === "" ? null : Number(maxPrice);

  const visibleProducts = products
    .filter((p) => selectedStores.size === 0 || selectedStores.has(p.store))
    .filter((p) => {
      // While categories haven't been seeded yet (or there are none), don't filter.
      if (categories.length === 0 || selectedCategories.size === 0) return true;
      return p.category !== null && selectedCategories.has(p.category);
    })
    .filter((p) => {
      if (!onSaleOnly) return true;
      const pct = effectiveDiscount(p);
      return pct !== null && pct > 0;
    })
    .filter((p) => {
      if (min !== null && (p.current_price === null || p.current_price < min)) return false;
      if (max !== null && (p.current_price === null || p.current_price > max)) return false;
      return true;
    })
    .filter((p) => {
      if (!search.trim()) return true;
      const q = search.trim().toLowerCase();
      return (
        p.product_name.toLowerCase().includes(q) ||
        (p.brand ?? "").toLowerCase().includes(q)
      );
    })
    .sort((a, b) => {
      if (sortOption === "price-asc") {
        return (a.current_price ?? Infinity) - (b.current_price ?? Infinity);
      }
      if (sortOption === "price-desc") {
        return (b.current_price ?? -Infinity) - (a.current_price ?? -Infinity);
      }
      return 0;
    });

    const handleOpen = () => {
      setSettingsModalOpen(true);
    };

    const handleClose = () => {
      setSettingsModalOpen(false);
    };

  const filtersActive =
    minPrice ||
    maxPrice ||
    selectedCategories.size !== categories.length ||
    selectedStores.size !== stores.filter((s) => s.enabled).length;

  return (
    <main className="min-h-screen bg-[#f6f3ec] text-[#1c1a16]">
      <Navbar setModalOpen={handleOpen} />
      <Modal isOpen={settingsModalOpen} onClose={handleClose} />
      <div className="mx-auto max-w-6xl px-6 py-8 sm:px-10">
        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Left sidebar */}
          <aside className="shrink-0 lg:w-64">
            <div className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
              <h3 className="text-sm font-semibold">Butikker</h3>
              <div className="mt-3 flex flex-col gap-2">
                {stores.map((s) => (
                  <label
                    key={s.store}
                    className="flex cursor-pointer items-center gap-2 text-sm text-[#1c1a16]/80"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStores.has(s.store)}
                      onChange={() => toggleStore(s.store)}
                      className="h-4 w-4 rounded border-[#1c1a16]/30 accent-[#8a5a3d]"
                    />
                    {storeLabel(s.store)}
                  </label>
                ))}
                {stores.length === 0 && (
                  <p className="text-xs text-[#1c1a16]/40">Ingen butikker funnet.</p>
                )}
              </div>

              <h3 className="mt-6 text-sm font-semibold">Kategori</h3>
              <div className="mt-3 flex flex-col gap-2">
                {categories.map((c) => (
                  <label
                    key={c}
                    className="flex cursor-pointer items-center gap-2 text-sm capitalize text-[#1c1a16]/80"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCategories.has(c)}
                      onChange={() => toggleCategory(c)}
                      className="h-4 w-4 rounded border-[#1c1a16]/30 accent-[#8a5a3d]"
                    />
                    {c}
                  </label>
                ))}
                {categories.length === 0 && (
                  <p className="text-xs text-[#1c1a16]/40">Ingen kategorier funnet.</p>
                )}
              </div>

              <h3 className="mt-6 text-sm font-semibold">Pris</h3>
              <div className="mt-3 flex items-center gap-2">
                <input
                  type="number"
                  min={0}
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  placeholder="Min"
                  className="w-full rounded-lg border border-[#1c1a16]/15 px-2 py-1.5 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />
                <span className="text-[#1c1a16]/30">–</span>
                <input
                  type="number"
                  min={0}
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  placeholder="Max"
                  className="w-full rounded-lg border border-[#1c1a16]/15 px-2 py-1.5 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>

              {filtersActive && (
                <button
                  onClick={() => {
                    setMinPrice("");
                    setMaxPrice("");
                    setSelectedCategories(new Set(categories));
                    setSelectedStores(new Set(stores.filter((s) => s.enabled).map((s) => s.store)));
                  }}
                  className="mt-4 text-xs font-medium text-[#8a5a3d] hover:underline"
                >
                  Nullstill filtre
                </button>
              )}
            </div>
          </aside>

          {/* Right side */}
          <div className="min-w-0 flex-1">
            {/* Search + sale toggle + sort */}
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Søk etter produkt eller merke …"
                className="min-w-[200px] flex-1 rounded-lg border border-[#1c1a16]/15 bg-white px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
              />

              <button
                onClick={() => setOnSaleOnly((v) => !v)}
                className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                  onSaleOnly
                    ? "border-[#8a5a3d] bg-[#8a5a3d] text-white"
                    : "border-[#1c1a16]/20 text-[#1c1a16]/70 hover:border-[#1c1a16]/40"
                }`}
              >
                Kun tilbud
              </button>

              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value as SortOption)}
                className="shrink-0 rounded-full border border-[#1c1a16]/20 bg-white px-4 py-2 text-sm font-medium text-[#1c1a16]/70 focus:border-[#1c1a16]/40 focus:outline-none"
              >
                <option value="none">Sortering</option>
                <option value="price-asc">Pris: lav til høy</option>
                <option value="price-desc">Pris: høy til lav</option>
              </select>
            </div>

            {/* States */}
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

            {!loading && !error && products.length > 0 && visibleProducts.length === 0 && (
              <p className="py-16 text-center text-sm text-[#1c1a16]/50">
                Ingen produkter matcher filtrene dine.
              </p>
            )}

            {/* Product grid */}
            {!loading && !error && visibleProducts.length > 0 && (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {visibleProducts.map((p) => {
                  const pct = effectiveDiscount(p);
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
                          <span className="text-sm text-[#1c1a16]/40 line-through">
                            {p.old_price !== null && p.old_price !== 0.00 && (
                                p.old_price
                            )}
                          </span>
                      </div>

                      <div className="mt-1 flex justify-between text-xs text-[#1c1a16]/40">
                        <span>{p.package_size ?? ""}</span>
                        {p.price_per_kg !== null && (
                          <span>{p.price_per_kg}/{p.unit_type ?? "kg"}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}