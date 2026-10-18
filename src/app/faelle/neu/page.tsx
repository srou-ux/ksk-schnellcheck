"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewCasePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [audience, setAudience] = useState<"verein" | "steuerberater">("verein");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const response = await fetch("/api/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, audience }),
    });
    const body = await response.json();
    setPending(false);
    if (!response.ok) {
      setError(body.error ?? "Der Fall konnte nicht angelegt werden.");
      return;
    }
    router.push(`/faelle/${body.case.id}`);
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-xl space-y-6 rounded-xl border border-line bg-card p-6">
      <div>
        <h1 className="text-3xl">Neue Prüfung</h1>
        <p className="mt-2 text-sm text-ink/70">Ohne Anmeldung. Der Fall bleibt auf diesem System, bis Sie ihn löschen.</p>
      </div>
      <label className="block text-sm">
        Name des Falls
        <input value={title} onChange={(event) => setTitle(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" placeholder="Verlag Beispiel, Rechnung März" />
      </label>
      <fieldset className="space-y-2 text-sm">
        <legend>Für wen ist der Bericht?</legend>
        <label className="flex gap-2"><input type="radio" checked={audience === "verein"} onChange={() => setAudience("verein")} /> Verein oder KMU, Alltagssprache</label>
        <label className="flex gap-2"><input type="radio" checked={audience === "steuerberater"} onChange={() => setAudience("steuerberater")} /> Ausführliche Fundstellen</label>
      </fieldset>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      <button disabled={pending} className="rounded-md bg-stamp px-4 py-2 text-white disabled:opacity-60">{pending ? "Wird angelegt …" : "Fall anlegen"}</button>
    </form>
  );
}
