"use client";

import Link from "next/link";
import { usePruefstand } from "@/components/pruef-provider";
import {
  GRENZWERT_EURO,
  JAHR,
  berichtstext,
  dokumentStatus,
  euro,
  jahresbild,
  type AmpelStufe,
} from "@/lib/pruefstand";

const AMPEL: Record<AmpelStufe, string> = {
  leer: "border-line bg-card text-ink",
  ok: "border-ok bg-ok-bg text-ok",
  offen: "border-amber bg-amber-bg text-amber",
  sperre: "border-danger bg-danger-bg text-danger",
  "ueber-grenze": "border-navy bg-card text-navy",
};

export default function DashboardPage() {
  const { bereit, stand } = usePruefstand();
  const bild = jahresbild(stand.dokumente);
  const balken = bild.stufe === "sperre" ? "bg-danger" : bild.stufe === "offen" ? "bg-amber" : bild.stufe === "ok" ? "bg-ok" : "bg-navy";

  function exportieren() {
    const datei = new Blob([berichtstext(stand)], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(datei);
    const link = document.createElement("a");
    link.href = url;
    link.download = `pruefbericht-${JAHR}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-medium text-navy">Jahr {JAHR}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-navy">Dashboard</h1>
      </header>

      <section className={`rounded-lg border-2 p-6 md:p-8 ${AMPEL[bild.stufe]}`}>
        <p className="text-sm font-semibold tracking-wide">Jahres-Ampel</p>
        <p className="mt-2 text-4xl font-semibold tracking-tight">{bereit ? bild.titel : "…"}</p>
        <dl className="mt-6 grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs uppercase tracking-wide opacity-70">Jahressumme</dt>
            <dd className="mt-1 text-2xl font-semibold">{euro(bild.summe)}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide opacity-70">Grenzwert</dt>
            <dd className="mt-1 text-2xl font-semibold">{euro(GRENZWERT_EURO)}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide opacity-70">Offene Positionen</dt>
            <dd className="mt-1 text-2xl font-semibold">{bild.offen}</dd>
          </div>
        </dl>
        <div className="mt-6">
          <div className="mb-2 flex justify-between text-xs">
            <span>Fortschritt bis zum Grenzwert</span>
            <span>{bild.fortschritt} %</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/80">
            <div className={`h-full ${balken}`} style={{ width: `${bild.fortschritt}%` }} />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Link href="/hochladen" className="rounded-lg border border-line bg-card p-5 hover:border-navy">
          <h2 className="text-lg font-semibold text-navy">Rechnungen hochladen</h2>
          <p className="mt-2 text-sm text-ink/70">PDF, Foto, Excel oder Word. Danach sehen Sie jede Position.</p>
        </Link>
        <Link href="/hochladen" className="rounded-lg border border-line bg-card p-5 hover:border-navy">
          <h2 className="text-lg font-semibold text-navy">Offene Positionen ({bild.offen})</h2>
          <p className="mt-2 text-sm text-ink/70">Offene Zeilen klären Sie im Chat. Nichts wird still entschieden.</p>
        </Link>
        <button type="button" onClick={exportieren} className="rounded-lg border border-line bg-card p-5 text-left hover:border-navy">
          <h2 className="text-lg font-semibold text-navy">Prüfbericht exportieren</h2>
          <p className="mt-2 text-sm text-ink/70">Textdatei mit Status, Fundstelle und Ihren Entscheidungen.</p>
        </button>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-navy">Erfasste Dokumente</h2>
        {stand.dokumente.length === 0 ? (
          <p className="mt-3 rounded-lg border border-dashed border-line bg-card px-4 py-8 text-sm text-ink/70">
            Noch keine Rechnung. Laden Sie die erste Datei hoch.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-line overflow-hidden rounded-lg border border-line bg-card">
            {stand.dokumente.map((dokument) => {
              const status = dokumentStatus(dokument);
              const badge =
                status === "Sperre" ? "bg-danger-bg text-danger" : status === "Offen" ? "bg-amber-bg text-amber" : "bg-ok-bg text-ok";
              return (
                <li key={dokument.id}>
                  <Link href={`/hochladen?dokument=${dokument.id}`} className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-paper">
                    <span>
                      <span className="block font-medium">{dokument.name}</span>
                      <span className="text-xs text-ink/60">{new Date(dokument.zeit).toLocaleString("de-DE")} · {dokument.positionen.length} Positionen</span>
                    </span>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${badge}`}>{status}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
