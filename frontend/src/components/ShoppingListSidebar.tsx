"use client";

import { X, Trash2, ShoppingCart, ChevronsRight, TriangleAlert, Import } from "lucide-react";
import { Product } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
  products: Product[];
  onRemove: (id: number) => void;
  onOpenImport: () => void;
}

function storeLabel(store: string): string {
  const labels: Record<string, string> = {
    rema1000: "REMA 1000",
    coop_extra: "Extra",
    kiwi: "Kiwi",
  };

  return labels[store] ?? store;
}

function formatPrice(value: number | null) {
  if (value === null || value === 0) return "Ingen pris";
  return `${value.toFixed(2)} kr`;
}

export default function ShoppingListSidebar({
  open,
  onClose,
  products,
  onRemove,
  onOpenImport,
}: Props) {
  const total = products.reduce(
    (sum, p) => sum + (p.current_price || 0),
    0
  );

  const saved = products.reduce((sum, p) => {
    if (!p.old_price || !p.current_price) return sum;
    return sum + (p.old_price - p.current_price);
  }, 0);

  const hasMissingPrice = products.some(
    (p) => !p.current_price || !p.old_price
    );

  return (
    <aside
      className={`
        fixed right-0 top-0 z-50
        flex h-screen w-96 flex-col
        border-l border-[#1c1a16]/10
        bg-[#faf8f5]
        transition-transform duration-300
        ${open ? "translate-x-0" : "translate-x-full"}
      `}
    >
      <button 
        onClick={onClose}
        className={`absolute left-0 top-1/2 translate-y-1/2 -translate-x-1/2 border-[#1c1a16]/10 bg-white hover:bg-[#faf8f5] border rounded-full px-1.5 py-0.5 cursor-pointer ${open ? "opacity-100" : "opacity-0"} transition-all duration-100`}
      >
        <ChevronsRight size={16} strokeWidth={1.5}/>
      </button>
      <div className="flex items-center justify-between border-[#1c1a16]/10 px-5 py-4">
        <div>
          <h2 className="font-semibold text-[#1c1a16]">Handleliste</h2>
          <p className="text-xs text-[#1c1a16]/50">{products.length} varer</p>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onOpenImport}
            className="flex items-center gap-2 rounded-lg border border-[#1c1a16]/15 bg-white px-3 py-1.5 text-sm font-medium text-[#1c1a16]/80 cursor-pointer hover:border-[#8a5a3d]/50 hover:text-[#8a5a3d] transition-colors"
            title="Importer fra JSON"
          >
            <Import size={16} strokeWidth={1.5} />
            Importer
          </button>

          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-[#1c1a16]/5 transition"
          >
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>
      </div>

      {/* Items */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-3">
        {products.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <ShoppingCart size={32} className="text-[#1c1a16]/30" />
            <p className="mt-3 text-sm text-[#1c1a16]/50">Handlelisten er tom</p>
          </div>
        )}

        {products.map((p) => (
          <div
            key={p.id}
            className="rounded-xl border border-[#1c1a16]/10 bg-white p-4"
          >
            <div className="flex justify-between gap-3">
              <div>
                <h3 className="font-medium text-[#1c1a16]">{p.product_name}</h3>
                <p className="text-xs text-[#1c1a16]/50">{storeLabel(p.store)}</p>
              </div>

              <button
                onClick={() => onRemove(p.id)}
                className="h-fit rounded-md p-1 text-[#1c1a16]/40 hover:text-[#8a5a3d]"
              >
                <Trash2 size={15} />
              </button>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <span className="text-lg font-bold">{formatPrice(p.current_price)}</span>

              {p.old_price && p.current_price && (
                <span className="text-xs text-[#1c1a16]/40 line-through">
                  {formatPrice(p.old_price)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-[#1c1a16]/10 bg-white p-5 pb-2">
        <div className="flex justify-between text-sm text-[#1c1a16]/60">
          <span>Totalt</span>
          <span className="font-semibold text-[#1c1a16]">
            {total.toFixed(2)} kr
          </span>
        </div>

        <div className="mt-2 flex justify-between text-sm">
          <span className="text-[#1c1a16]/60">Spart</span>
          <span className="font-semibold text-[#8a5a3d]">
            {saved.toFixed(2)} kr
          </span>
        </div>

        {hasMissingPrice && (
            <span className="flex items-center mt-2 gap-1.5 text-xs text-amber-800 rounded-full w-fit px-3 py-1.5 border border-amber-200 bg-amber-50">
                <TriangleAlert className="w-3.5 h-3.5 shrink-0" strokeWidth={2} />
                Enkelte varer mangler pris og er ikke regnet med i det du har spart
            </span>
        )}

        <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[#8a5a3d] py-3 text-sm font-semibold text-white transition hover:bg-[#7a4d33]">
          <ShoppingCart size={16} />
          Send handleliste
        </button>
        <p className="text-xs mt-2 text-[#1c1a16]/40">Du kan endre hvor handlelisten blir sendt i innstillinger</p>
      </div>
    </aside>
  );
}