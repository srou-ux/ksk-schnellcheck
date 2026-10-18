import { existsSync, mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { KonsensErgebnis } from "@/lib/model-consensus";
import { ladeFreigegebene, zahlenWertePfad as registerPfad, type RegisterEintrag } from "@/lib/zahlen-register";

export type Freigabe = "entwurf" | "freigegeben";

export type WertZeile = {
  betrag: number;
  gueltig_ab: string;
  gueltig_bis: string | null;
  version?: number;
  einheit?: "euro" | "prozent";
  quelle?: string;
  freigabe?: Freigabe;
};

export type WerteGruppe = {
  name: string;
  beschreibung: string;
  quelle: string;
  werte: WertZeile[];
  einheit?: "euro" | "prozent";
  thema?: string;
  stichworte?: string[];
  bedingung?: string;
};

export type Grenze = {
  value: number;
  unit: "euro" | "prozent";
  jahr: number | null;
  label: string;
};

export type ProzentStatus = "belegt" | "nutzerangabe" | "unbekannt";

export type ProzentZeile = {
  pruefer: string;
  label: string;
  status: ProzentStatus;
};

export type ZahlenListe = {
  liste_stand: string;
  letzte_aenderung: string;
  wertegruppen: WerteGruppe[];
};

export type ZeitCheck = {
  jahr: number;
  angenommen: boolean;
  line: string;
  hinweise: string[];
};

const DATE = /^\d{4}-\d{2}-\d{2}$/;

export function zahlenWertePfad(): string {
  return registerPfad();
}

export function vorlageAusDatei(file = zahlenWertePfad()): ZahlenListe {
  return liesJson(file);
}

function liesJson(file: string): ZahlenListe {
  let raw: string;
  try {
    raw = readFileSync(file, "utf8");
  } catch {
    throw new Error("Die Werteliste daten/zahlen-werte.json fehlt.");
  }
  const parsed = JSON.parse(raw) as ZahlenListe;
  if (!Array.isArray(parsed.wertegruppen)) throw new Error("Die Werteliste daten/zahlen-werte.json ist ungültig.");
  return parsed;
}

function anzeigeBetrag(eintrag: RegisterEintrag): number | null {
  if (eintrag.einheit === "euro" && eintrag.wertCent != null) return eintrag.wertCent / 100;
  if (eintrag.einheit === "prozent" && eintrag.wertBps != null) return eintrag.wertBps / 100;
  return null;
}

function listeAusEintraegen(eintraege: RegisterEintrag[]): ZahlenListe {
  const gruppen: WerteGruppe[] = [];
  for (const eintrag of eintraege) {
    let gruppe = gruppen.find((item) => item.name === eintrag.gruppe);
    if (!gruppe) {
      gruppe = {
        name: eintrag.gruppe,
        beschreibung: eintrag.beschreibung,
        quelle: eintrag.quelle,
        werte: [],
        einheit: eintrag.einheit === "prozent" ? "prozent" : "euro",
        thema: eintrag.thema ?? undefined,
        stichworte: eintrag.stichworte,
        bedingung: eintrag.bedingung ?? undefined,
      };
      gruppen.push(gruppe);
    }
    const betrag = anzeigeBetrag(eintrag);
    if (betrag == null) continue;
    gruppe.werte.push({
      betrag,
      gueltig_ab: eintrag.gueltigAb,
      gueltig_bis: eintrag.gueltigBis,
      version: eintrag.version,
      einheit: eintrag.einheit === "prozent" ? "prozent" : "euro",
      quelle: eintrag.quelle,
      freigabe: eintrag.freigabe,
    });
  }
  for (const gruppe of gruppen) gruppe.werte.sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab) || (a.version ?? 0) - (b.version ?? 0));
  const zeiten = eintraege.map((eintrag) => eintrag.createdAt.slice(0, 10)).sort();
  return {
    liste_stand: zeiten[0] ?? new Date().toISOString().slice(0, 10),
    letzte_aenderung: zeiten[zeiten.length - 1] ?? new Date().toISOString().slice(0, 10),
    wertegruppen: gruppen,
  };
}

export function ladeZahlenWerte(file?: string): ZahlenListe {
  if (file && path.resolve(file) !== path.resolve(zahlenWertePfad())) return liesJson(file);
  return listeAusEintraegen(ladeFreigegebene());
}

export function schreibeZahlenWerte(liste: ZahlenListe, file: string): void {
  if (path.resolve(file) === path.resolve(zahlenWertePfad())) {
    throw new Error("Die Vorlagendatei daten/zahlen-werte.json wird nicht überschrieben.");
  }
  const payload = `${JSON.stringify(liste, null, 2)}\n`;
  const directory = path.dirname(file);
  mkdirSync(directory, { recursive: true });
  const temp = `${file}.tmp`;
  const backup = `${file}.bak`;
  try {
    writeFileSync(temp, payload, "utf8");
    if (existsSync(file)) renameSync(file, backup);
    renameSync(temp, file);
    if (existsSync(backup)) unlinkSync(backup);
  } catch {
    try {
      if (!existsSync(file) && existsSync(backup)) renameSync(backup, file);
    } catch {
      // Die Sicherung bleibt liegen, die unvollständige Datei wird nicht zur Liste.
    }
    try {
      if (existsSync(temp)) unlinkSync(temp);
    } catch {
      // Die temporäre Datei ist nicht die Liste.
    }
    throw new Error("Die Werteliste konnte nicht gespeichert werden.");
  }
}

export function formatProzent(value: number): string {
  return `${value.toFixed(1).replace(".", ",")} %`;
}

export function formatBetrag(betrag: number): string {
  const negative = betrag < 0;
  const absolute = Math.abs(betrag);
  const [whole, fraction] = absolute.toFixed(Number.isInteger(absolute) ? 0 : 2).split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const body = fraction && fraction !== "00" ? `${grouped},${fraction}` : grouped;
  return `${negative ? "-" : ""}${body} €`;
}

export function formatDatum(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}.${month}.${year}`;
}

function isoDatum(value: string): boolean {
  if (!DATE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

export function fensterEnthaeltJahr(zeile: WertZeile, jahr: number): boolean {
  const anfang = `${jahr}-01-01`;
  const ende = `${jahr}-12-31`;
  if (zeile.gueltig_ab > ende) return false;
  if (zeile.gueltig_bis && zeile.gueltig_bis < anfang) return false;
  return true;
}

export function bezugsjahr(frage: string, heute = new Date()): { jahr: number; angenommen: boolean } {
  const match = frage.match(/\b(?:19|20)\d{2}\b/);
  if (match) return { jahr: Number(match[0]), angenommen: false };
  return { jahr: heute.getFullYear(), angenommen: true };
}

export function einheitVon(gruppe: WerteGruppe): "euro" | "prozent" {
  if (gruppe.einheit === "prozent" || gruppe.name === "abgabesatz") return "prozent";
  return "euro";
}

function gruppenLabel(gruppe: WerteGruppe): string {
  if (gruppe.name === "abgabepflichtgrenze_veranstalter") return "Abgabepflichtgrenze Veranstalter";
  if (gruppe.name === "bagatellgrenze_zahlungsvorgang") return "Bagatellgrenze je Zahlungsvorgang";
  if (gruppe.name === "abgabesatz") return "Abgabesatz";
  return gruppe.beschreibung.trim() || gruppe.name;
}

function formatWert(gruppe: WerteGruppe, betrag: number): string {
  return einheitVon(gruppe) === "prozent" ? formatProzent(betrag) : formatBetrag(betrag);
}

function quellenKuerzel(quelle: string): string {
  const info = quelle.match(/info[_ -]?(\d+)/i);
  if (info) return `Info_${info[1]}`;
  return quelle.replace(/\.pdf$/i, "");
}

export function werteFuerJahr(gruppe: WerteGruppe, jahr: number): WertZeile[] {
  return gruppe.werte.filter((zeile) => fensterEnthaeltJahr(zeile, jahr)).sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
}

export function wertFuerJahr(gruppe: WerteGruppe, jahr: number): WertZeile | null {
  const anfang = `${jahr}-01-01`;
  const ende = `${jahr}-12-31`;
  const deckend = gruppe.werte.filter((zeile) => zeile.gueltig_ab <= anfang && (zeile.gueltig_bis === null || zeile.gueltig_bis >= ende));
  return deckend.length === 1 ? deckend[0] : null;
}

function trifftStichwort(frage: string, stichwort: string): boolean {
  const needle = stichwort.trim().toLowerCase();
  if (!needle) return false;
  if (needle.length <= 3) return new RegExp(`\\b${needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(frage);
  return frage.toLowerCase().includes(needle);
}

function passendeGruppen(frage: string, liste: ZahlenListe): WerteGruppe[] {
  return liste.wertegruppen.filter((gruppe) => {
    const worte = gruppe.stichworte ?? (gruppe.thema ? [gruppe.thema] : []);
    return worte.some((wort) => trifftStichwort(frage, wort));
  });
}

export function alleThemenBetraege(frage: string, liste: ZahlenListe): Array<{ value: number; unit: "euro" | "prozent" }> {
  const gesehen = new Set<string>();
  const treffer: Array<{ value: number; unit: "euro" | "prozent" }> = [];
  for (const gruppe of passendeGruppen(frage, liste)) {
    const unit = einheitVon(gruppe);
    for (const zeile of gruppe.werte) {
      const key = `${unit}:${zeile.betrag}`;
      if (gesehen.has(key)) continue;
      gesehen.add(key);
      treffer.push({ value: zeile.betrag, unit });
    }
  }
  return treffer;
}

export function relevanteBetraege(frage: string, liste: ZahlenListe, jahr: number): Array<{ value: number; unit: "euro" | "prozent" }> {
  const gesehen = new Set<string>();
  const treffer: Array<{ value: number; unit: "euro" | "prozent" }> = [];
  for (const gruppe of passendeGruppen(frage, liste)) {
    const zeile = wertFuerJahr(gruppe, jahr);
    if (!zeile) continue;
    const unit = einheitVon(gruppe);
    const key = `${unit}:${zeile.betrag}`;
    if (gesehen.has(key)) continue;
    gesehen.add(key);
    treffer.push({ value: zeile.betrag, unit });
  }
  return treffer;
}

export function relevanteWerte(frage: string, liste: ZahlenListe, jahr: number): string[] {
  return relevanteBetraege(frage, liste, jahr).map((treffer) => treffer.unit === "prozent" ? formatProzent(treffer.value) : formatBetrag(treffer.value));
}

export function f05Hinweis(input: {
  nenntKeine: boolean;
  frage: string;
  jahr: number;
  liste: ZahlenListe;
  prueferLabel: string;
}): string | null {
  if (!input.nenntKeine) return null;
  const werte = relevanteWerte(input.frage, input.liste, input.jahr);
  if (werte.length === 0) return null;
  const pruefer = input.prueferLabel.match(/Prüfer\s+\d+/)?.[0] ?? input.prueferLabel;
  return `⚠️ ${pruefer} nennt keine Zahlen — Dokument enthält laut Liste: ${werte.join(", ")}. Lesefehler wahrscheinlich.`;
}

export function kontextBlock(liste: ZahlenListe, jahr: number): string {
  const zeilen = liste.wertegruppen.flatMap((gruppe) => {
    const wert = wertFuerJahr(gruppe, jahr);
    if (!wert) return [];
    const quelle = wert.quelle ?? gruppe.quelle;
    return [`- ${gruppenLabel(gruppe)}: ${formatWert(gruppe, wert.betrag)} (Quelle: ${quellenKuerzel(quelle)})`];
  });
  return [
    `## Kontext (vom System bereitgestellt — verbindlich, Stand: ${liste.liste_stand})`,
    `Bezugsjahr: ${jahr}`,
    "Aktuell gültige Werte (aus dem Zahlenregister, nur freigegeben):",
    ...zeilen,
    "Werte anderer Jahre sind für dieses Bezugsjahr NICHT gültig.",
  ].join("\n");
}

function gleicheBetrag(links: number, rechts: number): boolean {
  return Math.abs(links - rechts) < 0.001;
}

export type BetragImJahr = "gueltig" | "historisch" | "fremd";

export function stehtInListe(value: number, unit: "euro" | "prozent", liste: ZahlenListe): boolean {
  return liste.wertegruppen.some((gruppe) => einheitVon(gruppe) === unit && gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, value)));
}

export function betragImJahr(value: number, unit: "euro" | "prozent", liste: ZahlenListe, jahr: number): BetragImJahr {
  const zeilen = liste.wertegruppen
    .filter((gruppe) => einheitVon(gruppe) === unit)
    .flatMap((gruppe) => gruppe.werte.filter((zeile) => gleicheBetrag(zeile.betrag, value)));
  if (zeilen.length === 0) return "fremd";
  return zeilen.some((zeile) => fensterEnthaeltJahr(zeile, jahr)) ? "gueltig" : "historisch";
}

export function nurGueltigeBetraege(keys: string[], labels: string[], liste: ZahlenListe, jahr: number): { keys: string[]; labels: string[] } {
  const behalten = keys.map((key, index) => ({ key, label: labels[index] ?? "" })).filter((item) => {
    const value = Number(item.key);
    return Number.isFinite(value) && betragImJahr(value, "euro", liste, jahr) === "gueltig";
  });
  return { keys: behalten.map((item) => item.key), labels: behalten.map((item) => item.label).filter(Boolean) };
}

function prueferKurz(label: string): string {
  return label.match(/Prüfer\s+\d+/)?.[0] ?? label;
}

function labelFuer(nennung: Grenze, gruppe: WerteGruppe | undefined): string {
  if (gruppe) return formatWert(gruppe, nennung.value);
  return nennung.unit === "prozent" ? formatProzent(nennung.value) : formatBetrag(nennung.value);
}

export type ZeitHinweis = { text: string; ausserhalb: boolean };

export function zeitHinweisEintraege(nennungen: Grenze[], liste: ZahlenListe, bezugsjahrWert: number, prueferLabel: string): ZeitHinweis[] {
  const pruefer = prueferKurz(prueferLabel);
  const hinweise: ZeitHinweis[] = [];
  const gesehen = new Set<string>();
  for (const nennung of nennungen) {
    const pruefjahr = nennung.jahr ?? bezugsjahrWert;
    const key = `${nennung.unit}:${nennung.value.toFixed(2)}:${pruefjahr}`;
    if (gesehen.has(key)) continue;
    gesehen.add(key);
    const gruppen = liste.wertegruppen.filter((gruppe) => einheitVon(gruppe) === nennung.unit);
    const zeilen = gruppen.flatMap((gruppe) => gruppe.werte.filter((zeile) => gleicheBetrag(zeile.betrag, nennung.value)));
    if (zeilen.length === 0 || zeilen.some((zeile) => fensterEnthaeltJahr(zeile, pruefjahr))) continue;
    const gruppe = gruppen.find((item) => item.werte.some((zeile) => gleicheBetrag(zeile.betrag, nennung.value)));
    const label = labelFuer(nennung, gruppe);
    const beendet = zeilen
      .filter((zeile) => zeile.gueltig_bis && zeile.gueltig_bis < `${pruefjahr}-01-01`)
      .sort((a, b) => (b.gueltig_bis ?? "").localeCompare(a.gueltig_bis ?? ""));
    const kuenftig = zeilen
      .filter((zeile) => zeile.gueltig_ab > `${pruefjahr}-12-31`)
      .sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
    const ausserhalb = betragImJahr(nennung.value, nennung.unit, liste, bezugsjahrWert) === "historisch";
    const text = nennung.jahr != null && beendet[0]?.gueltig_bis
      ? `⚠️ Zeit-Check: ${label} gilt nicht für ${nennung.jahr}, sondern nur bis ${formatDatum(beendet[0].gueltig_bis)} (${pruefer})`
      : nennung.jahr != null && kuenftig[0]
        ? `⚠️ Zeit-Check: ${label} gilt nicht für ${nennung.jahr}, sondern erst ab ${formatDatum(kuenftig[0].gueltig_ab)} (${pruefer})`
        : beendet[0]?.gueltig_bis
          ? `⚠️ Zeit-Check: ${label} gilt nur bis ${formatDatum(beendet[0].gueltig_bis)} (${pruefer})`
          : kuenftig[0]
            ? `⚠️ Zeit-Check: ${label} gilt erst ab ${formatDatum(kuenftig[0].gueltig_ab)} (${pruefer})`
            : `⚠️ Zeit-Check: ${label} gilt im Bezugsjahr ${pruefjahr} nicht (${pruefer})`;
    hinweise.push({ text, ausserhalb });
  }
  return hinweise;
}

export function zeitHinweise(nennungen: Grenze[], liste: ZahlenListe, bezugsjahrWert: number, prueferLabel: string): string[] {
  return zeitHinweisEintraege(nennungen, liste, bezugsjahrWert, prueferLabel).map((eintrag) => eintrag.text);
}

export function klassifiziereProzent(value: number, frage: string, liste: ZahlenListe): ProzentStatus {
  const gruppen = liste.wertegruppen.filter((gruppe) => einheitVon(gruppe) === "prozent");
  if (gruppen.some((gruppe) => gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, value)))) return "belegt";
  const inFrage = frage.match(/\d+(?:[.,]\d+)?\s*%/g)?.some((raw) => {
    const parsed = Number(raw.replace("%", "").replace(/\s/g, "").replace(",", "."));
    return Number.isFinite(parsed) && gleicheBetrag(parsed, value);
  });
  return inFrage ? "nutzerangabe" : "unbekannt";
}

export function zeitErgebnis(input: {
  jahr: number;
  angenommen: boolean;
  hinweise: string[];
}): ZeitCheck {
  return {
    jahr: input.jahr,
    angenommen: input.angenommen,
    hinweise: input.hinweise,
    line: input.hinweise.length > 0 ? "📅 Zeit-Check: ⚠️" : `📅 Zeit-Check: ✅ Werte passen zum Bezugsjahr ${input.jahr}`,
  };
}

export function mitZeitabweichung(konsens: KonsensErgebnis, hinweise: ZeitHinweis[], hatGueltige = true): KonsensErgebnis {
  if (hinweise.length === 0 || konsens.status !== "konsens") return konsens;
  const verletzung = hinweise.filter((hinweis) => !hinweis.ausserhalb);
  if (verletzung.length > 0) {
    return {
      status: "abweichung",
      line: "⚠️ Abweichung — Zeit-Check, kein Konsens 3/3",
      detail: verletzung.map((hinweis) => hinweis.text).join(" — "),
    };
  }
  if (!hatGueltige) {
    return {
      status: "hinweis",
      line: "⚠️ Gültige Werte konsistent — historische Werte im Zeit-Check",
      detail: hinweise.map((hinweis) => hinweis.text).join(" — "),
    };
  }
  return konsens;
}

export function jahreswechselHinweis(heute = new Date()): string | null {
  if (heute.getMonth() < 9) return null;
  return `⚠️ Für ${heute.getFullYear() + 1} prüfen!`;
}

export function ergaenzeZeile(liste: ZahlenListe, input: {
  gruppe: string;
  betrag: number;
  gueltig_ab: string;
  gueltig_bis: string | null;
}, heute: string): ZahlenListe {
  if (!isoDatum(heute)) throw new Error("Das Änderungsdatum ist ungültig.");
  if (!Number.isFinite(input.betrag) || input.betrag <= 0) throw new Error("Der Betrag fehlt.");
  if (!isoDatum(input.gueltig_ab)) throw new Error("Der Beginn ist kein Datum.");
  if (input.gueltig_bis !== null && !isoDatum(input.gueltig_bis)) throw new Error("Das Ende ist kein Datum.");
  if (input.gueltig_bis && input.gueltig_bis < input.gueltig_ab) throw new Error("Das Ende liegt vor dem Anfang.");
  const next = structuredClone(liste);
  const gruppe = next.wertegruppen.find((item) => item.name === input.gruppe);
  if (!gruppe) throw new Error("Die Wertegruppe gibt es nicht.");
  const doppelt = gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, input.betrag) && zeile.gueltig_ab === input.gueltig_ab && zeile.gueltig_bis === input.gueltig_bis);
  if (doppelt) throw new Error("Diese Zeile steht schon in der Liste.");
  gruppe.werte.push({ betrag: input.betrag, gueltig_ab: input.gueltig_ab, gueltig_bis: input.gueltig_bis });
  gruppe.werte.sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
  next.letzte_aenderung = heute;
  return next;
}
