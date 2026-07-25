'use client';

import { Bell, Plug, Plus, ShoppingBasket, SlidersHorizontal, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

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
  type = 'text',
}: {
  label: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div className="py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 last:border-b-0">
      <label className="text-sm font-medium text-[#F2EEE7] block mb-2">{label}</label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#1A1613] border border-[#3A332E] rounded-lg px-3 py-2 text-sm text-[#F2EEE7] placeholder:text-[#6B655D] outline-none focus:border-[#8A5A44] transition-colors duration-150"
      />
    </div>
  );
}

export default function Modal({ isOpen, onClose }: ModalProps) {
  const [activeTab, setActiveTab] = useState<string>('Varslinger');

  // Varslinger state — hvert varsel har på/av + hvilke kanaler det sendes på
  const [notifications, setNotifications] = useState<{
    priceDrops: { enabled: boolean; channels: Channel[] };
    newOffers: { enabled: boolean; channels: Channel[] };
    weeklyDigest: { enabled: boolean; channels: Channel[] };
    stockAlerts: { enabled: boolean; channels: Channel[] };
    dryGoodsAlerts: { enabled: boolean; channels: Channel[] };
    dashboardNewOffers: { enabled: boolean; channels: Channel[] };
    bestDealsWeekly: { enabled: boolean; channels: Channel[] };
    favoriteFoodAlerts: { enabled: boolean; channels: Channel[] };
  }>({
    priceDrops: { enabled: true, channels: ['email'] },
    newOffers: { enabled: true, channels: ['discord', 'email'] },
    weeklyDigest: { enabled: false, channels: [] },
    stockAlerts: { enabled: false, channels: [] },
    dryGoodsAlerts: { enabled: true, channels: ['email'] },
    dashboardNewOffers: { enabled: true, channels: [] },
    bestDealsWeekly: { enabled: true, channels: ['discord'] },
    favoriteFoodAlerts: { enabled: true, channels: ['email'] },
  });

  const updateNotification = (
    key: keyof typeof notifications,
    patch: Partial<{ enabled: boolean; channels: Channel[] }>
  ) => {
    setNotifications((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }));
  };

  // Preferanser state
  const [stores, setStores] = useState({
    rema: true,
    kiwi: true,
    coop: true,
    extra: false,
    meny: false,
  });
  const [allergies, setAllergies] = useState({
    gluten: false,
    laktose: false,
    nøtter: false,
    egg: false,
    skalldyr: false,
  });
  const [onlyOffers, setOnlyOffers] = useState(true);
  const [showOutOfStock, setShowOutOfStock] = useState(false);

  // Handleliste state
  const [dryGoods, setDryGoods] = useState<string[]>(['Ris', 'Mel', 'Sukker', 'Havregryn']);
  const [favoriteFoods, setFavoriteFoods] = useState<string[]>(['Kylling', 'Kjøttdeig']);
  const [budgetAmount, setBudgetAmount] = useState('');
  const [budgetPeriod, setBudgetPeriod] = useState<'uke' | 'måned'>('uke');

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

  // Konfigurasjon state
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [smtpHost, setSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState('');
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPass, setSmtpPass] = useState('');
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [smtpEnabled, setSmtpEnabled] = useState(false);

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
      <ScrollbarStyles />
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex flex-row max-w-7xl w-full max-h-9/12 h-full bg-[#211C19] rounded-2xl overflow-hidden text-[#F2EEE7]"
      >
        {/* Sidebar */}
        <div className="bg-[#2A2420] max-w-72 w-full h-full py-4 px-5 shrink-0">
          <h1 className="font-bold">Innstillinger</h1>
          <button
            onClick={() => setActiveTab('Varslinger')}
            className={`mt-6 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${
              activeTab === 'Varslinger' && 'bg-[#b1aeae]/10'
            } hover:bg-[#b1aeae]/10 rounded-lg p-2`}
          >
            <Bell size={17} strokeWidth={1.5} className="cursor-pointer" />
            Varslinger
          </button>
          <button
            onClick={() => setActiveTab('Preferanser')}
            className={`mt-3 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${
              activeTab === 'Preferanser' && 'bg-[#b1aeae]/10'
            } hover:bg-[#b1aeae]/10 rounded-lg p-2`}
          >
            <SlidersHorizontal size={17} strokeWidth={1.5} className="cursor-pointer" />
            Preferanser
          </button>
          <button
            onClick={() => setActiveTab('Handleliste')}
            className={`mt-3 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${
              activeTab === 'Handleliste' && 'bg-[#b1aeae]/10'
            } hover:bg-[#b1aeae]/10 rounded-lg p-2`}
          >
            <ShoppingBasket size={17} strokeWidth={1.5} className="cursor-pointer" />
            Handleliste
          </button>
          <button
            onClick={() => setActiveTab('Konfigurasjon')}
            className={`mt-3 transition-all duration-200 flex items-center gap-1.5 cursor-pointer w-full ${
              activeTab === 'Konfigurasjon' && 'bg-[#b1aeae]/10'
            } hover:bg-[#b1aeae]/10 rounded-lg p-2`}
          >
            <Plug size={17} strokeWidth={1.5} className="cursor-pointer" />
            Konfigurasjon
          </button>
        </div>

        {/* Content */}
        <div className="w-full h-full flex flex-col overflow-hidden">
          <div className="px-4.5 py-3.5 border-b-[0.5px] border-[#F2EEE7]/10 flex items-center justify-between shrink-0">
            <h3 className="font-semibold">{activeTab}</h3>
            <button
              onClick={onClose}
              style={{ border: 'none', background: 'none', fontSize: '20px', cursor: 'pointer' }}
            >
              <X size={18} strokeWidth={1.25} className="cursor-pointer" />
            </button>
          </div>

          <div className="settings-scroll overflow-y-auto px-6 py-4">
            {/* ---------------- VARSLINGER ---------------- */}
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

            {/* ---------------- PREFERANSER ---------------- */}
            {activeTab === 'Preferanser' && (
              <div className="max-w-md">
                <SectionLabel>Butikker som skannes</SectionLabel>
                <SettingRow title="REMA 1000">
                  <Toggle
                    checked={stores.rema}
                    onChange={(v) => setStores((s) => ({ ...s, rema: v }))}
                  />
                </SettingRow>
                <SettingRow title="Kiwi">
                  <Toggle
                    checked={stores.kiwi}
                    onChange={(v) => setStores((s) => ({ ...s, kiwi: v }))}
                  />
                </SettingRow>
                <SettingRow title="Coop Extra">
                  <Toggle
                    checked={stores.coop}
                    onChange={(v) => setStores((s) => ({ ...s, coop: v }))}
                  />
                </SettingRow>
                <SettingRow title="Extra">
                  <Toggle
                    checked={stores.extra}
                    onChange={(v) => setStores((s) => ({ ...s, extra: v }))}
                  />
                </SettingRow>
                <SettingRow title="Meny">
                  <Toggle
                    checked={stores.meny}
                    onChange={(v) => setStores((s) => ({ ...s, meny: v }))}
                  />
                </SettingRow>

                <SectionLabel>Allergier og hensyn</SectionLabel>
                <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                  Vi skjuler varer som inneholder dette der det er mulig
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

                <SectionLabel>Visning</SectionLabel>
                <SettingRow
                  title="Vis kun tilbud"
                  description="Skjul varer uten aktiv rabatt som standard"
                >
                  <Toggle checked={onlyOffers} onChange={setOnlyOffers} />
                </SettingRow>
                <SettingRow
                  title="Vis utsolgte varer"
                  description="Inkluder varer som for øyeblikket ikke er på lager"
                >
                  <Toggle checked={showOutOfStock} onChange={setShowOutOfStock} />
                </SettingRow>
              </div>
            )}

            {/* ---------------- HANDLELISTE ---------------- */}
            {activeTab === 'Handleliste' && (
              <div className="max-w-md">
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

                <button className="mt-4 bg-[#8A5A44] hover:bg-[#7A4E3A] transition-colors duration-150 text-[#F2EEE7] text-sm font-medium rounded-lg px-4 py-2 cursor-pointer">
                  Lagre endringer
                </button>
              </div>
            )}

            {/* ---------------- KONFIGURASJON ---------------- */}
            {activeTab === 'Konfigurasjon' && (
              <div className="max-w-md">
                <SectionLabel>Google Gemini</SectionLabel>
                <p className="text-xs text-[#9B958C] -mt-1 mb-2">
                  Brukes til å tolke og kategorisere tilbud automatisk
                </p>
                <TextField
                  label="API-nøkkel"
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

                <button className="mt-6 bg-[#8A5A44] hover:bg-[#7A4E3A] transition-colors duration-150 text-[#F2EEE7] text-sm font-medium rounded-lg px-4 py-2 cursor-pointer">
                  Lagre endringer
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}