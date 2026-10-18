import requirements from "../../config/ksk-quellenanforderungen-v1.json";
import { getDb } from "@/lib/db";
import { absoluteUrl, leseLinkliste, type KatalogEintrag } from "@/lib/quellenkatalog-lese";

type KatalogDb = {
  id: string;
  katalog_key: string;
  art: KatalogEintrag["art"];
  titel: string;
  url: string;
  dokumentnummer: string | null;
  herausgeber: string;
  listenherkunft: string;
  archiv_quelle_id: string | null;
};

export type KatalogZeile = KatalogEintrag & {
  id: string;
  archiv_quelle_id: string | null;
};

function zeile(row: KatalogDb): KatalogZeile {
  return {
    id: row.id,
    katalogKey: row.katalog_key,
    art: row.art,
    titel: row.titel,
    url: row.url,
    dokumentnummer: row.dokumentnummer,
    herausgeber: row.herausgeber,
    listenherkunft: row.listenherkunft,
    archiv_quelle_id: row.archiv_quelle_id,
  };
}

const now = () => new Date().toISOString();

export function festeEinstiege(): KatalogEintrag[] {
  return [
    {
      katalogKey: "gesetz:ksvg",
      art: "gesetz",
      titel: "Künstlersozialversicherungsgesetz (KSVG)",
      url: requirements.einstiege.ksvg,
      dokumentnummer: null,
      herausgeber: "Bundesministerium der Justiz",
      listenherkunft: "fest",
    },
    {
      katalogKey: "verordnung:ksventgv",
      art: "verordnung",
      titel: "Künstlersozialversicherungs-Entgeltverordnung (KSVEntgV)",
      url: requirements.einstiege.ksventgv,
      dokumentnummer: null,
      herausgeber: "Bundesministerium der Justiz",
      listenherkunft: "fest",
    },
  ];
}

export function ergaenzeGesetzestexte(html: string, baseUrl: string, stamm: KatalogEintrag): KatalogEintrag[] {
  return leseLinkliste(html, baseUrl, stamm.herausgeber)
    .filter((item) => {
      const host = new URL(item.url).hostname;
      const basis = new URL(baseUrl).hostname;
      return host === basis;
    })
    .map((item) => ({
      ...item,
      katalogKey: `url:${item.url}`,
      art: stamm.art,
      dokumentnummer: null,
      listenherkunft: stamm.listenherkunft,
    }));
}

export function merkeKatalog(eintraege: KatalogEintrag[]): number {
  const stamp = now();
  const write = getDb().prepare(`INSERT INTO quellenkatalog (
      id, katalog_key, art, titel, url, dokumentnummer, herausgeber, listenherkunft, archiv_quelle_id, erfasst_am, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
    ON CONFLICT(katalog_key) DO UPDATE SET
      art = excluded.art, titel = excluded.titel, url = excluded.url, dokumentnummer = excluded.dokumentnummer,
      herausgeber = excluded.herausgeber, listenherkunft = excluded.listenherkunft, updated_at = excluded.updated_at`);
  let count = 0;
  for (const item of eintraege) {
    write.run(crypto.randomUUID(), item.katalogKey, item.art, item.titel, item.url, item.dokumentnummer, item.herausgeber, item.listenherkunft, stamp, stamp);
    count += 1;
  }
  return count;
}

export function katalogNachKey(key: string): KatalogZeile | null {
  const row = getDb().prepare("SELECT * FROM quellenkatalog WHERE katalog_key = ?").get(key) as KatalogDb | undefined;
  return row ? zeile(row) : null;
}

export function katalogAnzahl(): number {
  return Number((getDb().prepare("SELECT COUNT(*) AS n FROM quellenkatalog").get() as { n: number }).n);
}

export function setzeKatalogArchiv(katalogKey: string, archivQuelleId: string): void {
  getDb().prepare("UPDATE quellenkatalog SET archiv_quelle_id = ?, updated_at = ? WHERE katalog_key = ? AND (archiv_quelle_id IS NULL OR archiv_quelle_id = ?)")
    .run(archivQuelleId, now(), katalogKey, archivQuelleId);
}

export function ausgangsquellen(): KatalogZeile[] {
  const wanted = new Set(requirements.ausgangsquellen.map((item) => `informationsschrift:${item}`));
  wanted.add("gesetz:ksvg");
  wanted.add("verordnung:ksventgv");
  const rows = (getDb().prepare("SELECT * FROM quellenkatalog").all() as KatalogDb[]).map(zeile);
  return rows.filter((row) => wanted.has(row.katalogKey)
    || (row.art === "verordnung" && /abgabe/i.test(row.titel) && row.katalogKey !== "verordnung:ksventgv")
    || (row.listenherkunft === "fest" && row.url.toLowerCase().endsWith(".pdf")));
}

export function pdfNebenDemEinstieg(basis: string): string[] {
  const base = absoluteUrl(basis, basis);
  if (!base) return [];
  const host = new URL(base).hostname;
  return (getDb().prepare("SELECT url FROM quellenkatalog WHERE listenherkunft = 'fest' AND url LIKE '%.pdf'").all() as Array<{ url: string }>)
    .map((row) => row.url)
    .filter((url) => {
      try { return new URL(url).hostname === host; } catch { return false; }
    });
}
