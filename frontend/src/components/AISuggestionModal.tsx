"use client";

import { useEffect, useRef, useState } from "react";
import { X, Download, Copy, Check, ExternalLink } from "lucide-react";

interface AiSuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownloadData: () => void;
}

const PROMPT_TEMPLATE = `Du er en norsk kostholdsassistent. Jeg har lastet opp denne ukens tilbud fra dagligvarebutikker som en fil.

Still meg først disse spørsmålene, ett om gangen, før du foreslår noe:
1. Har du noen allergier eller matintoleranser jeg må ta hensyn til?
2. Bryr du deg om makronæringsstoffer (f.eks. høyt protein, lavt kalori- eller fettinnhold)?
3. Hvor mange middager vil du ha forslag til denne uken?

Når jeg har svart, bruk KUN varer som faktisk finnes i tilbudsdataen i den vedlagte filen til å foreslå middager. Ikke inkluder varer, priser eller butikker som ikke står i filen. Ta hensyn til svarene mine på spørsmålene over.

For hvert middagsforslag, oppgi:
- Navn på retten
- Kort beskrivelse
- Omtrentlig næringsinnhold per porsjon (kalorier, protein, fett, karbohydrater) – kun hvis jeg svarte ja på spørsmål 2

Svar på norsk, i vanlig tekst (ikke JSON) i denne fasen.

Når jeg har bestemt meg for hvilke middager jeg vil lage, lag en handleliste basert KUN på varene jeg trenger å kjøpe til akkurat disse rettene. Bruk eksakt pris og butikk fra den vedlagte filen for hver vare. Ikke legg til varer fra en "basislager"-kategori eller andre varer som ikke er tilbudsvarer i filen, med mindre jeg spør om det.

Svar med handlelisten KUN som rå JSON – ingen forklaringstekst, ingen markdown-kodeblokk, ingen tekst før eller etter. Feltnavnene skal være på engelsk, verdiene på norsk. "amount" skal alltid være et tall (ikke tekst som "1 pk"), og "unit" skal beskrive enheten separat (f.eks. "pk", "kg", "stk"). Bruk nøyaktig dette formatet:

[
  { "product": "string", "amount": number, "unit": "string", "price": number, "store": "string" }
]

Hvis en vare mangler pris eller butikk i den vedlagte filen, hopp over den varen helt i stedet for å gjette.`;

const AI_SITES = [
    { name: "Gemini", url: "https://gemini.google.com" },
    { name: "Claude", url: "https://claude.ai" },
    { name: "ChatGPT", url: "https://chat.openai.com" },
];

const steps = [
  {
    title: "Last ned ukens tilbud",
    description:
      "Last ned en fil med tilbudene som matcher filtrene dine akkurat nå. Denne filen laster du opp sammen med prompten i steg 3.",
  },
  {
    title: "Kopier prompten",
    description:
      "Denne teksten ber AI-en stille deg noen spørsmål (allergier, makro-preferanser osv.) før den gir middagsforslag, og lage en handleliste i JSON når du har bestemt deg.",
  },
  {
    title: "Lim inn i en AI-tjeneste",
    description:
      "Åpne en av tjenestene under, last opp filen fra steg 1, lim inn prompten fra steg 2, og send. Svar på spørsmålene den stiller, og etter du har valgt middager, så kopierer du JSON-handlelisten den lager tilbake til appen.",
  },
];

export default function AiSuggestionModal({
  isOpen,
  onClose,
  onDownloadData,
}: AiSuggestionModalProps) {
  const [copied, setCopied] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  function handleCopy() {
    navigator.clipboard.writeText(PROMPT_TEMPLATE).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (dialogRef.current && !dialogRef.current.contains(e.target as Node)) {
      onClose();
    }
  }

  return (
    <div
      onMouseDown={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#1c1a16]/40 px-4"
    >
      <div
        ref={dialogRef}
        className="w-full max-w-lg rounded-xl border border-[#1c1a16]/10 bg-[#f6f3ec] p-6 shadow-xl"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold tracking-tight">Få middagsforslag med AI</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 cursor-pointer hover:bg-[#1c1a16]/5 transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        <p className="mt-1.5 text-sm text-[#1c1a16]/60">
          Kjøring av AI lokalt er som regel ganske tregt. Følg disse tre stegene for å bruke
          en AI-tjeneste i stedet.
        </p>

        <div className="mt-5 flex flex-col gap-4">
          {steps.map((step, i) => (
            <div
              key={step.title}
              className="rounded-lg border border-[#1c1a16]/10 bg-white p-4"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#8a5a3d] font-mono text-xs font-bold text-white">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold">{step.title}</h3>
                  <p className="mt-0.5 text-xs text-[#1c1a16]/55 leading-relaxed">
                    {step.description}
                  </p>

                  {i === 0 && (
                    <button
                      onClick={onDownloadData}
                      className="mt-3 flex items-center gap-1.5 rounded-lg bg-[#8a5a3d] px-3 py-1.5 text-xs font-semibold text-white cursor-pointer hover:bg-[#7a4d33] transition-colors"
                    >
                      <Download size={13} strokeWidth={2} />
                      Last ned tilbudsdata
                    </button>
                  )}

                  {i === 1 && (
                    <>
                      <div className="mt-3 max-h-32 overflow-y-auto rounded-lg border border-[#1c1a16]/10 bg-[#f6f3ec] p-2.5 font-mono text-[11px] leading-relaxed text-[#1c1a16]/70 custom-scrollbar whitespace-pre-wrap">
                        {PROMPT_TEMPLATE}
                      </div>
                      <button
                        onClick={handleCopy}
                        className={`mt-3 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                          copied
                            ? "bg-[#1c1a16]/5 text-[#8a5a3d]"
                            : "bg-[#8a5a3d] text-white hover:bg-[#7a4d33]"
                        }`}
                      >
                        {copied ? <Check size={13} strokeWidth={2.5} /> : <Copy size={13} strokeWidth={2} />}
                        {copied ? "Kopiert!" : "Kopier prompt"}
                      </button>
                    </>
                  )}

                  {i === 2 && (
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      {AI_SITES.map((site) => (
                        <a
                          key={site.name}
                          href={site.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-between gap-1.5 rounded-lg outline outline-[#1c1a16]/15 px-3 py-1.5 text-xs font-semibold text-[#1c1a16]/70 hover:outline-[#1c1a16]/35 hover:text-[#1c1a16] transition-colors"
                        >
                          {site.name}
                          <ExternalLink size={12} />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}