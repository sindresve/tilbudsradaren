"use client";

import { Settings, ChefHat } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";


interface NavBarProps {
  setModalOpen: () => void;
  setAiModalOpen: () => void;
}


export default function Navbar({ setModalOpen, setAiModalOpen }: NavBarProps) {
  const pathname = usePathname();

  return (
    <nav className="border-b-2 border-dashed border-[#1c1a16]/20 bg-[#f6f3ec] px-6 sm:px-10">
      <div className="mx-auto flex max-w-7xl items-center justify-between py-4 h-15">
        <Link href="/" className="flex items-baseline gap-2 text-black">
          <span className="text-lg font-bold tracking-tight">Tilbudsradaren</span>
        </Link>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setAiModalOpen()}
            className="flex items-center gap-2 rounded-lg border border-[#1c1a16]/15 bg-white px-3 py-1.5 text-sm font-medium text-[#1c1a16]/80 cursor-pointer hover:border-[#8a5a3d]/50 hover:text-[#8a5a3d] transition-colors"
          >
            <ChefHat size={16} strokeWidth={1.5} />
            Middagsforslag
          </button>
          <button onClick={() => setModalOpen()} className="p-1.5">
            <Settings color="#000000" size={18} strokeWidth={1.25} className="cursor-pointer" />
          </button>
        </div>
      </div>
    </nav>
  );
}