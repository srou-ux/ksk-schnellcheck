"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { usePruefstand } from "@/components/pruef-provider";
import {
  ENTSCHEIDUNG_LABEL,
  euro,
  type Entscheidung,
} from "@/lib/pruefstand";

function ChatInhalt() {
  const suche = useSearchParams();
  const positionId = suche.get("position");
  const { bereit, stand, fokusId, setFokus, position, entscheide, gespraech } = usePruefstand();
  const [frage, setFrage] = useState("");
  const [fehler, setFehler] = useState<string | null>(null);
  const [wartet, setWartet] = useState(false);
  const geoeffnet = useRef<string | null>(null);
  const zielId = positionId ?? fokusId;
  const ziel = position(zielId);

  useEffect(() => {
    if (positionId) setFokus(positionId);
  }, [positionId, setFokus]);

  useEffect(() => {
    if (!bereit || !positionId || geoeffnet.current === positionId) return;
    geoeffnet.current = positionId;
    const schon = stand.nachrichten.some((nachricht) => nachricht.positionId === positionId && nachricht.rolle === "assistent");
    const merker = `ksk-assistent-start:${positionId}`;
    if (schon || window.sessionStorage.getItem(merker) === "1") return;
    window.sessionStorage.setItem(merker, "1");
    setWartet(true);
    setFehler(null);
    void antwortHolen("Bitte diese Position einordnen.", positionId).finally(() => setWartet(false));
    // Der Erstaufruf hängt an der Positions-ID aus der URL, nicht an jedem Speicherstand.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bereit, positionId]);

  async function antwortHolen(text: string, bezug: string | null) {
    const pos = position(bezug);
    const response = await fetch("/api/assistent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ frage: text, position: pos, dokumente: stand.dokumente }),
    });
    const body = await response.json();
    if (!response.ok) {
      if (bezug) window.sessionStorage.removeItem(`ksk-assistent-start:${bezug}`);
      setFehler(body.error ?? "Der Assistent antwortet gerade nicht.");
      return;
    }
    gespraech(text, bezug, body);
  }

  async function senden(event: React.FormEvent) {
    event.preventDefault();
    const text = frage.trim();
    if (text.length < 2) return;
    setFrage("");
    setWartet(true);
    setFehler(null);
    await antwortHolen(text, zielId);
    setWartet(false);
  }

  function entscheiden(aktion: Entscheidung, bezug: string | undefined) {
    if (!bezug) return;
    entscheide(bezug, aktion);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
      <section className="flex min-h-[32rem] flex-col rounded-lg border border-line bg-card">
        <header className="border-b border-line px-5 py-4">
          <h1 className="text-xl font-semibold text-navy">KSK-Assistent</h1>
          <p className="mt-1 text-sm text-ink/60">Vorschlag — Ihre Bestätigung erforderlich. Der Assistent rechnet nicht selbst.</p>
        </header>
        <ul className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {stand.nachrichten.length === 0 ? (
            <li className="text-sm text-ink/60">Fragen Sie zum Beispiel: Muss die Übersetzerin rein?</li>
          ) : null}
          {stand.nachrichten.map((nachricht) => (
            <li key={nachricht.id} className={nachricht.rolle === "nutzer" ? "ml-8 text-sm" : "rounded-lg border border-line bg-paper p-4 text-sm"}>
              <p className="text-xs font-semibold text-navy/70">{nachricht.rolle === "nutzer" ? "Sie" : "Assistent"}</p>
              <p className="mt-2 whitespace-pre-wrap">{nachricht.text}</p>
              {nachricht.vorschlag && nachricht.rolle === "assistent" ? (
                <div className="mt-4 space-y-3">
                  <dl className="grid gap-2 sm:grid-cols-2">
                    <div>
                      <dt className="text-xs text-ink/50">Position</dt>
                      <dd>{nachricht.vorschlag.position}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-ink/50">Betrag</dt>
                      <dd>{nachricht.vorschlag.betrag == null ? "—" : euro(nachricht.vorschlag.betrag)}</dd>
                    </div>
                    <div className="sm:col-span-2">
                      <dt className="text-xs text-ink/50">Rechtslage</dt>
                      <dd>{nachricht.vorschlag.rechtslage}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-ink/50">Konsequenz</dt>
                      <dd>{nachricht.vorschlag.konsequenzEuro == null ? "—" : euro(nachricht.vorschlag.konsequenzEuro)}</dd>
                    </div>
                  </dl>
                  <div className="flex flex-wrap gap-2">
                    {nachricht.vorschlag.optionen.map((option) => {
                      const aktuell = position(nachricht.positionId ?? null);
                      const entschieden = aktuell != null && aktuell.status !== "OFFEN";
                      return (
                        <button
                          key={option}
                          type="button"
                          disabled={!nachricht.positionId || entschieden}
                          onClick={() => entscheiden(option, nachricht.positionId)}
                          className="rounded-md border border-navy px-3 py-1.5 text-sm font-medium text-navy hover:bg-navy hover:text-white disabled:opacity-40"
                        >
                          {ENTSCHEIDUNG_LABEL[option]}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}
            </li>
          ))}
          {wartet ? <li className="text-sm text-ink/50">Der Assistent liest die Position …</li> : null}
        </ul>
        {fehler ? <p className="px-5 text-sm text-danger">{fehler}</p> : null}
        <form onSubmit={(event) => void senden(event)} className="border-t border-line p-4">
          <label className="block text-sm">
            Frage
            <textarea
              value={frage}
              onChange={(event) => setFrage(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-line px-3 py-2"
              placeholder="Muss die Übersetzerin rein?"
            />
          </label>
          <button type="submit" disabled={wartet} className="mt-3 rounded-md bg-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            Fragen
          </button>
        </form>
      </section>
      <aside className="rounded-lg border border-line bg-card p-4">
        <h2 className="text-sm font-semibold text-navy">Kontext</h2>
        {ziel ? (
          <dl className="mt-3 space-y-2 text-sm">
            <div>
              <dt className="text-xs text-ink/50">Position</dt>
              <dd>{ziel.text}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink/50">Betrag</dt>
              <dd>{ziel.betrag == null ? "—" : euro(ziel.betrag)}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink/50">Status</dt>
              <dd>{ziel.status}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink/50">Regel</dt>
              <dd>{ziel.regel}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-3 text-sm text-ink/60">Keine Position ausgewählt. Offene Zeilen öffnen den Chat mit Kontext.</p>
        )}
        {stand.audit.length > 0 ? (
          <div className="mt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-ink/50">Audit</h3>
            <ul className="mt-2 space-y-2 text-xs text-ink/70">
              {stand.audit.slice(0, 6).map((eintrag) => (
                <li key={eintrag.id}>{eintrag.zeit} — {eintrag.text}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink/60">Der Chat wird geladen …</p>}>
      <ChatInhalt />
    </Suspense>
  );
}
