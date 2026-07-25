"use client";

import { Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Tilbud" },
  { href: "/chat", label: "AI-assistent" },
];

interface NavBarProps {
  setModalOpen: () => void;
}


export default function Navbar({ setModalOpen }: NavBarProps) {
  const pathname = usePathname();

  return (
    <nav className="border-b-2 border-dashed border-[#1c1a16]/20 bg-[#f6f3ec] px-6 sm:px-10">
      <div className="mx-auto flex max-w-6xl items-center justify-between py-4">
        <Link href="/" className="flex items-baseline gap-2 text-black">
          <span className="text-lg font-bold tracking-tight">Tilbudsradaren</span>
        </Link>

        <div className="flex gap-1">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-[#1c1a16] text-[#f6f3ec]"
                    : "text-[#1c1a16]/60 hover:bg-[#1c1a16]/5 hover:text-[#1c1a16]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <button onClick={() => setModalOpen()}>
            <Settings color="#000000" size={18} strokeWidth={1.25} className="cursor-pointer" />
          </button>
        </div>
      </div>
    </nav>
  );
}