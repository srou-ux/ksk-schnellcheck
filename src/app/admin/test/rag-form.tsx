"use client";

import { visibleFundstellen } from "@/lib/mistral/fundstellen";
import Link from "next/link";
import { useState } from "react";

type RagPruefung = {
  zahlen: { status: "bestanden" | "warnung" | "uebersprungen"; checked: number; lines: string[] };
  library: { ok: boolean; documents: string[]; line: string };
  interne?: string | null;
};

type Konsens = { status: string; line: string; detail: string | null };
type ZeitCheck = { jahr: number; angenommen: boolean; line: string; hinweise: string[] };
type ProzentZeile = { pruefer: string; label: string; status: "belegt" | "nutzerangabe" | "unbekannt" };

type PrueferErgebnis = {
  id: string;
  label: string;
  modell: string;
  ok: boolean;
  answer: string;
  gezeigt: boolean;
  nutzerangaben?: string;
  hinweise?: string[];
  chunks?: string;
};

export function RagForm() {
  const [question, setQuestion] = useState("Was gilt für Reisekosten bei Musikvereinen?");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [pruefung, setPruefung] = useState<RagPruefung | null>(null);
  const [konsens, setKonsens] = useState<Konsens | null>(null);
  const [zeit, setZeit] = useState<ZeitCheck | null>(null);
  const [prozent, setProzent] = useState<ProzentZeile[]>([]);
  const [listeHinweise, setListeHinweise] = useState<string[]>([]);
  const [basis, setBasis] = useState<string | null>(null);
  const [pruefer, setPruefer] = useState<PrueferErgebnis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    setBusy(true);
    setError(null);
    setAnswer(null);
    setSources([]);
    setPruefung(null);
    setKonsens(null);
    setZeit(null);
    setProzent([]);
    setListeHinweise([]);
    setBasis(null);
    setPruefer([]);
    const response = await fetch("/api/mistral-test/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) {
      setError(body.error ?? "Die Frage ist fehlgeschlagen.");
      return;
    }
    const nextAnswer = typeof body.answer === "string" ? body.answer : "";
    const nextSources = Array.isArray(body.sources) ? body.sources.filter((item: unknown): item is string => typeof item === "string") : [];
    setAnswer(nextAnswer);
    setSources(visibleFundstellen(nextAnswer, nextSources));
    setPruefung(body.pruefung && typeof body.pruefung === "object" ? body.pruefung as RagPruefung : null);
    setKonsens(body.konsens && typeof body.konsens === "object" ? body.konsens as Konsens : null);
    setZeit(body.zeit && typeof body.zeit === "object" ? body.zeit as ZeitCheck : null);
    setProzent(Array.isArray(body.prozent) ? body.prozent as ProzentZeile[] : []);
    setListeHinweise(Array.isArray(body.listeHinweise) ? body.listeHinweise.filter((item: unknown): item is string => typeof item === "string") : []);
    setBasis(typeof body.basis === "string" ? body.basis : null);
    setPruefer(Array.isArray(body.pruefer) ? body.pruefer as PrueferErgebnis[] : []);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl">RAG-Test</h1>
        <Link href="/admin" className="text-sm text-ink/70">Zurück zur Library</Link>
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void ask();
        }}
        className="space-y-3 rounded-xl border border-line bg-card p-4"
      >
        <label className="block text-sm">
          Frage
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <button disabled={busy} className="rounded-md bg-stamp px-4 py-2 text-white">{busy ? "Frage läuft …" : "Fragen"}</button>
      </form>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      {answer !== null ? (
        <section className="space-y-3 rounded-xl border border-line bg-card p-4">
          {konsens && konsens.status !== "konsens" ? (
            <p className={`text-sm font-semibold ${konsens.status === "keiner" ? "text-danger" : "text-unclear"}`}>
              {konsens.status === "abweichung"
                ? "NICHT OK — 2/3 ist keine Mehrheitsentscheidung. Die Antwort ist nicht abschließend verlässlich."
                : konsens.status === "keiner"
                  ? konsens.line.includes("drei Läufe")
                    ? "UNGEKLÄRT — die drei Läufe stimmen nicht überein. Zwei von drei reichen nicht."
                    : "UNGEKLÄRT — die Prüfer stimmen nicht überein."
                  : konsens.status === "hinweis"
                    ? "⚠️ Die gültigen Beträge stimmen überein. Historische Werte stehen im Zeit-Check und zählen nicht als Widerspruch."
                    : konsens.line}
            </p>
          ) : null}
          <h2 className="text-2xl">Antwort</h2>
          <p className="whitespace-pre-wrap text-sm">{answer || (pruefer.some((item) => item.gezeigt && !item.ok) ? "⚠️ Prüfer nicht erreichbar" : "Mistral hat keinen Antworttext geliefert.")}</p>
          <h2 className="text-2xl">Fundstelle</h2>
          {sources.length === 0 ? (
            <p className="text-sm text-unclear">Keine Fundstelle erkannt.</p>
          ) : (
            <ul className="list-disc space-y-1 pl-5 text-sm">
              {sources.map((source) => <li key={source}>{source}</li>)}
            </ul>
          )}
          {konsens ? (
            <div className="rounded-md border border-line bg-paper px-4 py-3 text-sm">
              <h2 className="text-2xl">Prüfung</h2>
              <p className={`mt-2 ${konsens.status === "konsens" ? "text-ok" : konsens.status === "keiner" ? "text-danger" : "text-unclear"}`}>Konsens: {konsens.line}</p>
              {konsens.detail ? <p className="mt-1 text-unclear">{konsens.detail}</p> : null}
              {basis ? <p className="mt-2 text-danger">{basis}</p> : null}
              {listeHinweise.map((line) => <p key={line} className="mt-2 text-unclear">{line}</p>)}
              {zeit?.angenommen ? <p className="mt-2 text-unclear">Bezugsjahr angenommen: {zeit.jahr}</p> : null}
              {zeit?.line ? <p className={`mt-2 ${zeit.hinweise.length > 0 ? "text-danger" : "text-ok"}`}>{zeit.line}</p> : null}
              {zeit && zeit.hinweise.length > 0 ? (
                <ul className="mt-1 space-y-1 text-danger">
                  {zeit.hinweise.map((line) => <li key={line}>{line}</li>)}
                </ul>
              ) : null}
              {prozent.length > 0 ? (
                <div className="mt-3">
                  <p className="font-semibold">Prozent-Check</p>
                  {prozent.map((row) => (
                    <p key={`${row.pruefer}-${row.label}`} className={row.status === "unbekannt" ? "text-danger" : ""}>
                      {row.label} | {row.status === "belegt" ? "belegt" : row.status === "nutzerangabe" ? "Nutzerangabe" : "🔴 unbekannt"} ({row.pruefer})
                    </p>
                  ))}
                </div>
              ) : null}
              {pruefer.flatMap((item) => (item.hinweise ?? []).map((line) => `${item.id}: ${line}`)).map((line) => (
                <p key={line} className={`mt-1 ${line.includes("🔴") ? "text-danger" : "text-unclear"}`}>{line.replace(/^P\d+: /, "")}</p>
              ))}
              <div className="mt-3">
                <p className="font-semibold">Nutzerangaben-Prüfung (aus der Frage)</p>
                <p className="mt-1 whitespace-pre-wrap">{pruefer.find((item) => item.gezeigt)?.nutzerangaben || "—"}</p>
                {pruefer.filter((item) => !item.gezeigt).map((item) => (
                  <details key={`${item.id}-nutzer`} className="mt-2">
                    <summary className="cursor-pointer">{item.label}</summary>
                    <p className="mt-1 whitespace-pre-wrap">{item.nutzerangaben || "—"}</p>
                  </details>
                ))}
              </div>
              {pruefung?.zahlen.status === "bestanden" ? (
                <p className="mt-2 text-ok">Zahl-Check: ✅ {pruefung.zahlen.checked} Beträge geprüft, alle belegt</p>
              ) : pruefung ? (
                <ul className={`mt-2 space-y-1 ${pruefung.zahlen.status === "warnung" ? "text-danger" : "text-unclear"}`}>
                  {pruefung.zahlen.lines.map((line) => <li key={line}>Zahl-Check: {line}</li>)}
                </ul>
              ) : null}
              {pruefung ? (
                pruefung.library.ok ? (
                  <p className="mt-2 text-ok">Library-Bezug: ✅ {pruefung.library.documents.join(", ")}</p>
                ) : (
                  <p className="mt-2 text-danger">Library-Bezug: ⚠️ {pruefung.library.line}</p>
                )
              ) : null}
              {pruefung?.interne ? <p className="mt-2 text-danger">{pruefung.interne}</p> : null}
              <div className="mt-4 space-y-2">
                <p className="font-semibold">Prüfer-Antworten</p>
                {pruefer.map((item) => (
                  <details key={item.id} className="rounded-md border border-line px-3 py-2">
                    <summary className="cursor-pointer">
                      {item.label}{item.gezeigt ? " — aktuell angezeigt" : ""}
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap">{item.ok ? item.answer || "Mistral hat keinen Antworttext geliefert." : "⚠️ Prüfer nicht erreichbar"}</p>
                  </details>
                ))}
                <p className="font-semibold">Erhaltene Chunks</p>
                {pruefer.map((item) => (
                  <details key={`${item.id}-chunks`} className="rounded-md border border-line px-3 py-2">
                    <summary className="cursor-pointer">{item.label}</summary>
                    <p className="mt-2">Erhielt Chunks: {item.chunks || "keine"}</p>
                  </details>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
