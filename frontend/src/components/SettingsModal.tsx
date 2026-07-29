'use client';

import { Bell, Plug, Plus, ShoppingBasket, SlidersHorizontal, Trash2, X, Circle, Loader2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { getSettings, patchSettings } from '@/lib/api';
import { STORE_LABELS } from "@/lib/constants"

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function ScrollbarStyles() {
  return (
    <style jsx global>{`
      .settings-scroll::-webkit-scrollbar {
        width: 10px;
      }
      .settings-scroll::-webkit-scrollbar-track {
        background: transparent;
      }
      .settings-scroll::-webkit-scrollbar-thumb {
        background-color: #3a332e;
        border-radius: 999px;
        border: 2px solid #211c19;
      }
      .settings-scroll::-webkit-scrollbar-thumb:hover {
        background-color: #8a5a44;
      }
      .settings-scroll {
        scrollbar-width: thin;
        scrollbar-color: #3a332e transparent;
      }
      @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.85); }
      }
      .unsaved-dot {
        animation: pulse-dot 1.6s ease-in-out infinite;
      }
    `}</style>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ${
        checked ? 'bg-[#8A5A44]' : 'bg-[#3A332E]'
      }`}
    >
      <span
        className={`inline-block h-5 w-5 mt-0.5 transform rounded-full bg-[#F2EEE7] transition-transform duration-200 ${
          checked ? 'translate-x-5' : 'translate-x-0.5'
        }`}
      />
    </button>
  );
}

function SettingRow({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 last:border-b-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-[#F2EEE7]">{title}</p>
        {description && (
          <p className="text-xs text-[#9B958C] mt-0.5">{description}</p>
        )}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

type Channel = 'discord' | 'email';

function ChannelToggles({
  channels,
  onChange,
}: {
  channels: Channel[];
  onChange: (channels: Channel[]) => void;
}) {
  const toggle = (c: Channel) => {
    if (channels.includes(c)) {
      onChange(channels.filter((x) => x !== c));
    } else {
      onChange([...channels, c]);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => toggle('discord')}
        className={`text-xs font-medium rounded-full px-3 py-1.5 border transition-colors duration-150 cursor-pointer ${
          channels.includes('discord')
            ? 'bg-[#8A5A44] border-[#8A5A44] text-[#F2EEE7]'
            : 'bg-transparent border-[#3A332E] text-[#9B958C] hover:border-[#8A5A44]/60'
        }`}
      >
        Discord
      </button>
      <button
        onClick={() => toggle('email')}
        className={`text-xs font-medium rounded-full px-3 py-1.5 border transition-colors duration-150 cursor-pointer ${
          channels.includes('email')
            ? 'bg-[#8A5A44] border-[#8A5A44] text-[#F2EEE7]'
            : 'bg-transparent border-[#3A332E] text-[#9B958C] hover:border-[#8A5A44]/60'
        }`}
      >
        E-post
      </button>
    </div>
  );
}

function NotificationRow({
  title,
  description,
  enabled,
  onToggle,
  channels,
  onChannelsChange,
}: {
  title: string;
  description: string;
  enabled: boolean;
  onToggle: (v: boolean) => void;
  channels: Channel[];
  onChannelsChange: (c: Channel[]) => void;
}) {
  return (
    <div className="py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 last:border-b-0">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-[#F2EEE7]">{title}</p>
          <p className="text-xs text-[#9B958C] mt-0.5">{description}</p>
        </div>
        <div className="shrink-0">
          <Toggle checked={enabled} onChange={onToggle} />
        </div>
      </div>
      {enabled && (
        <div className="mt-3 flex items-center gap-2 pl-0.5">
          <span className="text-xs text-[#6B655D] mr-1">Send via:</span>
          <ChannelToggles channels={channels} onChange={onChannelsChange} />
        </div>
      )}
    </div>
  );
}

function ListInput({
  placeholder,
  onAdd,
}: {
  placeholder: string;
  onAdd: (value: string) => void;
}) {
  const [value, setValue] = useState('');

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onAdd(trimmed);
    setValue('');
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && submit()}
        className="flex-1 bg-[#1A1613] border border-[#3A332E] rounded-lg px-3 py-2 text-sm text-[#F2EEE7] placeholder:text-[#6B655D] outline-none focus:border-[#8A5A44] transition-colors duration-150"
      />
      <button
        onClick={submit}
        className="shrink-0 flex items-center gap-1 bg-[#8A5A44] hover:bg-[#7A4E3A] transition-colors duration-150 text-[#F2EEE7] text-sm font-medium rounded-lg px-3 py-2 cursor-pointer"
      >
        <Plus size={15} strokeWidth={2} />
        Legg til
      </button>
    </div>
  );
}

function ListItem({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5 border-b-[0.5px] border-[#F2EEE7]/10 last:border-b-0 group">
      <span className="text-sm text-[#F2EEE7]">{label}</span>
      <button
        onClick={onRemove}
        className="shrink-0 text-[#6B655D] hover:text-[#C0554A] transition-colors duration-150 cursor-pointer opacity-60 group-hover:opacity-100"
        aria-label={`Fjern ${label}`}
      >
        <Trash2 size={15} strokeWidth={1.75} />
      </button>
    </div>
  );
}

function EmptyListHint({ text }: { text: string }) {
  return <p className="text-xs text-[#6B655D] py-2">{text}</p>;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="text-xs font-semibold uppercase tracking-wide text-[#9B958C] mb-1 mt-6 first:mt-0">
      {children}
    </h4>
  );
}

function TextField({
  label,
  placeholder,
  value,
  onChange,
  inputMode = "text",
  pattern,
  type = "text",
  maxLength,
}: {
  label: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
  pattern?: string;
  type?: string;
  maxLength?: number;
}) {
  return (
    <div className="py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 last:border-b-0">
      <label className="text-sm font-medium text-[#F2EEE7] block mb-2">
        {label}
      </label>
      <input
        type={type}
        inputMode={inputMode}
        value={value}
        pattern={pattern}
        maxLength={maxLength}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#1A1613] border border-[#3A332E] rounded-lg px-3 py-2 text-sm text-[#F2EEE7] placeholder:text-[#6B655D] outline-none focus:border-[#8A5A44] transition-colors duration-150"
      />
    </div>
  );
}

// Small reusable "unsaved changes" pill shown next to a save button
function UnsavedHint() {
  return (
    <span className="flex items-center gap-1.5 text-xs text-[#E0A458]">
      <Circle size={7} className="fill-[#E0A458] text-[#E0A458] unsaved-dot" />
      Ulagrede endringer
    </span>
  );
}

export default function Modal({ isOpen, onClose }: ModalProps) {
  const [activeTab, setActiveTab] = useState<string>('Varslinger');

  // ---------------- NOTIFICATIONS STATE ----------------
  type NotificationsState = {
    priceDrops: { enabled: boolean; channels: Channel[] };
    newOffers: { enabled: boolean; channels: Channel[] };
    weeklyDigest: { enabled: boolean; channels: Channel[] };
    stockAlerts: { enabled: boolean; channels: Channel[] };
    dryGoodsAlerts: { enabled: boolean; channels: Channel[] };
    dashboardNewOffers: { enabled: boolean; channels: Channel[] };
    bestDealsWeekly: { enabled: boolean; channels: Channel[] };
    favoriteFoodAlerts: { enabled: boolean; channels: Channel[] };
  };

  const initialNotifications: NotificationsState = {
    priceDrops: { enabled: true, channels: ['email'] },
    newOffers: { enabled: true, channels: ['discord', 'email'] },
    weeklyDigest: { enabled: false, channels: [] },
    stockAlerts: { enabled: false, channels: [] },
    dryGoodsAlerts: { enabled: true, channels: ['email'] },
    dashboardNewOffers: { enabled: true, channels: [] },
    bestDealsWeekly: { enabled: true, channels: ['discord'] },
    favoriteFoodAlerts: { enabled: true, channels: ['email'] },
  };

  const [notifications, setNotifications] = useState<NotificationsState>(initialNotifications);
  const [savedNotifications, setSavedNotifications] = useState<NotificationsState>(initialNotifications);

  const updateNotification = (
    key: keyof NotificationsState,
    patch: Partial<{ enabled: boolean; channels: Channel[] }>
  ) => {
    setNotifications((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }));
  };

  // ---------------- PREFERENCES STATE ----------------
  type StoresState = Record<string, boolean>;
  type AllergiesState = { gluten: boolean; laktose: boolean; nøtter: boolean; egg: boolean; skalldyr: boolean };

  const initialAllergies: AllergiesState = {
    gluten: false,
    laktose: false,
    nøtter: false,
    egg: false,
    skalldyr: false,
  };

  const [stores, setStores] = useState<StoresState>({});
  const [savedStores, setSavedStores] = useState<StoresState>({});
  const [storesLoading, setStoresLoading] = useState(true);
  const [storesLoadError, setStoresLoadError] = useState<string | null>(null);

  const [allergies, setAllergies] = useState<AllergiesState>(initialAllergies);
  const [savedAllergies, setSavedAllergies] = useState<AllergiesState>(initialAllergies);

  // ---------------- SHOPPING LIST STATE ----------------
  const initialDryGoods = ['Ris', 'Mel', 'Sukker', 'Havregryn'];
  const initialFavoriteFoods = ['Kylling', 'Kjøttdeig'];

  const [dryGoods, setDryGoods] = useState<string[]>(initialDryGoods);
  const [savedDryGoods, setSavedDryGoods] = useState<string[]>(initialDryGoods);
  const [favoriteFoods, setFavoriteFoods] = useState<string[]>(initialFavoriteFoods);
  const [savedFavoriteFoods, setSavedFavoriteFoods] = useState<string[]>(initialFavoriteFoods);

  const addDryGood = (name: string) => {
    if (dryGoods.some((g) => g.toLowerCase() === name.toLowerCase())) return;
    setDryGoods((prev) => [...prev, name]);
  };
  const removeDryGood = (name: string) => {
    setDryGoods((prev) => prev.filter((g) => g !== name));
  };

  const addFavoriteFood = (name: string) => {
    if (favoriteFoods.some((f) => f.toLowerCase() === name.toLowerCase())) return;
    setFavoriteFoods((prev) => [...prev, name]);
  };
  const removeFavoriteFood = (name: string) => {
    setFavoriteFoods((prev) => prev.filter((f) => f !== name));
  };

  // ---------------- CONFIGURATION STATE ----------------
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [geminiKeySet, setGeminiKeySet] = useState(false);
  const [geminiKeyPreview, setGeminiKeyPreview] = useState<string | null>(null);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [savedWebhookUrl, setSavedWebhookUrl] = useState('');
  const [smtpHost, setSmtpHost] = useState('');
  const [savedSmtpHost, setSavedSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [savedSmtpPort, setSavedSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [savedSmtpUser, setSavedSmtpUser] = useState('');
  const [smtpPass, setSmtpPass] = useState('');
  const [savedSmtpPass, setSavedSmtpPass] = useState('');
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [savedWebhookEnabled, setSavedWebhookEnabled] = useState(false);
  const [smtpEnabled, setSmtpEnabled] = useState(false);
  const [savedSmtpEnabled, setSavedSmtpEnabled] = useState(false);
  const [postalCode, setPostalCode] = useState('');
  const [savedPostalCode, setSavedPostalCode] = useState('');
  const [budgetAmount, setBudgetAmount] = useState('');
  const [savedBudgetAmount, setSavedBudgetAmount] = useState('');
  const [budgetPeriod, setBudgetPeriod] = useState<'uke' | 'måned'>('uke');
  const [savedBudgetPeriod, setSavedBudgetPeriod] = useState<'uke' | 'måned'>('uke');

  // ---------------- DIRTY CHECKS ----------------
  const notificationsDirty = useMemo(
    () => JSON.stringify(notifications) !== JSON.stringify(savedNotifications),
    [notifications, savedNotifications]
  );

  const preferencesDirty = useMemo(
    () =>
      JSON.stringify(stores) !== JSON.stringify(savedStores) ||
      JSON.stringify(allergies) !== JSON.stringify(savedAllergies),
    [stores, savedStores, allergies, savedAllergies]
  );

  const shoppingListDirty = useMemo(
    () =>
      JSON.stringify(dryGoods) !== JSON.stringify(savedDryGoods) ||
      JSON.stringify(favoriteFoods) !== JSON.stringify(savedFavoriteFoods),
    [dryGoods, savedDryGoods, favoriteFoods, savedFavoriteFoods]
  );

  const configDirty = useMemo(
    () =>
      geminiApiKey !== '' ||
      webhookUrl !== savedWebhookUrl ||
      smtpHost !== savedSmtpHost ||
      smtpPort !== savedSmtpPort ||
      smtpUser !== savedSmtpUser ||
      smtpPass !== savedSmtpPass ||
      webhookEnabled !== savedWebhookEnabled ||
      smtpEnabled !== savedSmtpEnabled ||
      postalCode !== savedPostalCode ||
      budgetAmount !== savedBudgetAmount ||
      budgetPeriod !== savedBudgetPeriod,
    [
      geminiApiKey,
      webhookUrl, savedWebhookUrl,
      smtpHost, savedSmtpHost,
      smtpPort, savedSmtpPort,
      smtpUser, savedSmtpUser,
      smtpPass, savedSmtpPass,
      webhookEnabled, savedWebhookEnabled,
      smtpEnabled, savedSmtpEnabled,
      postalCode, savedPostalCode,
      budgetAmount, savedBudgetAmount,
      budgetPeriod, savedBudgetPeriod,
    ]
  );

  const anyDirty = notificationsDirty || preferencesDirty || shoppingListDirty || configDirty;

  const dirtyByTab: Record<string, boolean> = {
    Varslinger: notificationsDirty,
    Preferanser: preferencesDirty,
    Handleliste: shoppingListDirty,
    Konfigurasjon: configDirty,
  };

  // ---------------- DIFF PAYLOAD BUILDER ----------------
  // Only includes keys that actually changed since last save, grouped by
  // section, so the backend can run targeted UPDATE queries instead of
  // rewriting every column.
  const buildChangedPayload = () => {
    const payload: Record<string, unknown> = {};

    // notifications: only include individual notification keys that changed
    if (notificationsDirty) {
      const changedNotifications: Partial<NotificationsState> = {};
      (Object.keys(notifications) as (keyof NotificationsState)[]).forEach((key) => {
        if (JSON.stringify(notifications[key]) !== JSON.stringify(savedNotifications[key])) {
          changedNotifications[key] = notifications[key];
        }
      });
      if (Object.keys(changedNotifications).length > 0) {
        payload.notifications = changedNotifications;
      }
    }

    if (geminiApiKey !== '') {
      payload.geminiApiKey = geminiApiKey;
    }

    // stores: only changed store keys
    if (JSON.stringify(stores) !== JSON.stringify(savedStores)) {
      const changedStores: Partial<StoresState> = {};
      (Object.keys(stores) as (keyof StoresState)[]).forEach((key) => {
        if (stores[key] !== savedStores[key]) changedStores[key] = stores[key];
      });
      if (Object.keys(changedStores).length > 0) payload.stores = changedStores;
    }

    // allergies: only changed allergy keys
    if (JSON.stringify(allergies) !== JSON.stringify(savedAllergies)) {
      const changedAllergies: Partial<AllergiesState> = {};
      (Object.keys(allergies) as (keyof AllergiesState)[]).forEach((key) => {
        if (allergies[key] !== savedAllergies[key]) changedAllergies[key] = allergies[key];
      });
      if (Object.keys(changedAllergies).length > 0) payload.allergies = changedAllergies;
    }

    // lists: send the whole list only if it changed (lists are replaced, not diffed field-by-field)
    if (JSON.stringify(dryGoods) !== JSON.stringify(savedDryGoods)) {
      payload.dryGoods = dryGoods;
    }
    if (JSON.stringify(favoriteFoods) !== JSON.stringify(savedFavoriteFoods)) {
      payload.favoriteFoods = favoriteFoods;
    }

    // config: only changed individual fields
    const configFieldMap: Array<[string, unknown, unknown]> = [
      ['webhookUrl', webhookUrl, savedWebhookUrl],
      ['smtpHost', smtpHost, savedSmtpHost],
      ['smtpPort', smtpPort, savedSmtpPort],
      ['smtpUser', smtpUser, savedSmtpUser],
      ['smtpPass', smtpPass, savedSmtpPass],
      ['webhookEnabled', webhookEnabled, savedWebhookEnabled],
      ['smtpEnabled', smtpEnabled, savedSmtpEnabled],
      ['postalCode', postalCode, savedPostalCode],
      ['budgetAmount', budgetAmount, savedBudgetAmount],
      ['budgetPeriod', budgetPeriod, savedBudgetPeriod],
    ];
    const changedConfig: Record<string, unknown> = {};
    configFieldMap.forEach(([key, current, saved]) => {
      if (current !== saved) changedConfig[key] = current;
    });
    if (Object.keys(changedConfig).length > 0) payload.config = changedConfig;

    return payload;
  };

  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Single global save: sends only the diff to the backend, then syncs
  // "saved" snapshots so dirty-state clears for exactly what was sent.
  const saveAllChanges = async () => {
    const payload = buildChangedPayload();
    if (Object.keys(payload).length === 0) return;

    setIsSaving(true);
    setSaveError(null);
    try {
      if (payload.stores) {
        await patchSettings({ stores: payload.stores as Record<string, boolean> });
      }

      // Sync saved snapshots only for sections that were part of the payload
      if (payload.notifications) setSavedNotifications(notifications);
      if (payload.stores || payload.geminiApiKey) {
        const result = await patchSettings({
          ...(payload.stores ? { stores: payload.stores as Record<string, boolean> } : {}),
          ...(payload.geminiApiKey ? { gemini_api_key: payload.geminiApiKey as string } : {}),
        });
        setGeminiKeySet(result.config.gemini_api_key_set);
        setGeminiKeyPreview(result.config.gemini_api_key_preview);
      }
      if (payload.allergies) setSavedAllergies(allergies);
      if (payload.dryGoods) setSavedDryGoods(dryGoods);
      if (payload.favoriteFoods) setSavedFavoriteFoods(favoriteFoods);
      if (payload.config) {
        setSavedWebhookUrl(webhookUrl);
        setSavedSmtpHost(smtpHost);
        setSavedSmtpPort(smtpPort);
        setSavedSmtpUser(smtpUser);
        setSavedSmtpPass(smtpPass);
        setSavedWebhookEnabled(webhookEnabled);
        setSavedSmtpEnabled(smtpEnabled);
        setSavedPostalCode(postalCode);
        setSavedBudgetAmount(budgetAmount);
        setSavedBudgetPeriod(budgetPeriod);
      }
      if (payload.geminiApiKey) setGeminiApiKey('');
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Ukjent feil ved lagring');
    } finally {
      setIsSaving(false);
    }
  };

  // Warn before closing the modal if there are unsaved changes anywhere
  const handleClose = () => {
    if (anyDirty) {
      const confirmClose = window.confirm(
        'Du har ulagrede endringer. Er du sikker på at du vil lukke uten å lagre?'
      );
      if (!confirmClose) return;
    }
    onClose();
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    if (isOpen) document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, anyDirty]);

  // Lock background scroll while the modal is open. Applied directly to
  // <html>/<body> here so it works regardless of how layout.tsx is set up —
  // no changes to layout.tsx needed.
  useEffect(() => {
    if (!isOpen) return;

    const scrollY = window.scrollY;
    const originalBodyOverflow = document.body.style.overflow;
    const originalHtmlOverflow = document.documentElement.style.overflow;
    const originalBodyPosition = document.body.style.position;
    const originalBodyTop = document.body.style.top;
    const originalBodyWidth = document.body.style.width;

    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    // Also lock position so iOS Safari doesn't allow rubber-band scroll
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = '100%';

    return () => {
      document.documentElement.style.overflow = originalHtmlOverflow;
      document.body.style.overflow = originalBodyOverflow;
      document.body.style.position = originalBodyPosition;
      document.body.style.top = originalBodyTop;
      document.body.style.width = originalBodyWidth;
      window.scrollTo(0, scrollY);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;
    setStoresLoading(true);
    setStoresLoadError(null);

    getSettings()
      .then((settings) => {
        if (cancelled) return;
        const storesMap: StoresState = {};
        settings.stores.forEach((s) => {
          storesMap[s.store] = Boolean(s.enabled);
        });
        setStores(storesMap);
        setSavedStores(storesMap);
      })
      .catch((err) => {
        if (cancelled) return;
        setStoresLoadError(
          err instanceof Error ? err.message : 'Klarte ikke å hente innstillinger'
        );
      })
      .finally(() => {
        if (!cancelled) setStoresLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;
    setStoresLoading(true);
    setStoresLoadError(null);

    getSettings()
      .then((settings) => {
        if (cancelled) return;
        const storesMap: StoresState = {};
        settings.stores.forEach((s) => {
          storesMap[s.store] = Boolean(s.enabled);
        });
        setStores(storesMap);
        setSavedStores(storesMap);

        setGeminiKeySet(settings.config.gemini_api_key_set);
        setGeminiKeyPreview(settings.config.gemini_api_key_preview);
      })
      .catch((err) => {
        if (cancelled) return;
        setStoresLoadError(
          err instanceof Error ? err.message : 'Klarte ikke å hente innstillinger'
        );
      })
      .finally(() => {
        if (!cancelled) setStoresLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen]);
  
  if (!isOpen) return null;

  const tabs = [
    { id: 'Varslinger', label: 'Varslinger', icon: Bell },
    { id: 'Preferanser', label: 'Preferanser', icon: SlidersHorizontal },
    { id: 'Handleliste', label: 'Handleliste', icon: ShoppingBasket },
    { id: 'Konfigurasjon', label: 'Konfigurasjon', icon: Plug },
  ];

  return createPortal(
    <div
      onClick={handleClose}
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
      <ScrollbarStyles />
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex flex-row max-w-7xl w-full max-h-9/12 h-full bg-[#211C19] rounded-2xl overflow-hidden text-[#F2EEE7]"
      >
        {/* Sidebar */}
        <div className="bg-[#2A2420] max-w-72 w-full h-full py-4 px-5 shrink-0 flex flex-col">
          <h1 className="font-bold">Innstillinger</h1>

          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`mt-3 first:mt-6 transition-all duration-200 flex items-center justify-between gap-1.5 cursor-pointer w-full ${
                activeTab === id && 'bg-[#b1aeae]/10'
              } hover:bg-[#b1aeae]/10 rounded-lg p-2`}
            >
              <span className="flex items-center gap-1.5">
                <Icon size={17} strokeWidth={1.5} className="cursor-pointer" />
                {label}
              </span>
              {dirtyByTab[id] && (
                <Circle
                  size={7}
                  className="fill-[#E0A458] text-[#E0A458] unsaved-dot shrink-0"
                  aria-label="Ulagrede endringer"
                />
              )}
            </button>
          ))}

          {/* Bottom-anchored global save button — sends only changed fields */}
          <div className="mt-auto">
            {anyDirty && (
              <div className="flex items-center gap-1.5 text-xs text-[#E0A458] mb-2 px-0.5">
                <Circle size={7} className="fill-[#E0A458] text-[#E0A458] unsaved-dot shrink-0" />
                Ulagrede endringer
              </div>
            )}
            <button
              onClick={saveAllChanges}
              disabled={!anyDirty || isSaving}
              className={`w-full flex items-center justify-center gap-2 text-sm font-medium rounded-lg p-2 transition-colors duration-150 ${
                anyDirty && !isSaving
                  ? 'bg-[#8A5A44] hover:bg-[#7A4E3A] text-[#F2EEE7] cursor-pointer'
                  : 'bg-[#3A332E] text-[#6B655D] cursor-not-allowed'
              }`}
            >
              {isSaving ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Lagrer...
                </>
              ) : 'Lagre endringer'
              }
            </button>
            {saveError && (
              <p className="text-xs text-[#C0554A] mt-2 px-0.5">{saveError}</p>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="w-full h-full flex flex-col overflow-hidden">
          <div className="px-4.5 py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <h3 className="font-semibold">{activeTab}</h3>
              {dirtyByTab[activeTab] && <UnsavedHint />}
            </div>
            <button
              onClick={handleClose}
              style={{ border: 'none', background: 'none', fontSize: '20px', cursor: 'pointer' }}
            >
              <X size={18} strokeWidth={1.25} className="cursor-pointer" />
            </button>
          </div>

          <div className="settings-scroll overflow-y-auto px-6 py-4">
            {/* ---------------- NOTIFICATIONS ---------------- */}
            {activeTab === 'Varslinger' && (
              <div className="max-w-md">
                <SectionLabel>Varsler</SectionLabel>
                <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                  Skru på et varsel og velg om det skal sendes til Discord, e-post, eller begge
                </p>
                <NotificationRow
                  title="Tørrvare-varsler"
                  description="Varsle når varer fra tørrvarelisten din er på tilbud"
                  enabled={notifications.dryGoodsAlerts.enabled}
                  onToggle={(v) => updateNotification('dryGoodsAlerts', { enabled: v })}
                  channels={notifications.dryGoodsAlerts.channels}
                  onChannelsChange={(c) => updateNotification('dryGoodsAlerts', { channels: c })}
                />
                <NotificationRow
                  title="Nye tilbud i dashbordet"
                  description="Varsle når nye tilbud dukker opp i oversikten din"
                  enabled={notifications.dashboardNewOffers.enabled}
                  onToggle={(v) => updateNotification('dashboardNewOffers', { enabled: v })}
                  channels={notifications.dashboardNewOffers.channels}
                  onChannelsChange={(c) =>
                    updateNotification('dashboardNewOffers', { channels: c })
                  }
                />
                <NotificationRow
                  title="Ukens beste priser"
                  description="Varer med størst prosentvis avslag denne uken"
                  enabled={notifications.bestDealsWeekly.enabled}
                  onToggle={(v) => updateNotification('bestDealsWeekly', { enabled: v })}
                  channels={notifications.bestDealsWeekly.channels}
                  onChannelsChange={(c) => updateNotification('bestDealsWeekly', { channels: c })}
                />
                <NotificationRow
                  title="Favorittmat"
                  description="Varsle når mat du liker, som kylling eller kjøttdeig, er på tilbud"
                  enabled={notifications.favoriteFoodAlerts.enabled}
                  onToggle={(v) => updateNotification('favoriteFoodAlerts', { enabled: v })}
                  channels={notifications.favoriteFoodAlerts.channels}
                  onChannelsChange={(c) =>
                    updateNotification('favoriteFoodAlerts', { channels: c })
                  }
                />

              </div>
            )}

            {/* ---------------- PREFERENCES ---------------- */}
            {activeTab === 'Preferanser' && (
              <div className="w-full">
                <div className='w-full flex flex-row gap-10'>
                  <div className="max-w-md w-full">
                    <SectionLabel>Butikker som skannes</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                      Skru av/på butikker som er/ikke er i næromerådet ditt
                    </p>
                    {storesLoading && (
                      <p className="text-xs text-[#6B655D] py-2">Henter butikker …</p>
                    )}
                    {storesLoadError && !storesLoading && (
                      <p className="text-xs text-[#C0554A] py-2">{storesLoadError}</p>
                    )}
                    {!storesLoading && !storesLoadError && Object.keys(stores).length === 0 && (
                      <p className="text-xs text-[#6B655D] py-2">Ingen butikker funnet.</p>
                    )}
                    {Object.entries(stores).map(([storeKey, enabled]) => (
                      <SettingRow key={storeKey} title={STORE_LABELS[storeKey] ?? storeKey}>
                        <Toggle
                          checked={enabled}
                          onChange={(v) => setStores((s) => ({ ...s, [storeKey]: v }))}
                        />
                      </SettingRow>
                    ))}
                  </div>
                  <div className="max-w-md w-full">
                    <SectionLabel>Allergier og hensyn</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                      AI-chat assistenten vil ikke anbefale mat som inneholder dine allergier
                    </p>
                    <SettingRow title="Gluten">
                      <Toggle
                        checked={allergies.gluten}
                        onChange={(v) => setAllergies((a) => ({ ...a, gluten: v }))}
                      />
                    </SettingRow>
                    <SettingRow title="Laktose">
                      <Toggle
                        checked={allergies.laktose}
                        onChange={(v) => setAllergies((a) => ({ ...a, laktose: v }))}
                      />
                    </SettingRow>
                    <SettingRow title="Nøtter">
                      <Toggle
                        checked={allergies.nøtter}
                        onChange={(v) => setAllergies((a) => ({ ...a, nøtter: v }))}
                      />
                    </SettingRow>
                    <SettingRow title="Egg">
                      <Toggle
                        checked={allergies.egg}
                        onChange={(v) => setAllergies((a) => ({ ...a, egg: v }))}
                      />
                    </SettingRow>
                    <SettingRow title="Skalldyr">
                      <Toggle
                        checked={allergies.skalldyr}
                        onChange={(v) => setAllergies((a) => ({ ...a, skalldyr: v }))}
                      />
                    </SettingRow>
                  </div>
                </div>

              </div>
            )}

            {/* ---------------- SHOPPING LIST ---------------- */}
            {activeTab === 'Handleliste' && (
              <div className="w-full">
                <div className='w-full flex flex-row gap-10'>
                  <div className="max-w-md w-full">
                    <SectionLabel>Tørrvarer du ofte kjøper</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-3">
                      Legg til varer som ris, mel og sukker, så varsler vi deg når de er på tilbud
                    </p>
                    <ListInput placeholder="F.eks. Ris" onAdd={addDryGood} />
                    <div className="mt-2">
                      {dryGoods.length === 0 ? (
                        <EmptyListHint text="Ingen tørrvarer lagt til enda" />
                      ) : (
                        dryGoods.map((item) => (
                          <ListItem key={item} label={item} onRemove={() => removeDryGood(item)} />
                        ))
                      )}
                    </div>
                  </div>
                  <div className="max-w-md w-full">
                    <SectionLabel>Mat du liker</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-3">
                      F.eks. kylling eller kjøttdeig — brukes til favorittmat-varsler
                    </p>
                    <ListInput placeholder="F.eks. Kylling" onAdd={addFavoriteFood} />
                    <div className="mt-2">
                      {favoriteFoods.length === 0 ? (
                        <EmptyListHint text="Ingen favorittmat lagt til enda" />
                      ) : (
                        favoriteFoods.map((item) => (
                          <ListItem
                            key={item}
                            label={item}
                            onRemove={() => removeFavoriteFood(item)}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </div>

              </div>
            )}

            {/* ---------------- CONFIGURATION ---------------- */}
            {activeTab === 'Konfigurasjon' && (
              <div className="w-full">
                <div className='w-full flex flex-row gap-10'>
                  <div className="max-w-md w-full">
                    <SectionLabel>Google Gemini</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                      Brukes til å tolke og kategorisere tilbud automatisk
                    </p>
                    {geminiKeySet && (
                      <p className="text-xs text-[#6B655D] mb-2">
                        Lagret nøkkel: <span className="font-mono">{geminiKeyPreview}</span>
                      </p>
                    )}
                    <TextField
                      label={geminiKeySet ? 'Ny API-nøkkel (erstatter gjeldende)' : 'API-nøkkel'}
                      placeholder="AIza..."
                      value={geminiApiKey}
                      onChange={setGeminiApiKey}
                      type="password"
                    />

                    <SectionLabel>Discord-webhook</SectionLabel>
                    <SettingRow
                      title="Aktiver webhook"
                      description="Nødvendig for å sende varsler til Discord"
                    >
                      <Toggle checked={webhookEnabled} onChange={setWebhookEnabled} />
                    </SettingRow>
                    {webhookEnabled && (
                      <TextField
                        label="Webhook-URL"
                        placeholder="https://discord.com/api/webhooks/..."
                        value={webhookUrl}
                        onChange={setWebhookUrl}
                      />
                    )}

                    <SectionLabel>SMTP</SectionLabel>
                    <SettingRow
                      title="Aktiver SMTP"
                      description="Nødvendig for å sende varsler på e-post"
                    >
                      <Toggle checked={smtpEnabled} onChange={setSmtpEnabled} />
                    </SettingRow>
                    {smtpEnabled && (
                      <>
                        <TextField
                          label="Vert (host)"
                          placeholder="smtp.gmail.com"
                          value={smtpHost}
                          onChange={setSmtpHost}
                        />
                        <TextField
                          label="Port"
                          placeholder="587"
                          value={smtpPort}
                          onChange={setSmtpPort}
                        />
                        <TextField
                          label="Brukernavn"
                          placeholder="din@epost.no"
                          value={smtpUser}
                          onChange={setSmtpUser}
                        />
                        <TextField
                          label="Passord"
                          placeholder="••••••••"
                          value={smtpPass}
                          onChange={setSmtpPass}
                          type="password"
                        />
                      </>
                    )}
                  </div>
                  <div className="max-w-md w-full">
                    <SectionLabel>Postnummer</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                      Brukes til å finne dine nærmeste/lokale butikker
                    </p>
                    <TextField
                      label="Postnummer"
                      placeholder="1055"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={4}
                      value={postalCode}
                      onChange={(value) => {
                        const digitsOnly = value.replace(/\D/g, "").slice(0, 4);
                        setPostalCode(digitsOnly);
                      }}
                    />
                    <SectionLabel>Budsjett</SectionLabel>
                    <p className="text-xs text-[#9B958C] -mt-1 mb-3">
                      Sett et handlebudsjett for å holde oversikt over forbruket ditt
                    </p>
                    <div className="flex items-end gap-2 py-3.5">
                      <div className="flex-1">
                        <label className="text-sm font-medium text-[#F2EEE7] block mb-2">
                          Beløp (kr)
                        </label>
                        <input
                          type="number"
                          value={budgetAmount}
                          placeholder="500"
                          onChange={(e) => setBudgetAmount(e.target.value)}
                          className="w-full bg-[#1A1613] border border-[#3A332E] rounded-lg px-3 py-2 text-sm text-[#F2EEE7] placeholder:text-[#6B655D] outline-none focus:border-[#8A5A44] transition-colors duration-150"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="text-sm font-medium text-[#F2EEE7] block mb-2">
                          Periode
                        </label>
                        <select
                          value={budgetPeriod}
                          onChange={(e) => setBudgetPeriod(e.target.value as 'uke' | 'måned')}
                          className="w-full bg-[#1A1613] border border-[#3A332E] rounded-lg px-3 py-2 text-sm text-[#F2EEE7] outline-none focus:border-[#8A5A44] transition-colors duration-150 cursor-pointer"
                        >
                          <option value="uke">Per uke</option>
                          <option value="måned">Per måned</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}