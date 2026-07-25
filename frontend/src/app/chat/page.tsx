"use client";

import { useState } from "react";

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  text: string;
}

const PLACEHOLDER_RESPONSES = [
  "Dette er en forhåndsvisning av AI-assistenten — den er ikke koblet til noen modell ennå.",
  "Når dette er satt opp kan jeg svare på spørsmål om ukens tilbud, foreslå oppskrifter, og mer.",
  "Legg til Gemini API-nøkkel under Innstillinger når backend-koblingen er klar.",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 0,
      role: "assistant",
      text: "Hei! Jeg er AI-assistenten for Tilbudsradaren. Spør meg om ukens tilbud (foreløpig demo-svar).",
    },
  ]);
  const [input, setInput] = useState("");

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage: ChatMessage = { id: Date.now(), role: "user", text: trimmed };
    const reply: ChatMessage = {
      id: Date.now() + 1,
      role: "assistant",
      text: PLACEHOLDER_RESPONSES[Math.floor(Math.random() * PLACEHOLDER_RESPONSES.length)],
    };

    setMessages((prev) => [...prev, userMessage, reply]);
    setInput("");
  }

  return (
    <main className="flex min-h-screen flex-col bg-[#f6f3ec] text-[#1c1a16]">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6 py-8 sm:px-10">
        <div className="flex-1 space-y-3">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-[#1c1a16] text-[#f6f3ec]"
                    : "border border-[#1c1a16]/10 bg-white text-[#1c1a16]"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={sendMessage} className="mt-6 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Spør om ukens tilbud …"
            className="flex-1 rounded-full border border-[#1c1a16]/15 bg-white px-4 py-2.5 text-sm placeholder:text-[#1c1a16]/35 focus:border-[#1c1a16]/40 focus:outline-none"
          />
          <button
            type="submit"
            className="shrink-0 rounded-full bg-[#1c1a16] px-5 py-2.5 text-sm font-medium text-[#f6f3ec] transition-colors hover:bg-[#1c1a16]/85"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}