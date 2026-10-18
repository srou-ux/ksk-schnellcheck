"use client";

import { useEffect, useState } from "react";

interface Message {
  id: string;
  mode: string;
  role: string;
  content: string;
}

export function ChatPanel({ caseId, defaultMode }: { caseId: string; defaultMode: "nutzer" | "steuerberater" }) {
  const [mode, setMode] = useState(defaultMode);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    void fetch(`/api/cases/${caseId}/chat`).then(async (response) => {
      const body = await response.json();
      setMessages(body.messages ?? []);
    });
  }, [caseId]);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const response = await fetch(`/api/cases/${caseId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, mode }),
    });
    const body = await response.json();
    setPending(false);
    if (!response.ok) {
      setError(body.error ?? "Die Frage konnte nicht gestellt werden.");
      return;
    }
    setQuestion("");
    const refreshed = await fetch(`/api/cases/${caseId}/chat`);
    const data = await refreshed.json();
    setMessages(data.messages ?? []);
  }

  return (
    <section className="rounded-xl border border-line bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-xl">Fragen zum Bericht</h3>
        <label className="text-sm">
          Modus
          <select value={mode} onChange={(event) => setMode(event.target.value as "nutzer" | "steuerberater")} className="ml-2 rounded-md border border-line bg-paper px-2 py-1">
            <option value="nutzer">Nutzer</option>
            <option value="steuerberater">Fundstellen</option>
          </select>
        </label>
      </div>
      <p className="mt-2 text-sm text-ink/70">Der Chat zitiert den Bericht und, falls verbunden, die aktive Referenz-Library. Er stuft nicht um und rechnet nicht.</p>
      <ul className="mt-4 space-y-3">
        {messages.filter((message) => message.mode === mode).map((message) => (
          <li key={message.id} className={message.role === "user" ? "text-sm" : "rounded-md bg-paper p-3 text-sm"}>
            <span className="text-ink/50">{message.role === "user" ? "Sie" : "Bericht"} · {message.mode === "steuerberater" ? "Fundstellen" : "Alltagssprache"}</span>
            <p className="mt-1 whitespace-pre-wrap">{message.content}</p>
          </li>
        ))}
      </ul>
      <form onSubmit={send} className="mt-4 flex flex-col gap-2">
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} className="rounded-md border border-line bg-paper px-3 py-2 text-sm" placeholder="Was bedeutet die Einstufung dieser Position?" />
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <button disabled={pending} className="self-start rounded-md bg-stamp px-4 py-2 text-sm text-white disabled:opacity-60">{pending ? "Liest …" : "Fragen"}</button>
      </form>
    </section>
  );
}
