import { readFileSync } from "node:fs";
import path from "node:path";
import { getDb, korrigiereImportfreigaben } from "@/lib/db";
import { istBerechnungskennung, type RegisterSnapshot } from "@/lib/register-kennungen";

export type Freigabe = "entwurf" | "freigegeben";
export type Einheit = "euro" | "prozent" | "hinweis";

export type RegisterEintrag = {
  id: string;
  gruppe: string;
  version: number;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  einheit: Einheit;
  gueltigAb: string;
  gueltigBis: string | null;
  quelle: string;
  fundstelle: string | null;
  dokumentstand: string | null;
  anwendungsbereich: string | null;
  freigabe: Freigabe;
  freigabeNachweis: string | null;
  herkunft: string | null;
  beschreibung: string;
  thema: string | null;
  stichworte: string[];
  bedingung: string | null;
  createdAt: string;
};

export type WertEingabe = {
  gruppe: string;
  beschreibung?: string;
  betrag: string;
  einheit: "euro" | "prozent";
  gueltigAb: string;
  gueltigBis: string | null;
  quelle?: string;
  fundstelle?: string;
  dokumentstand?: string;
  anwendungsbereich?: string;
  thema?: string;
  stichworte?: string[];
  bedingung?: string;
};

export type Auswahl =
  | { ok: true; eintrag: RegisterEintrag }
  | { ok: false; grund: "fehlt" | "mehrdeutig" | "unbekannt" | "einheit"; meldung: string };

type SqlZeile = {
  id: string;
  gruppe: string;
  version: number;
  betrag: number | null;
  einheit: string;
  gueltig_ab: string;
  gueltig_bis: string | null;
  quelle: string;
  freigabe: string;
  beschreibung: string;
  thema: string | null;
  stichworte_json: string | null;
  bedingung: string | null;
  created_at: string;
  wert_cent: number | null;
  wert_exakt: string | null;
  wert_bps: number | null;
  anwendungsbereich: string | null;
  fundstelle: string | null;
  dokumentstand: string | null;
  freigabe_nachweis: string | null;
  herkunft: string | null;
};

type VorlageZeile = {
  gruppe: string;
  beschreibung: string;
  quelle: string;
  thema: string | null;
  stichworte: string[];
  bedingung: string | null;
  einheit: Einheit;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  gueltigAb: string;
  gueltigBis: string | null;
};

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const KENNUNG = /^[a-z][a-z0-9_]{1,63}$/;
const OFFEN = "9999-12-31";

const VOLLSTAENDIGKEIT = "Vollständigkeit der Angaben geprüft. Keine Aussage zur fachlichen Richtigkeit.";

export function zahlenWertePfad(): string {
  return path.join(process.cwd(), "daten", "zahlen-werte.json");
}

export function parseWert(einheit: "euro" | "prozent", raw: string): { wertExakt: string; wertCent: number | null; wertBps: number | null } {
  const text = raw.trim().replace(/\s/g, "").replace("€", "").replace("%", "");
  if (!/^\d+(?:[.,]\d+)?$/.test(text)) {
    throw new Error("Der Wert muss eine positive Zahl mit Punkt oder Komma sein.");
  }
  const [wholeRaw, fracRaw = ""] = text.replace(",", ".").split(".");
  if (fracRaw.length > 2) {
    throw new Error(einheit === "euro"
      ? "Geldbeträge dürfen höchstens zwei Nachkommastellen haben. Es wird nicht mit Fließkomma gerundet."
      : "Sätze dürfen höchstens zwei Nachkommastellen haben, damit sie in Basispunkten aufgehen.");
  }
  const whole = wholeRaw.replace(/^0+(?=\d)/, "");
  if (einheit === "euro") {
    const cents = Number(`${whole}${fracRaw.padEnd(2, "0")}`);
    if (!Number.isSafeInteger(cents) || cents <= 0) {
      throw new Error("Der Geldbetrag muss größer als 0 Cent sein und in eine Ganzzahl passen.");
    }
    return { wertExakt: `${whole}.${fracRaw.padEnd(2, "0")}`, wertCent: cents, wertBps: null };
  }
  const bps = Number(`${whole}${fracRaw.padEnd(2, "0")}`);
  if (!Number.isSafeInteger(bps) || bps <= 0 || bps > 10000) {
    throw new Error("Der Satz muss größer als 0 und höchstens 100 Prozent sein.");
  }
  const frac = fracRaw.replace(/0+$/, "");
  return { wertExakt: frac.length === 0 ? whole : `${whole}.${frac}`, wertCent: null, wertBps: bps };
}

export function snapshotVon(eintrag: RegisterEintrag): RegisterSnapshot {
  return {
    id: eintrag.id,
    kennung: eintrag.gruppe,
    anwendungsbereich: eintrag.anwendungsbereich,
    wertExakt: eintrag.wertExakt,
    wertCent: eintrag.wertCent,
    wertBps: eintrag.wertBps,
    einheit: eintrag.einheit,
    gueltigAb: eintrag.gueltigAb,
    gueltigBis: eintrag.gueltigBis,
    quelle: eintrag.quelle,
    fundstelle: eintrag.fundstelle,
    dokumentstand: eintrag.dokumentstand,
    freigabe: eintrag.freigabe,
  };
}

export function importiereVorlage(file = zahlenWertePfad()): void {
  korrigiereImportfreigaben();
  const zeilen = liesVorlageZeilen(file);
  const database = getDb();
  const existing = database.prepare("SELECT * FROM zahlen_register").all() as SqlZeile[];
  const backfills: Array<{ row: SqlZeile; zeile: VorlageZeile }> = [];
  const pending: VorlageZeile[] = [];
  for (const zeile of zeilen) {
    const match = existing.find((row) => gleicheVorlage(row, zeile));
    if (!match) {
      pending.push(zeile);
      continue;
    }
    if (!match.freigabe_nachweis && !match.wert_exakt && zeile.wertExakt) backfills.push({ row: match, zeile });
  }
  if (pending.length === 0 && backfills.length === 0) return;
  const stamp = new Date().toISOString();
  database.exec("BEGIN IMMEDIATE");
  try {
    const revision = database.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
      VALUES (?, ?, 'exaktwert_gesetzt', ?, ?, ?)`);
    const fill = database.prepare(`UPDATE zahlen_register
      SET wert_exakt = ?, wert_cent = ?, wert_bps = ?, herkunft = COALESCE(herkunft, 'import')
      WHERE id = ? AND freigabe_nachweis IS NULL AND wert_exakt IS NULL`);
    for (const item of backfills) {
      revision.run(crypto.randomUUID(), item.row.id, JSON.stringify(item.row), "Exakter Wert aus der JSON-Vorlage ergänzt. Betrag und Gültigkeit bleiben unverändert.", stamp);
      fill.run(item.zeile.wertExakt, item.zeile.wertCent, item.zeile.wertBps, item.row.id);
    }
    const insert = database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'entwurf', ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 'import')`);
    for (const zeile of pending) {
      const version = naechsteVersion(zeile.gruppe);
      insert.run(
        `import:${zeile.gruppe}:${zeile.gueltigAb}:${zeile.wertExakt ?? "hinweis"}`,
        zeile.gruppe,
        version,
        zeile.einheit,
        zeile.gueltigAb,
        zeile.gueltigBis,
        zeile.quelle,
        zeile.beschreibung,
        zeile.thema,
        JSON.stringify(zeile.stichworte),
        zeile.bedingung,
        stamp,
        zeile.wertCent,
        zeile.wertExakt,
        zeile.wertBps,
        zeile.beschreibung,
      );
    }
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    if (istUnique(error)) return;
    throw error;
  }
}

export function ladeEintraege(): RegisterEintrag[] {
  importiereVorlage();
  const rows = getDb().prepare("SELECT * FROM zahlen_register ORDER BY gruppe, version, gueltig_ab").all() as SqlZeile[];
  return rows.map(mapEintrag);
}

export function ladeFreigegebene(): RegisterEintrag[] {
  return ladeEintraege().filter((eintrag) => eintrag.freigabe === "freigegeben" && eintrag.freigabeNachweis);
}

export function legeEntwurfAn(input: WertEingabe): RegisterEintrag {
  const geprueft = pruefeEntwurf(input);
  const database = getDb();
  const id = crypto.randomUUID();
  const stamp = new Date().toISOString();
  database.exec("BEGIN IMMEDIATE");
  try {
    const meta = letzteZeile(geprueft.gruppe);
    const version = naechsteVersion(geprueft.gruppe);
    database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'entwurf', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'entwurf')`).run(
      id,
      geprueft.gruppe,
      version,
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle || meta?.quelle || "",
      geprueft.beschreibung || meta?.beschreibung || geprueft.gruppe,
      geprueft.thema ?? meta?.thema ?? null,
      JSON.stringify(geprueft.stichworte ?? (meta ? stichworte(meta) : [])),
      geprueft.bedingung ?? meta?.bedingung ?? null,
      stamp,
      geprueft.wertCent,
      geprueft.wertExakt,
      geprueft.wertBps,
      blank(geprueft.anwendungsbereich),
      blank(geprueft.fundstelle),
      blank(geprueft.dokumentstand),
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return eintragOderFehler(id);
}

export function bearbeiteEntwurf(id: string, input: WertEingabe): RegisterEintrag {
  const geprueft = pruefeEntwurf(input);
  const database = getDb();
  database.exec("BEGIN IMMEDIATE");
  try {
    const row = database.prepare("SELECT * FROM zahlen_register WHERE id = ?").get(id) as SqlZeile | undefined;
    if (!row) throw new Error("Den Entwurf gibt es nicht.");
    if (row.freigabe !== "entwurf") throw new Error("Freigegebene Werte werden nicht überschrieben. Legen Sie eine neue Version an.");
    schreibeRevision(database, row, "entwurf_bearbeitet", "Entwurf geändert. Andere Zeilen und ihre Gültigkeit bleiben unverändert.");
    database.prepare(`UPDATE zahlen_register SET
        wert_exakt = ?, wert_cent = ?, wert_bps = ?, einheit = ?, gueltig_ab = ?, gueltig_bis = ?,
        quelle = ?, anwendungsbereich = ?, fundstelle = ?, dokumentstand = ?, beschreibung = ?, bedingung = ?
      WHERE id = ? AND freigabe = 'entwurf'`).run(
      geprueft.wertExakt,
      geprueft.wertCent,
      geprueft.wertBps,
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle || row.quelle,
      blank(geprueft.anwendungsbereich) ?? row.anwendungsbereich,
      blank(geprueft.fundstelle) ?? row.fundstelle,
      blank(geprueft.dokumentstand) ?? row.dokumentstand,
      geprueft.beschreibung || row.beschreibung,
      geprueft.bedingung ?? row.bedingung,
      id,
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return eintragOderFehler(id);
}

export function gebeFrei(input: WertEingabe & { abbruchNachSchreiben?: boolean }): RegisterEintrag {
  const geprueft = pruefeFreigabe(input);
  const database = getDb();
  const id = crypto.randomUUID();
  const stamp = new Date().toISOString();
  const nachweis = JSON.stringify({
    art: "vollstaendigkeit",
    hinweis: VOLLSTAENDIGKEIT,
    quelle: geprueft.quelle,
    fundstelle: geprueft.fundstelle,
    dokumentstand: geprueft.dokumentstand,
    anwendungsbereich: geprueft.anwendungsbereich,
    gueltigAb: geprueft.gueltigAb,
    gueltigBis: geprueft.gueltigBis,
    zeit: stamp,
  });
  database.exec("BEGIN IMMEDIATE");
  try {
    const vorhanden = findeGleicheFreigabe(geprueft);
    if (vorhanden) {
      database.exec("COMMIT");
      return vorhanden;
    }
    const approved = database.prepare(`SELECT * FROM zahlen_register
      WHERE gruppe = ? AND freigabe = 'freigegeben' AND anwendungsbereich = ?`).all(geprueft.gruppe, geprueft.anwendungsbereich) as SqlZeile[];
    const overlapping = approved.filter((row) => ueberlappt(row.gueltig_ab, row.gueltig_bis, geprueft.gueltigAb, geprueft.gueltigBis));
    const closable = overlapping.filter((row) => row.gueltig_bis == null && row.gueltig_ab < geprueft.gueltigAb);
    const blocked = overlapping.filter((row) => !closable.some((item) => item.id === row.id));
    if (blocked.length > 0 || closable.length > 1) {
      throw new Error(konfliktMeldung(geprueft.gruppe, geprueft.anwendungsbereich, geprueft.gueltigAb, geprueft.gueltigBis));
    }
    if (closable.length === 1) {
      const ende = tagDavor(geprueft.gueltigAb);
      if (ende < closable[0].gueltig_ab) throw new Error("Die Ablösung würde den bisherigen Zeitraum umkehren.");
      schreibeRevision(database, closable[0], "abloesung", "Gültig-bis wird zur Ablösung gesetzt. Der vorherige Zustand bleibt in der Revision.");
      database.prepare("UPDATE zahlen_register SET gueltig_bis = ? WHERE id = ? AND freigabe = 'freigegeben' AND gueltig_bis IS NULL").run(ende, closable[0].id);
    }
    if (input.abbruchNachSchreiben) throw new Error("Testabbruch vor dem Commit.");
    const meta = letzteZeile(geprueft.gruppe);
    database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'freigegeben', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'freigabe')`).run(
      id,
      geprueft.gruppe,
      naechsteVersion(geprueft.gruppe),
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle,
      geprueft.beschreibung || meta?.beschreibung || geprueft.gruppe,
      geprueft.thema ?? meta?.thema ?? null,
      JSON.stringify(geprueft.stichworte ?? (meta ? stichworte(meta) : [])),
      geprueft.bedingung ?? meta?.bedingung ?? null,
      stamp,
      geprueft.wertCent,
      geprueft.wertExakt,
      geprueft.wertBps,
      geprueft.anwendungsbereich,
      geprueft.fundstelle,
      geprueft.dokumentstand,
      nachweis,
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    if (istUnique(error)) {
      const nochmal = findeGleicheFreigabe(geprueft);
      if (nochmal) return nochmal;
    }
    throw error;
  }
  return eintragOderFehler(id);
}

export function wertAm(kennung: string, anwendungsbereich: string, datum: string): Auswahl {
  return wertFuerZeitraum({ kennung, anwendungsbereich, von: datum, bis: datum });
}

export function wertFuerZeitraum(input: { kennung: string; anwendungsbereich: string; von: string; bis: string }): Auswahl {
  if (!isoDatum(input.von) || !isoDatum(input.bis) || input.bis < input.von) {
    return { ok: false, grund: "fehlt", meldung: "Der Gültigkeitszeitraum ist kein gültiges Datum." };
  }
  const rows = getDb().prepare(`SELECT * FROM zahlen_register
    WHERE gruppe = ? AND freigabe = 'freigegeben' AND freigabe_nachweis IS NOT NULL AND freigabe_nachweis != ''
      AND anwendungsbereich = ? AND gueltig_ab <= ? AND (gueltig_bis IS NULL OR gueltig_bis >= ?)`).all(
    input.kennung,
    input.anwendungsbereich,
    input.von,
    input.bis,
  ) as SqlZeile[];
  if (rows.length === 0) return { ok: false, grund: "fehlt", meldung: fehltMeldung(input.kennung, input.anwendungsbereich, input.von, input.bis) };
  if (rows.length > 1) return { ok: false, grund: "mehrdeutig", meldung: konfliktMeldung(input.kennung, input.anwendungsbereich, input.von, input.bis) };
  return { ok: true, eintrag: mapEintrag(rows[0]) };
}

export function berechnungswert(input: { kennung: string; anwendungsbereich: string; von: string; bis: string }): Auswahl {
  if (!istBerechnungskennung(input.kennung)) {
    return {
      ok: false,
      grund: "unbekannt",
      meldung: `Die Kennung „${input.kennung}“ ist keine Berechnungsregel. Sie löst keine Berechnung aus.`,
    };
  }
  return wertFuerZeitraum(input);
}

export function revisionenZu(zeileId: string): Array<{ aktion: string; zustand: Record<string, unknown>; grund: string }> {
  const rows = getDb().prepare("SELECT aktion, zustand_json, grund FROM zahlen_revisionen WHERE zeile_id = ? ORDER BY created_at").all(zeileId) as Array<{ aktion: string; zustand_json: string; grund: string }>;
  return rows.map((row) => ({ aktion: row.aktion, zustand: JSON.parse(row.zustand_json) as Record<string, unknown>, grund: row.grund }));
}

function fehltMeldung(kennung: string, bereich: string, von: string, bis: string): string {
  const zeit = von === bis ? `am ${von}` : `im Zeitraum ${von} bis ${bis}`;
  return `Für „${kennung}“ (${bereich}) liegt ${zeit} kein freigegebener Wert vor. Die Berechnung ist blockiert. Es wird kein Wert aus einem anderen Jahr übernommen.`;
}

function konfliktMeldung(kennung: string, bereich: string, von: string, bis: string | null): string {
  const zeit = bis == null ? `ab ${von}` : von === bis ? `am ${von}` : `im Zeitraum ${von} bis ${bis}`;
  return `Für „${kennung}“ (${bereich}) liegen ${zeit} mehrere freigegebene Werte vor. Die Gültigkeitszeiträume überschneiden sich. Die Berechnung ist blockiert.`;
}

function pruefeEntwurf(input: WertEingabe): WertEingabe & { wertExakt: string; wertCent: number | null; wertBps: number | null; einheit: "euro" | "prozent" } {
  const gruppe = input.gruppe.trim();
  if (!KENNUNG.test(gruppe)) throw new Error("Die Kennung darf nur Kleinbuchstaben, Ziffern und Unterstriche enthalten.");
  if (input.einheit !== "euro" && input.einheit !== "prozent") throw new Error("Die Einheit muss Euro oder Prozent sein.");
  if (!isoDatum(input.gueltigAb)) throw new Error("Der Beginn ist kein Datum.");
  if (input.gueltigBis !== null && !isoDatum(input.gueltigBis)) throw new Error("Das Ende ist kein Datum.");
  if (input.gueltigBis && input.gueltigBis < input.gueltigAb) throw new Error("Das Ende liegt vor dem Anfang.");
  const wert = parseWert(input.einheit, input.betrag);
  const meta = letzteZeile(gruppe);
  if (!input.beschreibung?.trim() && !meta) throw new Error("Die Beschreibung fehlt.");
  return { ...input, gruppe, ...wert, einheit: input.einheit };
}

function pruefeFreigabe(input: WertEingabe): WertEingabe & { wertExakt: string; wertCent: number | null; wertBps: number | null; einheit: "euro" | "prozent"; quelle: string; fundstelle: string; dokumentstand: string; anwendungsbereich: string } {
  const basis = pruefeEntwurf(input);
  const quelle = input.quelle?.trim() ?? "";
  const fundstelle = input.fundstelle?.trim() ?? "";
  const dokumentstand = input.dokumentstand?.trim() ?? "";
  const anwendungsbereich = input.anwendungsbereich?.trim() ?? "";
  if (!quelle || !fundstelle || !dokumentstand || !anwendungsbereich) {
    throw new Error("Zur Freigabe fehlen Angaben. Nötig sind Quelle, Fundstelle, Dokumentstand, Gültigkeit und Anwendungsbereich. Das System prüft nur die Vollständigkeit, nicht die fachliche Richtigkeit.");
  }
  if (DATE.test(dokumentstand) && !isoDatum(dokumentstand)) throw new Error("Der Dokumentstand ist kein gültiges Datum.");
  return { ...basis, quelle, fundstelle, dokumentstand, anwendungsbereich };
}

function findeGleicheFreigabe(input: { gruppe: string; anwendungsbereich: string; gueltigAb: string; gueltigBis: string | null; wertExakt: string }): RegisterEintrag | null {
  const row = getDb().prepare(`SELECT * FROM zahlen_register
    WHERE gruppe = ? AND freigabe = 'freigegeben' AND anwendungsbereich = ? AND gueltig_ab = ? AND wert_exakt = ?
      AND ((gueltig_bis IS NULL AND ? IS NULL) OR gueltig_bis = ?)`).get(
    input.gruppe,
    input.anwendungsbereich,
    input.gueltigAb,
    input.wertExakt,
    input.gueltigBis,
    input.gueltigBis,
  ) as SqlZeile | undefined;
  return row ? mapEintrag(row) : null;
}

function letzteZeile(gruppe: string): SqlZeile | null {
  return (getDb().prepare("SELECT * FROM zahlen_register WHERE gruppe = ? ORDER BY version DESC LIMIT 1").get(gruppe) as SqlZeile | undefined) ?? null;
}

function naechsteVersion(gruppe: string): number {
  const row = getDb().prepare("SELECT MAX(version) AS version FROM zahlen_register WHERE gruppe = ?").get(gruppe) as { version: number | null };
  return (row.version ?? 0) + 1;
}

function eintragOderFehler(id: string): RegisterEintrag {
  const row = getDb().prepare("SELECT * FROM zahlen_register WHERE id = ?").get(id) as SqlZeile | undefined;
  if (!row) throw new Error("Der Eintrag wurde nicht gespeichert.");
  return mapEintrag(row);
}

function schreibeRevision(database: ReturnType<typeof getDb>, row: SqlZeile, aktion: string, grund: string): void {
  database.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
    VALUES (?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), row.id, aktion, JSON.stringify(row), grund, new Date().toISOString());
}

function mapEintrag(row: SqlZeile): RegisterEintrag {
  let stichworte: string[] = [];
  if (row.stichworte_json) {
    const parsed = JSON.parse(row.stichworte_json) as unknown;
    if (Array.isArray(parsed)) stichworte = parsed.filter((item): item is string => typeof item === "string");
  }
  const einheit: Einheit = row.einheit === "prozent" || row.einheit === "hinweis" ? row.einheit : "euro";
  return {
    id: row.id,
    gruppe: row.gruppe,
    version: row.version,
    wertExakt: row.wert_exakt,
    wertCent: row.wert_cent,
    wertBps: row.wert_bps,
    einheit,
    gueltigAb: row.gueltig_ab,
    gueltigBis: row.gueltig_bis,
    quelle: row.quelle,
    fundstelle: row.fundstelle,
    dokumentstand: row.dokumentstand,
    anwendungsbereich: row.anwendungsbereich,
    freigabe: row.freigabe === "freigegeben" ? "freigegeben" : "entwurf",
    freigabeNachweis: row.freigabe_nachweis,
    herkunft: row.herkunft,
    beschreibung: row.beschreibung,
    thema: row.thema,
    stichworte,
    bedingung: row.bedingung,
    createdAt: row.created_at,
  };
}

function stichworte(row: SqlZeile): string[] {
  return mapEintrag(row).stichworte;
}

function gleicheVorlage(row: SqlZeile, zeile: VorlageZeile): boolean {
  if (row.gruppe !== zeile.gruppe || row.gueltig_ab !== zeile.gueltigAb) return false;
  if (zeile.einheit === "hinweis") return row.einheit === "hinweis";
  if (row.wert_exakt && zeile.wertExakt && row.wert_exakt === zeile.wertExakt) return true;
  if (row.einheit !== zeile.einheit) return false;
  if (zeile.wertCent != null && row.wert_cent != null) return row.wert_cent === zeile.wertCent;
  if (zeile.wertBps != null && row.wert_bps != null) return row.wert_bps === zeile.wertBps;
  if (row.betrag == null) return false;
  const ziel = zeile.einheit === "euro" ? zeile.wertCent : zeile.wertBps;
  return ziel != null && Math.round(Number(row.betrag) * 100) === ziel;
}

function liesVorlageZeilen(file: string): VorlageZeile[] {
  let raw: string;
  try {
    raw = readFileSync(file, "utf8");
  } catch {
    throw new Error("Die Werteliste daten/zahlen-werte.json fehlt.");
  }
  const betraege: string[] = [];
  const tagged = raw.replace(/"betrag"\s*:\s*(-?\d+(?:\.\d+)?)/g, (_match, num: string) => {
    const token = `__BETRAG_${betraege.length}__`;
    betraege.push(num);
    return `"betrag":"${token}"`;
  });
  const parsed = JSON.parse(tagged) as {
    liste_stand?: string;
    wertegruppen?: Array<{
      name?: string;
      beschreibung?: string;
      quelle?: string;
      einheit?: string;
      thema?: string;
      stichworte?: string[];
      bedingung?: string;
      werte?: Array<{ betrag?: string; gueltig_ab?: string; gueltig_bis?: string | null }>;
    }>;
  };
  if (!Array.isArray(parsed.wertegruppen)) throw new Error("Die Werteliste daten/zahlen-werte.json ist ungültig.");
  const zeilen: VorlageZeile[] = [];
  for (const gruppe of parsed.wertegruppen) {
    if (!gruppe.name || !KENNUNG.test(gruppe.name)) throw new Error("Eine Kennung in der Vorlage ist ungültig.");
    const einheit: "euro" | "prozent" = gruppe.einheit === "prozent" || gruppe.name === "abgabesatz" ? "prozent" : "euro";
    const werte = gruppe.werte ?? [];
    if (werte.length === 0) {
      zeilen.push({
        gruppe: gruppe.name,
        beschreibung: gruppe.beschreibung ?? gruppe.name,
        quelle: gruppe.quelle ?? "",
        thema: gruppe.thema ?? null,
        stichworte: gruppe.stichworte ?? [],
        bedingung: gruppe.bedingung ?? null,
        einheit: "hinweis",
        wertExakt: null,
        wertCent: null,
        wertBps: null,
        gueltigAb: parsed.liste_stand && isoDatum(parsed.liste_stand) ? parsed.liste_stand : "2026-01-01",
        gueltigBis: null,
      });
      continue;
    }
    for (const wert of werte) {
      const token = wert.betrag ?? "";
      const exact = token.startsWith("__BETRAG_") ? betraege[Number(token.slice(9, -2))] : token;
      const parsedWert = parseWert(einheit, exact);
      if (!wert.gueltig_ab || !isoDatum(wert.gueltig_ab)) throw new Error(`Der Beginn in ${gruppe.name} ist kein Datum.`);
      if (wert.gueltig_bis != null && !isoDatum(wert.gueltig_bis)) throw new Error(`Das Ende in ${gruppe.name} ist kein Datum.`);
      zeilen.push({
        gruppe: gruppe.name,
        beschreibung: gruppe.beschreibung ?? gruppe.name,
        quelle: gruppe.quelle ?? "",
        thema: gruppe.thema ?? null,
        stichworte: gruppe.stichworte ?? [],
        bedingung: gruppe.bedingung ?? null,
        einheit,
        wertExakt: parsedWert.wertExakt,
        wertCent: parsedWert.wertCent,
        wertBps: parsedWert.wertBps,
        gueltigAb: wert.gueltig_ab,
        gueltigBis: wert.gueltig_bis ?? null,
      });
    }
  }
  return zeilen;
}

function ueberlappt(aAb: string, aBis: string | null, bAb: string, bBis: string | null): boolean {
  return aAb <= (bBis ?? OFFEN) && bAb <= (aBis ?? OFFEN);
}

function isoDatum(value: string): boolean {
  if (!DATE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function tagDavor(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}

function blank(value: string | undefined): string | null {
  const text = value?.trim() ?? "";
  return text.length > 0 ? text : null;
}

function istUnique(error: unknown): boolean {
  return error instanceof Error && /UNIQUE/i.test(error.message);
}
