'use client';

import { X, Package, Tag, Store, MapPin } from "lucide-react";
import { STORE_LABELS } from "@/lib/constants";
import { Product, Catalog } from "@/types";

function storeLabel(store: string): string {
  return STORE_LABELS[store] ?? store;
}

function formatPrice(value: number | null): string {
  if (!value) return "Ingen pris oppgitt";
  return `${value.toFixed(2)} kr`;
}

function effectiveDiscount(p: Product): number | null {
  if (p.discount_percent !== null) return Math.round(p.discount_percent);
  if (p.current_price == null || p.old_price == null || p.old_price <= 0) return null;
  return Math.round(100 - (p.current_price / p.old_price) * 100);
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  p: Product;
  catalog?: Catalog | null;
}

export default function ProductModal({ isOpen, onClose, p, catalog }: ModalProps) {
  if (!isOpen || !p) return null;

  const pct = effectiveDiscount(p);
  const storeName = catalog?.store_name ?? storeLabel(p.store);
  const mapsUrl =
    catalog?.maps_url ??
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(storeName)}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-4xl overflow-hidden rounded-xl border border-[#1c1a16]/10 bg-[#f6f3ec] shadow-md"
      >
        <button
          onClick={onClose}
          className="absolute right-5 top-5 z-20 rounded-full border border-[#1c1a16]/10 bg-white p-2 shadow-sm hover:bg-[#1c1a16]/5 transition-colors cursor-pointer"
        >
          <X className="h-4 w-4 text-[#1c1a16]/70" />
        </button>

        {pct !== null && pct > 0 && (
          <div className="absolute left-5 top-5 rounded-full bg-[#8a5a3d] px-3 py-1.5 font-mono text-xs font-bold text-white">
            -{pct}%
          </div>
        )}

        <div className="grid md:grid-cols-[280px_1fr]">
          <div className="flex items-center justify-center bg-white p-8 md:border-r border-[#1c1a16]/10">
            <div className="flex aspect-square w-full max-w-[200px] items-center justify-center rounded-lg border border-[#1c1a16]/10 bg-[#f6f3ec]">
              <Package className="h-16 w-16 text-[#1c1a16]/25" />
            </div>
          </div>

          <div className="p-8">
            <p className="font-mono text-[10px] uppercase tracking-wider text-[#1c1a16]/40">
              {storeLabel(p.store)}
              {p.category ? ` · ${p.category}` : ""}
            </p>

            <h1 className="mt-1.5 text-2xl font-semibold leading-snug text-[#1c1a16]">
              {p.product_name}
            </h1>

            {p.brand && (
              <p className="mt-1 text-sm text-[#1c1a16]/50">
                {p.brand}
              </p>
            )}

            <div className="mt-6 flex items-baseline gap-3 border-t border-dashed border-[#1c1a16]/10 pt-5">
              <span className="text-3xl font-bold text-[#1c1a16]">
                {formatPrice(p.current_price)}
              </span>

              {p.old_price && (
                <span className="text-base text-[#1c1a16]/40 line-through">
                  {formatPrice(p.old_price)}
                </span>
              )}
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <Info title="Butikk" value={storeLabel(p.store)} icon={<Store size={15} />} />
              <Info title="Kategori" value={p.category ?? "Ukjent"} icon={<Tag size={15} />} />
              <Info title="Pakning" value={p.package_size ?? "Ukjent"} />
              <Info title="Pris per enhet" value={p.price_per_kg ? `${p.price_per_kg} kr/${p.unit_type ?? "kg"}` : "Ikke oppgitt"} />
            </div>

            <div className="mt-6 flex items-center justify-between gap-3 rounded-lg border border-[#1c1a16]/10 bg-white p-4">
              <div className="min-w-0">
                <div className="mb-1 flex items-center gap-1.5 text-[#1c1a16]/40">
                  <MapPin size={15} />
                  <span className="text-xs">Butikk</span>
                </div>
                <div className="truncate text-sm font-semibold text-[#1c1a16]">
                  {storeName}
                </div>
              </div>

              <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex shrink-0 items-center gap-1.5 rounded-lg border border-[#1c1a16]/10 bg-[#1c1a16] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#1c1a16]/90"
              >
                <MapPin size={14} />
                Åpne i Google Maps
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Info({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-[#1c1a16]/10 bg-white p-4">
      <div className="mb-1.5 flex items-center gap-1.5 text-[#1c1a16]/40">
        {icon}
        <span className="text-xs">{title}</span>
      </div>
      <div className={`text-sm font-semibold text-[#1c1a16] ${title.toLowerCase() === "kategori" && 'capitalize'}`}>
        {value}
      </div>
    </div>
  );
}