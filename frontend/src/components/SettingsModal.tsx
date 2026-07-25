'use client';

import { Bell, Info, Plug, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Modal({ isOpen, onClose }: ModalProps) {
  const [activeTab, setActiveTab] = useState<string>("Info");

        
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return createPortal(
        <div
            onClick={onClose}
            style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 50,
        }}
        >
            {/* For lightmode: #F7F3EC, #EDE7DC */}
            <div 
                onClick={(e) => e.stopPropagation()}
                className='flex flex-row max-w-7xl w-full max-h-9/12 h-full bg-[#211C19] rounded-2xl overflow-hidden text-[#F2EEE7]'
            >
                <div className='bg-[#2A2420] max-w-72 w-full h-full py-4 px-5'>
                    <h1 className='font-bold'>Innstillinger</h1>
                    <button onClick={() => setActiveTab("Info")} className={`mt-6 text- flex transition-all duration-200  items-center gap-1.5 cursor-pointer w-full ${activeTab === "Info" && 'bg-[#b1aeae]/10'} hover:bg-[#b1aeae]/10 rounded-lg p-2`}>
                        <Info size={17} strokeWidth={1.5} className="cursor-pointer" />
                        Info
                    </button>
                    <button onClick={() => setActiveTab("Varslinger")} className={`mt-3 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${activeTab === "Varslinger" && 'bg-[#b1aeae]/10'} hover:bg-[#b1aeae]/10 rounded-lg p-2`}>
                        <Bell size={17} strokeWidth={1.5} className="cursor-pointer" />
                        Varslinger
                    </button>
                    <button onClick={() => setActiveTab("Konfigurasjon")} className={`mt-3 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${activeTab === "Konfigurasjon" && 'bg-[#b1aeae]/10'} hover:bg-[#b1aeae]/10 rounded-lg p-2`}>
                        <Plug size={17} strokeWidth={1.5} className="cursor-pointer" />
                        Konfigurasjon
                    </button>
                </div>
                <div className='w-full h-full flex flex-col overflow-hidden'>
                    <div className='px-4.5 py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 flex items-center justify-between'>
                        <h3 className='font-semibold'>{activeTab}</h3>

                        <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: '20px', cursor: 'pointer' }}>
                            <X size={18} strokeWidth={1.25} className="cursor-pointer" />
                        </button>
                    </div>

                </div>
            </div>
        </div>,
        document.body
    );
}