"use client";

import { useEffect, useState } from "react";
import { getProducts, getStores, getCatalogs } from "@/lib/api";
import { Product, StoreToggle, Catalog } from "@/types";
import { STORE_LABELS } from "@/lib/constants";
import Navbar from "@/components/Navbar";
import Modal from "@/components/SettingsModal";
import ProductModal from "@/components/ProductModal";
import AiSuggestionModal from "@/components/AISuggestionModal";
import { Plus, RotateCcw, ShoppingCart } from "lucide-react";
import ShoppingListSidebar from "@/components/ShoppingListSidebar";
import ImportShoppingListModal from "@/components/ImportModal";

function storeLabel(store: string): string {
  return STORE_LABELS[store] ?? store;
}

function formatPrice(value: number | null): string {
  if (value === null) return "Ingen pris oppgitt";
  if (value === 0.0) return "Ingen pris oppgitt";
  return `${value.toFixed(2)} kr`;
}

function effectiveDiscount(p: Product): number | null {
  if (p.discount_percent !== null && p.discount_percent !== 0) {
    return Math.round(p.discount_percent);
  }
  return discountPercent(p.current_price, p.old_price);
}

function discountPercent(
  current: number | null,
  old: number | null
): number | null {
  if (current === null || old === null || old <= 0) return null;
  return Math.round(100 - (current / old) * 100);
}

function getIsoWeek(date: Date): { year: number; week: number } {
  const d = new Date(
    Date.UTC(date.getFullYear(), date.getMonth(), date.getDate())
  );
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7
  );
  return { year: d.getUTCFullYear(), week };
}

function getNextMondayAt8(): Date {
  const now = new Date();
  const next = new Date(now);
  next.setHours(8, 0, 0, 0);

  const dayOfWeek = now.getDay();
  let daysUntilMonday = (1 - dayOfWeek + 7) % 7;

  if (daysUntilMonday === 0 && now.getTime() >= next.getTime()) {
    daysUntilMonday = 7;
  }

  next.setDate(now.getDate() + daysUntilMonday);
  return next;
}

type SortOption =
  | "none"
  | "price-asc"
  | "price-desc"
  | "discount-desc"
  | "discount-asc"
  | "name-asc"
  | "name-desc"
  | "store-asc"
  | "category-asc";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [stores, setStores] = useState<StoreToggle[]>([]);
  const [availableWeeks, setAvailableWeeks] = useState<Catalog[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<{
    year: number;
    week: number;
  } | null>(null);

  // Modals
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [aiModalOpen, setAiModalOpen] = useState(false);

  // Shopping list
  const [shoppingListOpen, setShoppingListOpen] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [shoppingList, setShoppingList] = useState<Product[]>([]);

  // Sidebar filters
  const [selectedStores, setSelectedStores] = useState<Set<string>>(new Set());
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");

  // Program status
  const [isRunning, setIsRunning] = useState(false);
  const [nextScan, setNextScan] = useState<Date | null>(null);
  const [timeUntilScan, setTimeUntilScan] = useState<string>("--:--:--");

  // Top bar filters
  const [onSaleOnly, setOnSaleOnly] = useState(true);
  const [sortOption, setSortOption] = useState<SortOption>("none");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isRunning || !nextScan) {
      setTimeUntilScan("--:--:--");
      return;
    }

    const tick = () => {
      const diff = nextScan.getTime() - Date.now();
      if (diff <= 0) {
        setTimeUntilScan("00:00:00");
        return;
      }
      const h = Math.floor(diff / 3_600_000);
      const m = Math.floor((diff % 3_600_000) / 60_000);
      const s = Math.floor((diff % 60_000) / 1000);
      setTimeUntilScan(
        `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
      );
    };

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [isRunning, nextScan]);

  function handleToggleRunning() {
    if (isRunning) {
      setIsRunning(false);
      setNextScan(null);
      return;
    }
    setIsRunning(true);
    setNextScan(getNextMondayAt8());
  }

  useEffect(() => {
    getStores()
      .then((s) => {
        setStores(s);
        setSelectedStores(
          new Set(s.filter((x) => x.enabled).map((x) => x.store))
        );
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getProducts(undefined, selectedWeek?.year, selectedWeek?.week)
      .then(setProducts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedWeek]);

  useEffect(() => {
    getCatalogs()
      .then(setAvailableWeeks)
      .catch(() => {});
  }, []);

  function addToShoppingList(product: Product) {
    setShoppingList((prev) => {
      if (prev.some((p) => p.id === product.id)) {
        return prev;
      }
      return [...prev, product];
    });
  }

  function removeFromShoppingList(id: number) {
    setShoppingList((prev) => prev.filter((p) => p.id !== id));
  }

  function importToShoppingList(matched: Product[]) {
    setShoppingList((prev) => {
      const existingIds = new Set(prev.map((p) => p.id));
      const newOnes = matched.filter((p) => !existingIds.has(p.id));
      return [...prev, ...newOnes];
    });
  }

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

  const categories = Array.from(
    new Set(
      products
        .map((p) => p.category)
        .filter((c): c is string => Boolean(c))
    )
  ).sort((a, b) => a.localeCompare(b, "nb"));

  useEffect(() => {
    if (categories.length > 0 && selectedCategories.size === 0 && !loading) {
      setSelectedCategories(new Set(categories));
    }
  }, [loading]);

  const min = minPrice.trim() === "" ? null : Number(minPrice);
  const max = maxPrice.trim() === "" ? null : Number(maxPrice);

  const productsBeforeStoreFilter = products
    .filter((p) => {
      if (categories.length === 0 || selectedCategories.size === 0) return true;
      return p.category !== null && selectedCategories.has(p.category);
    })
    .filter((p) => {
      if (!onSaleOnly) return true;
      const pct = effectiveDiscount(p);
      return pct !== null && pct > 0;
    })
    .filter((p) => {
      if (min !== null && (p.current_price === null || p.current_price < min))
        return false;
      if (max !== null && (p.current_price === null || p.current_price > max))
        return false;
      return true;
    })
    .filter((p) => {
      if (!search.trim()) return true;
      const q = search.trim().toLowerCase();
      return (
        p.product_name.toLowerCase().includes(q) ||
        (p.brand ?? "").toLowerCase().includes(q)
      );
    });

  const storeCounts = new Map<string, number>();

  const productsBeforeCategoryFilter = products
    .filter((p) => selectedStores.size === 0 || selectedStores.has(p.store))
    .filter((p) => {
      if (!onSaleOnly) return true;
      const pct = effectiveDiscount(p);
      return pct !== null && pct > 0;
    })
    .filter((p) => {
      if (min !== null && (p.current_price === null || p.current_price < min))
        return false;
      if (max !== null && (p.current_price === null || p.current_price > max))
        return false;
      return true;
    })
    .filter((p) => {
      if (!search.trim()) return true;
      const q = search.trim().toLowerCase();
      return (
        p.product_name.toLowerCase().includes(q) ||
        (p.brand ?? "").toLowerCase().includes(q)
      );
    });

  const categoryCounts = new Map<string, number>();

  productsBeforeCategoryFilter.forEach((p) => {
    if (!p.category) return;
    categoryCounts.set(
      p.category,
      (categoryCounts.get(p.category) ?? 0) + 1
    );
  });

  const weekOptions = Array.from(
    new Map(
      availableWeeks.map((c) => [
        `${c.year}-${c.week}`,
        { year: c.year, week: c.week },
      ])
    ).values()
  ).sort((a, b) => b.year - a.year || b.week - a.week);

  productsBeforeStoreFilter.forEach((p) => {
    storeCounts.set(p.store, (storeCounts.get(p.store) ?? 0) + 1);
  });

  const visibleProducts = products
    .filter((p) => selectedStores.size === 0 || selectedStores.has(p.store))
    .filter((p) => {
      if (categories.length === 0 || selectedCategories.size === 0) return true;
      return p.category !== null && selectedCategories.has(p.category);
    })
    .filter((p) => {
      if (!onSaleOnly) return true;
      const pct = effectiveDiscount(p);
      return pct !== null && pct > 0;
    })
    .filter((p) => {
      if (min !== null && (p.current_price === null || p.current_price < min))
        return false;
      if (max !== null && (p.current_price === null || p.current_price > max))
        return false;
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
      switch (sortOption) {
        case "price-asc":
          return (a.current_price ?? Infinity) - (b.current_price ?? Infinity);
        case "price-desc":
          return (b.current_price ?? -Infinity) - (a.current_price ?? -Infinity);
        case "discount-desc":
          return (effectiveDiscount(b) ?? -1) - (effectiveDiscount(a) ?? -1);
        case "discount-asc":
          return (effectiveDiscount(a) ?? 999) - (effectiveDiscount(b) ?? 999);
        case "name-asc":
          return a.product_name.localeCompare(b.product_name, "nb");
        case "name-desc":
          return b.product_name.localeCompare(a.product_name, "nb");
        case "store-asc":
          return storeLabel(a.store).localeCompare(storeLabel(b.store), "nb");
        case "category-asc":
          return (a.category ?? "").localeCompare(b.category ?? "", "nb");
        default:
          return 0;
      }
    });

  const handleOpen = () => {
    setSettingsModalOpen(true);
  };

  const handleClose = () => {
    setSettingsModalOpen(false);
    getStores()
      .then((s) => setStores(s))
      .catch(() => {});
  };

  const handleOpenProductModal = (product: Product) => {
    setProductModalOpen(true);
    setSelectedProduct(product);
  };

  const handleCloseProductModal = () => {
    setProductModalOpen(false);
  };

  function handleDownloadDealsData() {
    const exportData = visibleProducts.map((p) => ({
      butikk: storeLabel(p.store),
      navn: p.product_name,
      merke: p.brand,
      kategori: p.category,
      pris: p.current_price,
      for_pris: p.old_price,
      rabatt_prosent: effectiveDiscount(p),
      pakningsstorrelse: p.package_size,
      pris_per_enhet: p.price_per_kg,
      enhet: p.unit_type,
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const { year, week } = selectedWeek ?? getIsoWeek(new Date());
    a.href = url;
    a.download = `tilbud-uke-${week}-${year}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const filtersActive =
    minPrice ||
    maxPrice ||
    selectedCategories.size !== categories.length ||
    selectedStores.size !== stores.filter((s) => s.enabled).length;

  return (
    <main
      className={`h-full flex flex-col bg-[#f6f3ec] text-[#1c1a16] transition-all duration-300 ${
        shoppingListOpen ? "lg:mr-44" : ""
      }`}
    >
      <Navbar
        setModalOpen={handleOpen}
        setAiModalOpen={() => setAiModalOpen(true)}
        setShoppingListOpen={() => setShoppingListOpen(!shoppingListOpen)}
        itemsAmount={shoppingList.length}
      />
      <Modal isOpen={settingsModalOpen} onClose={handleClose} />
      <ProductModal
        isOpen={productModalOpen}
        onClose={handleCloseProductModal}
        p={selectedProduct!}
      />
      <AiSuggestionModal
        isOpen={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        onDownloadData={handleDownloadDealsData}
      />
      <div className="w-full relative px-6 py-8 sm:px-10">
        <ShoppingListSidebar
          open={shoppingListOpen}
          onClose={() => setShoppingListOpen(false)}
          products={shoppingList}
          onRemove={removeFromShoppingList}
          onOpenImport={() => setImportModalOpen(true)}
        />
        <ImportShoppingListModal
          open={importModalOpen}
          onClose={() => setImportModalOpen(false)}
          allProducts={products}
          onImport={importToShoppingList}
        />

        <div className="mx-auto max-w-7xl w-full">
          <div className="flex flex-col gap-8 lg:flex-row">
            {/* Left sidebar */}
            <aside className="shrink-0 lg:w-64 flex flex-col gap-2">
              <div className="rounded-xl relative border border-[#1c1a16]/10 bg-white p-5 pt-3.5 h-full max-h-[70vh] flex flex-col">
                <div className="flex items-center justify-between h-7">
                  <h3 className="text-sm font-semibold">Butikker</h3>
                  {filtersActive && (
                    <button
                      onClick={() => {
                        setMinPrice("");
                        setMaxPrice("");
                        setSelectedCategories(new Set(categories));
                        setSelectedStores(
                          new Set(
                            stores
                              .filter((s) => s.enabled)
                              .map((s) => s.store)
                          )
                        );
                      }}
                      title="Nullstill filtre"
                      className="rounded-full p-1.5 cursor-pointer hover:bg-[#1c1a16]/5 transition-colors"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className="mt-3 flex flex-col gap-2 max-h-[29.5vh] overflow-y-scroll custom-scrollbar pb-2">
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
                      {storeLabel(s.store)} ({storeCounts.get(s.store) ?? 0})
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
                      {c} ({categoryCounts.get(c) ?? 0})
                    </label>
                  ))}
                  {categories.length === 0 && (
                    <p className="text-xs text-[#1c1a16]/40">Ingen kategorier funnet.</p>
                  )}
                </div>

                <div className="mt-auto">
                  <h3 className="text-sm font-semibold">Pris</h3>
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
                </div>
              </div>
              <div className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
                <h3 className="text-sm font-semibold">Info</h3>
                <div className="flex flex-col gap-3 pt-4">
                  <div className="flex items-center justify-between text-xs text-[#1c1a16]/50">
                    <span>Uke</span>
                    <span className="font-mono font-semibold text-[#1c1a16]/80">
                      {getIsoWeek(new Date()).week}, {getIsoWeek(new Date()).year}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#1c1a16]/50">
                    <span>Neste scan om</span>
                    <span className="font-mono font-semibold text-[#1c1a16]/80">
                      {timeUntilScan}
                    </span>
                  </div>

                  <button
                    onClick={handleToggleRunning}
                    className={`mt-1 w-full rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                      isRunning
                        ? "bg-[#1c1a16]/5 text-[#8a5a3d] hover:bg-[#1c1a16]/10"
                        : "bg-[#8a5a3d] text-white hover:bg-[#7a4d33]"
                    }`}
                  >
                    {isRunning ? "Stopp" : "Start"}
                  </button>
                </div>
              </div>
            </aside>

            {/* Right side */}
            <div className="min-w-0 flex-1">
              <div className="mb-4 flex flex-wrap items-center gap-3 pr-4">
                <select
                  value={
                    selectedWeek
                      ? `${selectedWeek.year}-${selectedWeek.week}`
                      : "current"
                  }
                  onChange={(e) => {
                    if (e.target.value === "current") {
                      setSelectedWeek(null);
                      return;
                    }
                    const [year, week] = e.target.value.split("-").map(Number);
                    setSelectedWeek({ year, week });
                  }}
                  className="shrink-0 rounded-lg border border-[#1c1a16]/20 bg-white px-4 py-2 text-sm font-medium text-[#1c1a16]/70 focus:border-[#1c1a16]/40 focus:outline-none"
                >
                  <option value="current">Denne uken</option>
                  {weekOptions.map(({ year, week }) => (
                    <option key={`${year}-${week}`} value={`${year}-${week}`}>
                      Uke {week}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Søk etter produkt eller merke …"
                  className="min-w-50 flex-1 rounded-lg border border-[#1c1a16]/15 bg-white px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />

                <button
                  onClick={() => setOnSaleOnly((v) => !v)}
                  className={`shrink-0 rounded-lg cursor-pointer px-4 py-2 text-sm font-medium transition-colors ${
                    onSaleOnly
                      ? "bg-[#8a5a3d] text-white"
                      : "outline outline-[#1c1a16]/20 text-[#1c1a16]/70 hover:outline-[#1c1a16]/40"
                  }`}
                >
                  Kun tilbud
                </button>

                <select
                  value={sortOption}
                  onChange={(e) => setSortOption(e.target.value as SortOption)}
                  className="shrink-0 rounded-lg cursor-pointer border border-[#1c1a16]/20 bg-white px-4 py-2 text-sm font-medium text-[#1c1a16]/70 focus:border-[#1c1a16]/40 focus:outline-none"
                >
                  <option value="none">Standard</option>
                  <option value="price-asc">Pris: lav → høy</option>
                  <option value="price-desc">Pris: høy → lav</option>
                  <option value="discount-desc">Størst rabatt</option>
                  <option value="discount-asc">Minst rabatt</option>
                  <option value="name-asc">Navn: A → Å</option>
                  <option value="name-desc">Navn: Å → A</option>
                  <option value="store-asc">Butikk: A → Å</option>
                  <option value="category-asc">Kategori: A → Å</option>
                </select>
              </div>

              <p className="mb-4 text-sm text-[#1c1a16]/50">
                Viser{" "}
                <span className="font-semibold">{visibleProducts.length}</span> av{" "}
                <span className="font-semibold">{products.length}</span> produkter
              </p>

              {/* States */}
              {loading && (
                <p className="py-16 text-center text-sm text-[#1c1a16]/50">
                  Henter tilbud …
                </p>
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
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 overflow-y-scroll custom-scrollbar max-h-[calc(81vh+4px)] pb-4 p-0.5 pr-1">
                  {visibleProducts.map((p) => {
                    const pct = effectiveDiscount(p);
                    return (
                      <div
                        key={p.id}
                        onClick={() => handleOpenProductModal(p)}
                        className="group relative cursor-pointer overflow-hidden rounded-xl border border-[#1c1a16]/10 bg-white px-4 py-4 transition-all duration-150 hover:outline hover:outline-[#8a5a3d]"
                      >
                        {/* Add to shopping list button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            addToShoppingList(p);
                          }}
                          className="absolute right-3 top-3 flex items-center justify-center bg-[#8a5a3d] rounded-full p-1.5 text-white opacity-0 translate-y-1 transition-all duration-200 hover:bg-[#7a4d33] group-hover:opacity-100 group-hover:translate-y-0"
                          title="Legg til i handleliste"
                        >
                          <Plus size={13} strokeWidth={2.5} />
                        </button>

                        {/* Header */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-mono text-[10px] uppercase tracking-wider text-[#1c1a16]/40">
                              {storeLabel(p.store)}
                              {p.category ? ` · ${p.category}` : ""}
                            </p>
                            <h2 className="mt-1 truncate font-semibold leading-snug text-[#1c1a16]">
                              {p.product_name}
                            </h2>
                            <span className="text-xs text-[#1c1a16]/40">{p.package_size ?? ""}</span>
                          </div>

                        </div>

                        {/* Price */}
                        <div className="mt-3 flex items-baseline justify-between gap-2 relative border-t w-full border-dashed border-[#1c1a16]/10 pt-3">
                          <div className="flex items-baseline gap-2">
                            <span className="text-xl font-bold text-[#1c1a16]">
                              {formatPrice(p.current_price)}
                            </span>
                            {p.old_price !== null && p.old_price !== 0.0 && (
                              <span className="text-sm text-[#1c1a16]/40 line-through">
                                {formatPrice(p.old_price)}
                              </span>
                            )}
                          </div>
                            {pct !== null && pct > 0 && (
                              <span className=" rounded-full bg-[#8a5a3d] px-2 py-1 font-mono text-xs font-bold text-white">
                                -{pct}%
                              </span>
                            )}
                        </div>

                        {/* Package information */}
                        <div className="mt-2 flex justify-between">
                          <span>
                            {shoppingList.some((item) => item.id === p.id) && (
                              <div className="rounded-full bg-[#1c1a16]/5 px-2 py-1 text-[10px] font-medium text-[#8a5a3d]">
                                I handleliste
                              </div>
                            )}
                          </span>
                        </div>

                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}