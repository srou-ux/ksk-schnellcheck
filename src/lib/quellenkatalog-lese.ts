export type KatalogArt = "informationsschrift" | "formular" | "sprachfassung" | "gesetz" | "verordnung" | "sonstig";
export type StandGenauigkeit = "tag" | "monat" | "jahr" | "unbekannt";
export type AnwendungStatus = "belegt" | "ungeklaert" | "widerspruch";

export type KatalogEintrag = {
  katalogKey: string;
  art: KatalogArt;
  titel: string;
  url: string;
  dokumentnummer: string | null;
  herausgeber: string;
  listenherkunft: string;
};

export type StandLesung = { text: string | null; iso: string | null; genauigkeit: StandGenauigkeit };

const ENTITY: Record<string, string> = { nbsp: " ", amp: "&", quot: "\"", apos: "'", lt: "<", gt: ">" };

export function htmlText(value: string): string {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&([a-z]+);/gi, (all, name: string) => ENTITY[name.toLowerCase()] ?? all)
    .replace(/&#(\d+);/g, (_, code: string) => String.fromCharCode(Number(code)))
    .replace(/\s+/g, " ")
    .trim();
}

export function absoluteUrl(raw: string, base: string): string | null {
  try {
    const url = new URL(raw, base);
    url.hash = "";
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    url.protocol = "https:";
    return url.toString();
  } catch {
    return null;
  }
}

function dokumentnummer(titel: string, href: string): string | null {
  const fromTitle = titel.match(/Informationsschrift\s+Nr\.?\s*0*(\d+[a-z]?)/i)?.[1]
    ?? titel.match(/\bInfo(?:rmationsschrift)?\s+No\.?\s*0*(\d+[a-z]?)/i)?.[1]
    ?? titel.match(/\bInfo(?:rmationsschrift)?\s+Nr\.?\s*0*(\d+[a-z]?)/i)?.[1];
  if (fromTitle) return fromTitle.toLowerCase();
  const fromFile = decodeURIComponent(href).match(/Info_0*(\d+[a-z]?)_/i)?.[1];
  return fromFile ? fromFile.toLowerCase() : null;
}

function artVon(titel: string, href: string, nummer: string | null): KatalogArt {
  const probe = `${titel} ${decodeURIComponent(href)}`.toLowerCase();
  if (/\(en[, ]|englische version|\binfo no\b/.test(probe)) return "sprachfassung";
  if (nummer && /informationsschriften\/info_/i.test(href) && !/englische/i.test(probe)) return "informationsschrift";
  if (/vordrucke_und_formulare|anmeldeunterlagen|meldebogen|änderungsmitteilung|aenderungsmitteilung|vordruck|fragebogen/.test(probe)) return "formular";
  if (nummer) return "informationsschrift";
  if (/verordnung/.test(probe)) return "verordnung";
  if (/gesetz/.test(probe)) return "gesetz";
  return "sonstig";
}

export function leseLinkliste(html: string, baseUrl: string, herkunft: string): KatalogEintrag[] {
  const seen = new Set<string>();
  const entries: KatalogEintrag[] = [];
  const pattern = /<a\b[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(html))) {
    const href = match[1];
    if (!/\.pdf(?:$|\?)/i.test(href)) continue;
    const url = absoluteUrl(href, baseUrl);
    if (!url) continue;
    const titel = htmlText(match[2]).replace(/\s*\(PDF[\s\S]*$/i, "").trim();
    if (!titel) continue;
    const nummer = dokumentnummer(titel, href);
    const art = artVon(titel, href, nummer);
    const key = nummer && art !== "formular" ? `${art}:${nummer}` : `url:${url}`;
    if (seen.has(key)) continue;
    seen.add(key);
    entries.push({
      katalogKey: key,
      art,
      titel,
      url,
      dokumentnummer: nummer,
      herausgeber: herkunft,
      listenherkunft: herkunft,
    });
  }
  return entries;
}

export function mediencenterLayout(html: string, eintraege: KatalogEintrag[]): { erkannt: boolean; fehler: string | null } {
  const infos = eintraege.filter((item) => item.art === "informationsschrift");
  const erkannt = infos.length >= 3 && /informationsschrift/i.test(html);
  if (erkannt) return { erkannt: true, fehler: null };
  return {
    erkannt: false,
    fehler: "Der Seitenaufbau des KSK-Mediencenters wurde nicht erkannt. Vorhandene Katalogeinträge bleiben unverändert.",
  };
}

export function leseDokumentstand(value: string | null | undefined): StandLesung {
  const text = value?.trim() || "";
  const month = text.match(/(?:^|stand:?\s*)(0[1-9]|1[0-2])\.(\d{4})$/i) ?? text.match(/^(0[1-9]|1[0-2])\.(\d{4})$/);
  if (month) return { text, iso: `${month[2]}-${month[1]}`, genauigkeit: "monat" };
  const iso = text.match(/^(\d{4})-(0[1-9]|1[0-2])(?:-([0-3]\d))?$/);
  if (iso?.[3]) return { text, iso: text, genauigkeit: "tag" };
  if (iso) return { text, iso: `${iso[1]}-${iso[2]}`, genauigkeit: "monat" };
  const year = text.match(/^(\d{4})$/);
  if (year) return { text, iso: year[1], genauigkeit: "jahr" };
  const embedded = text.match(/Stand:\s*(0[1-9]|1[0-2])\.(\d{4})/i);
  if (embedded) return { text: `${embedded[1]}.${embedded[2]}`, iso: `${embedded[2]}-${embedded[1]}`, genauigkeit: "monat" };
  return { text: text || null, iso: null, genauigkeit: "unbekannt" };
}

export function standAusText(text: string): StandLesung {
  const match = text.match(/Stand:\s*(0[1-9]|1[0-2])\.(\d{4})/i);
  if (!match) return { text: null, iso: null, genauigkeit: "unbekannt" };
  return leseDokumentstand(`${match[1]}.${match[2]}`);
}

export function anwendungFuerJahr(input: {
  jahr: number;
  genauigkeit: StandGenauigkeit;
  iso: string | null;
  gueltigAb: string | null;
  gueltigBis: string | null;
  modell: AnwendungStatus;
  offenePunkte?: string[];
}): AnwendungStatus {
  if (input.modell === "widerspruch") return "widerspruch";
  if (input.modell !== "belegt") return "ungeklaert";
  if (input.offenePunkte?.some((item) => item.trim().length > 0)) return "ungeklaert";
  const von = input.gueltigAb?.slice(0, 10) ?? null;
  const bis = input.gueltigBis?.slice(0, 10) ?? null;
  const anfang = `${input.jahr}-01-01`;
  const ende = `${input.jahr}-12-31`;
  if (von && von > anfang) return "ungeklaert";
  if (bis && bis < ende) return "ungeklaert";
  const standJahr = input.iso ? Number(input.iso.slice(0, 4)) : null;
  if (standJahr !== null && standJahr > input.jahr) return "ungeklaert";
  if (input.genauigkeit === "unbekannt" && !von) return "ungeklaert";
  if (!von && input.iso && input.genauigkeit !== "unbekannt" && standJahr !== null && standJahr < input.jahr && input.genauigkeit !== "jahr") {
    return "ungeklaert";
  }
  return "belegt";
}

export function vorbereitungslage(input: {
  status: string;
  schritt: string;
  quellen: Array<{ status: string; anwendung_status?: string | null; luecken_typ?: string | null }>;
  nachrecherchen: Array<{ status: string }>;
  luecken: string[];
}): { automatisch: boolean; nachrecherche: boolean; pruefung: boolean; hinweis: string } {
  const nachrecherche = input.status === "running" && /nachrecherche/i.test(input.schritt)
    || input.nachrecherchen.some((item) => item.status === "laeuft" || item.status === "offen");
  const pruefung = input.quellen.some((item) => item.status === "fehler" || item.anwendung_status === "ungeklaert" || item.anwendung_status === "widerspruch" || Boolean(item.luecken_typ))
    || input.nachrecherchen.some((item) => item.status === "offen_manuell" || item.status === "kostenlimit")
    || input.luecken.length > 0;
  const automatisch = input.quellen.some((item) => item.status === "archiviert");
  const hinweis = automatisch
    ? "Automatisch vorbereitet bedeutet, dass ein Entwurf archiviert wurde. Das ist keine fachliche Bestätigung und keine Freigabe."
    : "Es liegt noch kein archivierter Entwurf vor.";
  return { automatisch, nachrecherche, pruefung, hinweis };
}
