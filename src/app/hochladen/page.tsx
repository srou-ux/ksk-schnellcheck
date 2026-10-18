"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";
import { usePruefstand } from "@/components/pruef-provider";
import {
  STATUS_LABEL,
  euro,
  type Dokument,
  type Positionsstatus,
} from "@/lib/pruefstand";

const SCHRITTE = ["Extrahieren", "Prüfen", "Fertig"] as const;

const RAHMEN: Record<Positionsstatus, string> = {
  ZAEHLT: "border-ok bg-ok-bg",
  OFFEN: "border-amber bg-amber-bg",
  SPERRE: "border-danger bg-danger-bg",
  AUSGESCHLOSSEN: "border-line bg-card",
  AUSGENOMMEN: "border-line bg-card",
};

const BADGE: Record<Positionsstatus, string> = {
  ZAEHLT: "bg-ok text-white",
  OFFEN: "bg-amber text-white",
  SPERRE: "bg-danger text-white",
  AUSGESCHLOSSEN: "bg-navy text-white",
  AUSGENOMMEN: "bg-ink/70 text-white",
};

function HochladenInhalt() {
  const router = useRouter();
  const suche = useSearchParams();
  const { stand, dokumentAnlegen, setFokus } = usePruefstand();
  const dateiRef = useRef<HTMLInputElement>(null);
  const [ziehen, setZiehen] = useState(false);
  const [schritt, setSchritt] = useState<number | null>(null);
  const [aktivId, setAktivId] = useState<string | null>(suche.get("dokument"));
  const dokument =
    stand.dokumente.find((eintrag) => eintrag.id === (aktivId ?? suche.get("dokument"))) ??
    stand.dokumente[0] ??
    null;
  const auditZurPosition = (positionId: string) => stand.audit.filter((eintrag) => eintrag.positionId === positionId);

  async function verarbeiten(datei: File) {
    setSchritt(0);
    await warten(500);
    setSchritt(1);
    await warten(500);
    setSchritt(2);
    const angelegt = dokumentAnlegen(datei.name);
    setAktivId(angelegt.id);
    await warten(300);
    setSchritt(null);
  }

  function klaeren(dokumentAktuell: Dokument, positionId: string) {
    setFokus(positionId);
    router.push(`/chat?position=${positionId}&dokument=${dokumentAktuell.id}`);
  }

  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-semibold text-navy">Vorschlag — Ihre Bestätigung erforderlich</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-navy">Rechnung hochladen</h1>
        <p className="mt-2 max-w-2xl text-sm text-ink/70">
          PDF, Foto, Excel oder Word. Ohne KI legt der Prüfstand einen Vorschlag an. Offene Positionen entscheiden Sie.
        </p>
      </header>

      <section
        onDragOver={(event) => {
          event.preventDefault();
          setZiehen(true);
        }}
        onDragLeave={() => setZiehen(false)}
        onDrop={(event) => {
          event.preventDefault();
          setZiehen(false);
          const datei = event.dataTransfer.files[0];
          if (datei) void verarbeiten(datei);
        }}
        data-dropzone="rechnung"
        className={`rounded-lg border-2 border-dashed px-6 py-14 text-center ${ziehen ? "border-navy bg-paper" : "border-line bg-card"}`}
      >
        <p className="text-lg font-medium text-navy">Rechnung hierher ziehen oder klicken</p>
        <p className="mt-2 text-sm text-ink/60">PDF, PNG, JPG, Excel, Word</p>
        <input
          ref={dateiRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,.xls,.xlsx,.doc,.docx,.csv,.txt,application/pdf,image/*"
          className="sr-only"
          onChange={(event) => {
            const datei = event.target.files?.[0];
            event.target.value = "";
            if (datei) void verarbeiten(datei);
          }}
        />
        <button
          type="button"
          onClick={() => dateiRef.current?.click()}
          disabled={schritt !== null}
          className="mt-6 rounded-md bg-navy px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Datei auswählen
        </button>
      </section>

      {schritt !== null ? (
        <ol className="grid gap-3 sm:grid-cols-3">
          {SCHRITTE.map((name, index) => {
            const erreicht = index <= schritt;
            const aktuell = index === schritt;
            return (
              <li
                key={name}
                className={`rounded-lg border px-4 py-3 text-sm ${erreicht ? "border-navy bg-card text-navy" : "border-line text-ink/40"}`}
              >
                <span className="font-semibold">{index + 1}</span>
                <span className="ml-2">{name}</span>
                {aktuell ? <span className="mt-1 block text-xs">läuft</span> : null}
                {index < schritt ? <span className="mt-1 block text-xs text-ok">erledigt</span> : null}
              </li>
            );
          })}
        </ol>
      ) : null}

      {dokument ? (
        <section className="space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-navy">{dokument.name}</h2>
              <p className="text-sm text-ink/60">Vorschlag — Ihre Bestätigung erforderlich</p>
            </div>
          </div>
          <ul className="space-y-3">
            {dokument.positionen.map((position) => (
              <li key={position.id} className={`rounded-lg border-2 px-4 py-4 ${RAHMEN[position.status]}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{position.text}</p>
                    <p className="mt-1 text-sm text-ink/70">
                      {position.betrag == null ? "kein Einzelbetrag" : euro(position.betrag)}
                      <span className="mx-2">·</span>
                      {position.fundstelle}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-medium">{position.regel}</span>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${BADGE[position.status]}`}>{STATUS_LABEL[position.status]}</span>
                  </div>
                </div>
                {position.status === "OFFEN" ? (
                  <button
                    type="button"
                    onClick={() => klaeren(dokument, position.id)}
                    className="mt-3 rounded-md border border-amber bg-white px-3 py-1.5 text-sm font-medium text-amber"
                  >
                    Im Chat klären
                  </button>
                ) : null}
                {auditZurPosition(position.id).length > 0 ? (
                  <ul className="mt-3 space-y-1 text-xs text-ink/70">
                    {auditZurPosition(position.id).map((eintrag) => (
                      <li key={eintrag.id}>{eintrag.zeit} — {eintrag.text}</li>
                    ))}
                  </ul>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <p className="text-sm text-ink/60">
          Nach dem Hochladen erscheint die Positionsansicht. Zum Gespräch: <Link href="/chat" className="text-navy underline">Chat</Link>
        </p>
      )}
    </div>
  );
}

function warten(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function HochladenPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink/60">Die Seite wird geladen …</p>}>
      <HochladenInhalt />
    </Suspense>
  );
}
