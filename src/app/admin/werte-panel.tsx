"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ABGABEGRENZE, ABGABESATZ, BEREICH_ABGABESATZ, BEREICH_GRENZE } from "@/lib/register-kennungen";

type Eintrag = {
  id: string;
  gruppe: string;
  version: number;
  wertExakt: string | null;
  einheit: "euro" | "prozent" | "hinweis";
  gueltigAb: string;
  gueltigBis: string | null;
  quelle: string;
  fundstelle: string | null;
  dokumentstand: string | null;
  anwendungsbereich: string | null;
  freigabe: "entwurf" | "freigegeben";
  beschreibung: string;
  bedingung: string | null;
};

function statusVon(eintrag: Eintrag, heute: string): "Entwurf" | "freigegeben" | "historisch" {
  if (eintrag.freigabe !== "freigegeben") return "Entwurf";
  if (eintrag.gueltigBis && eintrag.gueltigBis < heute) return "historisch";
  return "freigegeben";
}

function wertText(eintrag: Eintrag): string {
  if (!eintrag.wertExakt) return "ohne Betrag";
  const text = eintrag.wertExakt.replace(".", ",");
  return eintrag.einheit === "prozent" ? `${text} %` : `${text} €`;
}

export function WertePanel() {
  const [eintraege, setEintraege] = useState<Eintrag[]>([]);
  const [heute, setHeute] = useState("");
  const [hinweis, setHinweis] = useState("");
  const [jahreswechsel, setJahreswechsel] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [id, setId] = useState("");
  const [gruppe, setGruppe] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [betrag, setBetrag] = useState("");
  const [einheit, setEinheit] = useState<"euro" | "prozent">("euro");
  const [gueltigAb, setGueltigAb] = useState("");
  const [gueltigBis, setGueltigBis] = useState("");
  const [quelle, setQuelle] = useState("");
  const [fundstelle, setFundstelle] = useState("");
  const [dokumentstand, setDokumentstand] = useState("");
  const [anwendungsbereich, setAnwendungsbereich] = useState("");

  const load = useCallback(async () => {
    const response = await fetch("/api/mistral-test/zahlen-werte");
    const body = await response.json();
    if (!response.ok) {
      setError(body.error ?? "Die Werteliste konnte nicht gelesen werden.");
      setEintraege([]);
      return;
    }
    setError(null);
    setEintraege(Array.isArray(body.eintraege) ? body.eintraege : []);
    setHeute(typeof body.heute === "string" ? body.heute : "");
    setHinweis(typeof body.hinweis === "string" ? body.hinweis : "");
    setJahreswechsel(typeof body.jahreswechsel === "string" ? body.jahreswechsel : null);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const gruppen = [...new Map(eintraege.map((eintrag) => [eintrag.gruppe, eintrag.beschreibung])).entries()];

  function bereichFuer(kennung: string): string {
    if (kennung === ABGABESATZ) return BEREICH_ABGABESATZ;
    if (kennung === ABGABEGRENZE) return BEREICH_GRENZE;
    return "";
  }

  function uebernehmen(eintrag: Eintrag) {
    setId(eintrag.freigabe === "entwurf" ? eintrag.id : "");
    setGruppe(eintrag.gruppe);
    setBeschreibung(eintrag.beschreibung);
    setBetrag(eintrag.wertExakt?.replace(".", ",") ?? "");
    setEinheit(eintrag.einheit === "prozent" ? "prozent" : "euro");
    setGueltigAb(eintrag.gueltigAb);
    setGueltigBis(eintrag.gueltigBis ?? "");
    setQuelle(eintrag.quelle);
    setFundstelle(eintrag.fundstelle ?? "");
    setDokumentstand(eintrag.dokumentstand ?? "");
    setAnwendungsbereich(eintrag.anwendungsbereich || bereichFuer(eintrag.gruppe));
    setSuccess(null);
    setError(null);
  }

  async function senden(aktion: "entwurf" | "freigeben" | "bearbeiten") {
    setBusy(true);
    setError(null);
    setSuccess(null);
    const response = await fetch("/api/mistral-test/zahlen-werte", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aktion,
        id: aktion === "bearbeiten" ? id : undefined,
        gruppe,
        beschreibung,
        betrag,
        einheit,
        gueltig_ab: gueltigAb,
        gueltig_bis: gueltigBis || null,
        quelle,
        fundstelle,
        dokumentstand,
        anwendungsbereich,
      }),
    });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) {
      setError(body.error ?? "Die Werteliste konnte nicht gespeichert werden.");
      return;
    }
    setEintraege(Array.isArray(body.eintraege) ? body.eintraege : []);
    setHeute(typeof body.heute === "string" ? body.heute : heute);
    setId("");
    setBetrag("");
    setSuccess(aktion === "freigeben"
      ? "Die Angaben sind vollständig. Der Wert gilt jetzt für Berechnungen. Das System bestätigt damit nicht, dass er fachlich richtig ist."
      : "Der Entwurf ist gespeichert. Freigegebene Werte und ihre Gültigkeit sind unverändert.");
  }

  async function speichern(event: FormEvent, aktion: "entwurf" | "freigeben" | "bearbeiten") {
    event.preventDefault();
    await senden(aktion);
  }

  return (
    <section className="space-y-4 rounded-xl border border-line bg-card p-4">
      <h2 className="text-2xl">Zahlenregister</h2>
      <p className="text-sm text-ink/70">Gespeichert in SQLite. Importierte Werte aus daten/zahlen-werte.json bleiben Entwürfe. Eine Freigabe legt eine neue Version an und verändert die Vorlagendatei nicht.</p>
      {hinweis ? <p className="text-sm text-ink/80">{hinweis}</p> : null}
      {jahreswechsel ? <p className="text-sm font-semibold text-unclear">{jahreswechsel}</p> : null}
      {gruppen.map(([name, titel]) => (
        <div key={name}>
          <h3 className="font-semibold">{titel}</h3>
          <p className="text-sm text-ink/70">{name}</p>
          <table className="mt-2 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="py-1 pr-3">Status</th>
                <th className="py-1 pr-3">Version</th>
                <th className="py-1 pr-3">Wert</th>
                <th className="py-1 pr-3">gültig ab</th>
                <th className="py-1 pr-3">gültig bis</th>
                <th className="py-1 pr-3">Quelle</th>
                <th className="py-1 pr-3">Fundstelle</th>
                <th className="py-1 pr-3">Dokumentstand</th>
                <th className="py-1 pr-3">Anwendungsbereich</th>
                <th className="py-1"> </th>
              </tr>
            </thead>
            <tbody>
              {eintraege.filter((eintrag) => eintrag.gruppe === name).map((eintrag) => (
                <tr key={eintrag.id} className="border-b border-line/60" data-testid="register-zeile">
                  <td className="py-1 pr-3" data-testid="register-status">{statusVon(eintrag, heute)}</td>
                  <td className="py-1 pr-3">{eintrag.version}</td>
                  <td className="py-1 pr-3">{wertText(eintrag)}</td>
                  <td className="py-1 pr-3">{eintrag.gueltigAb}</td>
                  <td className="py-1 pr-3">{eintrag.gueltigBis ?? "offen"}</td>
                  <td className="py-1 pr-3">{eintrag.quelle || "—"}</td>
                  <td className="py-1 pr-3">{eintrag.fundstelle ?? "—"}</td>
                  <td className="py-1 pr-3">{eintrag.dokumentstand ?? "—"}</td>
                  <td className="py-1 pr-3">{eintrag.anwendungsbereich ?? "—"}</td>
                  <td className="py-1">
                    {eintrag.freigabe === "entwurf" ? (
                      <button type="button" className="text-stamp" onClick={() => uebernehmen(eintrag)}>Bearbeiten</button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {eintraege.find((eintrag) => eintrag.gruppe === name)?.bedingung ? <p className="text-sm">{eintraege.find((eintrag) => eintrag.gruppe === name)?.bedingung}</p> : null}
        </div>
      ))}
      <form onSubmit={(event) => void speichern(event, id ? "bearbeiten" : "entwurf")} className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm">
          Kennung
          <input value={gruppe} onChange={(event) => setGruppe(event.target.value.trim().toLowerCase())} list="register-kennungen" className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" placeholder="neue_kennung" />
          <datalist id="register-kennungen">
            {gruppen.map(([name, titel]) => <option key={name} value={name}>{titel}</option>)}
          </datalist>
        </label>
        <label className="block text-sm">
          Beschreibung
          <input value={beschreibung} onChange={(event) => setBeschreibung(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          Betrag
          <input value={betrag} onChange={(event) => setBetrag(event.target.value)} inputMode="decimal" className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          Einheit
          <select value={einheit} onChange={(event) => setEinheit(event.target.value === "prozent" ? "prozent" : "euro")} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2">
            <option value="euro">Euro</option>
            <option value="prozent">Prozent</option>
          </select>
        </label>
        <label className="block text-sm">
          gültig ab
          <input type="date" value={gueltigAb} onChange={(event) => setGueltigAb(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          gültig bis
          <input type="date" value={gueltigBis} onChange={(event) => setGueltigBis(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          Quelle
          <input value={quelle} onChange={(event) => setQuelle(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          Fundstelle
          <input value={fundstelle} onChange={(event) => setFundstelle(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        <label className="block text-sm">
          Dokumentstand
          <input value={dokumentstand} onChange={(event) => setDokumentstand(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" placeholder="2026-10-05" />
        </label>
        <label className="block text-sm">
          Anwendungsbereich
          <input value={anwendungsbereich} onChange={(event) => setAnwendungsbereich(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" placeholder={bereichFuer(gruppe) || "Anwendungsbereich"} />
        </label>
        <div className="flex flex-wrap gap-3 sm:col-span-2">
          <button disabled={busy} className="rounded-md border border-line px-4 py-2">{busy ? "Speichert …" : id ? "Entwurf ändern" : "Als Entwurf speichern"}</button>
          <button type="button" disabled={busy} onClick={() => void senden("freigeben")} className="rounded-md bg-stamp px-4 py-2 text-white">Freigeben</button>
        </div>
      </form>
      {success ? <p className="text-sm text-ok">{success}</p> : null}
      {error ? <p className="text-sm text-danger">{error}</p> : null}
    </section>
  );
}
