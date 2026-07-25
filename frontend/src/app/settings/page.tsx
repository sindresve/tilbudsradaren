"use client";

import { useState } from "react";

export default function SettingsPage() {
  // Local-only state for now — not persisted. Wiring to /api/settings comes later.
  const [discordWebhook, setDiscordWebhook] = useState("");
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("");
  const [smtpUsername, setSmtpUsername] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [emailTo, setEmailTo] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [weeklyBudget, setWeeklyBudget] = useState("");

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    // Placeholder — no backend endpoint yet.
    alert("Innstillinger er ikke koblet til serveren ennå. Dette er kun en forhåndsvisning.");
  }

  return (
    <main className="min-h-screen bg-[#f6f3ec] text-[#1c1a16]">

      <div className="mx-auto max-w-3xl px-6 py-8 sm:px-10">
        <div className="mb-6 rounded-lg border border-[#8a5a3d]/30 bg-[#8a5a3d]/5 px-4 py-3 text-sm text-[#8a5a3d]">
          Denne siden er foreløpig kun en forhåndsvisning — endringer lagres ikke ennå.
        </div>

        <form onSubmit={handleSave} className="flex flex-col gap-8">
          {/* Discord */}
          <section className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
            <h2 className="text-sm font-semibold">Discord-varsling</h2>
            <p className="mt-1 text-xs text-[#1c1a16]/50">
              Send ukentlige tilbud til en Discord-kanal via webhook.
            </p>
            <div className="mt-4">
              <label className="text-xs font-medium text-[#1c1a16]/70">Webhook-URL</label>
              <input
                type="text"
                value={discordWebhook}
                onChange={(e) => setDiscordWebhook(e.target.value)}
                placeholder="https://discord.com/api/webhooks/…"
                className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
              />
            </div>
          </section>

          {/* Email / SMTP */}
          <section className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
            <h2 className="text-sm font-semibold">E-postvarsling (SMTP)</h2>
            <p className="mt-1 text-xs text-[#1c1a16]/50">
              Send en oppsummering av ukens tilbud på e-post.
            </p>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-[#1c1a16]/70">SMTP-vert</label>
                <input
                  type="text"
                  value={smtpHost}
                  onChange={(e) => setSmtpHost(e.target.value)}
                  placeholder="smtp.gmail.com"
                  className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-[#1c1a16]/70">Port</label>
                <input
                  type="number"
                  value={smtpPort}
                  onChange={(e) => setSmtpPort(e.target.value)}
                  placeholder="587"
                  className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-[#1c1a16]/70">Brukernavn</label>
                <input
                  type="text"
                  value={smtpUsername}
                  onChange={(e) => setSmtpUsername(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-[#1c1a16]/70">Passord</label>
                <input
                  type="password"
                  value={smtpPassword}
                  onChange={(e) => setSmtpPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-[#1c1a16]/70">Send til (e-post)</label>
                <input
                  type="email"
                  value={emailTo}
                  onChange={(e) => setEmailTo(e.target.value)}
                  placeholder="deg@eksempel.no"
                  className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
                />
              </div>
            </div>
          </section>

          {/* AI */}
          <section className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
            <h2 className="text-sm font-semibold">AI-assistent</h2>
            <p className="mt-1 text-xs text-[#1c1a16]/50">
              Brukes av AI-assistenten for å svare på spørsmål om ukens tilbud.
            </p>
            <div className="mt-4">
              <label className="text-xs font-medium text-[#1c1a16]/70">Gemini API-nøkkel</label>
              <input
                type="password"
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
                placeholder="••••••••••••••••"
                className="mt-1 w-full rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
              />
            </div>
          </section>

          {/* Budget */}
          <section className="rounded-xl border border-[#1c1a16]/10 bg-white p-5">
            <h2 className="text-sm font-semibold">Budsjett</h2>
            <p className="mt-1 text-xs text-[#1c1a16]/50">
              Ukentlig handlebudsjett, brukes til varsler og oversikt.
            </p>
            <div className="mt-4">
              <label className="text-xs font-medium text-[#1c1a16]/70">Ukentlig budsjett (kr)</label>
              <input
                type="number"
                min={0}
                value={weeklyBudget}
                onChange={(e) => setWeeklyBudget(e.target.value)}
                placeholder="1500"
                className="mt-1 w-full max-w-xs rounded-lg border border-[#1c1a16]/15 px-3 py-2 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
              />
            </div>
          </section>

          <button
            type="submit"
            className="self-start rounded-full bg-[#1c1a16] px-6 py-2.5 text-sm font-medium text-[#f6f3ec] transition-colors hover:bg-[#1c1a16]/85"
          >
            Lagre innstillinger
          </button>
        </form>
      </div>
    </main>
  );
}