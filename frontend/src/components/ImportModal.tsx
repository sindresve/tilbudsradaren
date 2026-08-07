"use client";

import { useEffect, useRef, useState } from "react";
import { X, TriangleAlert, CheckCircle2, XCircle } from "lucide-react";
import { Product } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
  allProducts: Product[];
  onImport: (products: Product[]) => void;
}

interface ImportedItem {
  product: string;
  amount?: number;
  unit?: string;
  price?: number;
  store?: string;
}

interface MatchResult {
  imported: ImportedItem;
  match: Product | null;
}

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9æøå ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function storeKeyLabel(store: string): string {
  const labels: Record<string, string> = {
    rema1000: "rema 1000",
    coop_extra: "extra",
    kiwi: "kiwi",
  };
  return normalize(labels[store] ?? store);
}

function storeLabel(store: string): string {
  const labels: Record<string, string> = {
    rema1000: "REMA 1000",
    coop_extra: "Extra",
    kiwi: "Kiwi",
  };
  return labels[store] ?? store;
}

function findBestMatch(item: ImportedItem, allProducts: Product[]): Product | null {
  const target = normalize(item.product);
  const targetWords = target.split(" ").filter(Boolean);
  if (targetWords.length === 0) return null;

  const targetStore = item.store ? normalize(item.store) : null;

  let best: Product | null = null;
  let bestScore = 0;

  for (const p of allProducts) {
    const name = normalize(p.product_name);
    const nameWords = name.split(" ").filter(Boolean);

    const overlap = targetWords.filter(
      (w) => nameWords.includes(w) || name.includes(w)
    ).length;

    if (overlap === 0) continue;

    let score = overlap / targetWords.length;

    if (targetStore) {
      const pStoreLabel = storeKeyLabel(p.store);
      if (pStoreLabel === targetStore || pStoreLabel.includes(targetStore) || targetStore.includes(pStoreLabel)) {
        score += 0.5;
      }
    }

    if (name === target) {
      score += 1;
    }

    if (score > bestScore) {
      bestScore = score;
      best = p;
    }
  }

  if (bestScore < 0.5) return null;
  return best;
}

export default function ImportShoppingListModal({
  open,
  onClose,
  allProducts,
  onImport,
}: Props) {
  const [importText, setImportText] = useState("");
  const [importError, setImportError] = useState<string | null>(null);
  const [matchResults, setMatchResults] = useState<MatchResult[] | null>(null);

  const dialogRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!open) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (dialogRef.current && !dialogRef.current.contains(e.target as Node)) {
      onClose();
    }
  }

  function handleParseImport() {
    setImportError(null);
    setMatchResults(null);

    let parsed: unknown;
    try {
      parsed = JSON.parse(importText);
    } catch {
      setImportError("Klarte ikke å tolke JSON-en. Sjekk at den er gyldig.");
      return;
    }

    if (!Array.isArray(parsed)) {
      setImportError("JSON-en må være en liste med produkter.");
      return;
    }

    const items = parsed as ImportedItem[];
    const invalid = items.some((i) => typeof i.product !== "string" || !i.product.trim());
    if (invalid) {
      setImportError('Hvert element må ha et "product"-felt med tekst.');
      return;
    }

    const results: MatchResult[] = items.map((item) => ({
      imported: item,
      match: findBestMatch(item, allProducts),
    }));

    setMatchResults(results);
  }

  function handleConfirmImport() {
    if (!matchResults) return;
    const matched = matchResults
      .map((r) => r.match)
      .filter((p): p is Product => p !== null);
    onImport(matched);
    handleClose();
  }

  function handleClose() {
    setImportText("");
    setImportError(null);
    setMatchResults(null);
    onClose();
  }

  return (
    <div 
      onMouseDown={handleBackdropClick}
      className="fixed inset-0 z-60 flex items-center justify-center bg-black/40 p-4"
    >
      <div 
        ref={dialogRef}
        className="flex max-h-[85vh] w-full max-w-lg flex-col rounded-2xl bg-[#faf8f5] shadow-xl"
      >
        <div className="flex items-center justify-between border-b border-[#1c1a16]/10 px-5 py-4">
          <h3 className="font-semibold text-[#1c1a16]">Importer handleliste</h3>
          <button
            onClick={handleClose}
            className="rounded-lg p-2 hover:bg-[#1c1a16]/5 transition"
          >
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-4">
          {!matchResults && (
            <>
              <p className="text-sm text-[#1c1a16]/60">
                Lim inn en liste med produkter som JSON. Vi prøver å matche hvert produkt mot varer som finnes i katalogen.
              </p>
              <textarea
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder='[{ "product": "Kyllingfilet", "amount": 1, "unit": "pk", "price": 39.9, "store": "Kiwi" }]'
                className="h-56 w-full resize-none rounded-xl border border-[#1c1a16]/15 bg-white p-3 font-mono text-xs text-[#1c1a16]/80 focus:border-[#8a5a3d]/50 focus:outline-none"
              />
              {importError && (
                <p className="flex items-center gap-1.5 text-xs text-red-700">
                  <TriangleAlert className="h-3.5 w-3.5 shrink-0" strokeWidth={2} />
                  {importError}
                </p>
              )}
            </>
          )}

          {matchResults && (
            <div className="space-y-2">
              <p className="text-sm text-[#1c1a16]/60">
                Fant treff på{" "}
                <span className="font-semibold text-[#1c1a16]">
                  {matchResults.filter((r) => r.match).length}
                </span>{" "}
                av <span className="font-semibold text-[#1c1a16]">{matchResults.length}</span> varer.
              </p>

              {matchResults.map((r, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-3 rounded-xl border border-[#1c1a16]/10 bg-white p-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-[#1c1a16]">
                      {r.imported.product}
                    </p>
                    {r.match ? (
                      <p className="truncate text-xs text-[#1c1a16]/50">
                        → {r.match.product_name} ({storeLabel(r.match.store)})
                      </p>
                    ) : (
                      <p className="text-xs text-red-700">Ingen treff funnet</p>
                    )}
                  </div>
                  {r.match ? (
                    <CheckCircle2 size={18} className="shrink-0 text-[#8a5a3d]" strokeWidth={1.75} />
                  ) : (
                    <XCircle size={18} className="shrink-0 text-red-400" strokeWidth={1.75} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-[#1c1a16]/10 p-5 pt-4">
          {!matchResults ? (
            <button
              onClick={handleParseImport}
              disabled={!importText.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#8a5a3d] py-3 text-sm font-semibold text-white transition hover:bg-[#7a4d33] disabled:cursor-not-allowed disabled:opacity-40"
            >
              Match produkter
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => setMatchResults(null)}
                className="flex-1 rounded-xl border border-[#1c1a16]/15 bg-white py-3 text-sm font-semibold text-[#1c1a16]/80 transition hover:border-[#1c1a16]/30"
              >
                Tilbake
              </button>
              <button
                onClick={handleConfirmImport}
                disabled={matchResults.every((r) => !r.match)}
                className="flex-1 rounded-xl bg-[#8a5a3d] py-3 text-sm font-semibold text-white transition hover:bg-[#7a4d33] disabled:cursor-not-allowed disabled:opacity-40"
              >
                Legg til {matchResults.filter((r) => r.match).length} varer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}