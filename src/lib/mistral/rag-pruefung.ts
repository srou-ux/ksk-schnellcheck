export type ZahlenPruefung = {
  status: "bestanden" | "warnung" | "uebersprungen";
  checked: number;
  lines: string[];
};

export type LibraryPruefung = {
  ok: boolean;
  documents: string[];
  line: string;
};

export type RagPruefung = {
  zahlen: ZahlenPruefung;
  library: LibraryPruefung;
  interne: string | null;
};

const SKIP_LINE = "Citations nicht verfügbar — Zahl-Check übersprungen";
const LIBRARY_WARN = "Antwort ohne Library-Bezug — Ergebnis ungültig (Testmodus)";

export function parseZahl(raw: string): number | null {
  let value = raw.replace(/€/g, "").replace(/%/g, "").replace(/\beuro?\b/gi, "").replace(/\s/g, "");
  if (!value) return null;
  const lastComma = value.lastIndexOf(",");
  const lastDot = value.lastIndexOf(".");
  if (lastComma >= 0 && lastDot >= 0) {
    value = lastComma > lastDot ? value.replace(/\./g, "").replace(",", ".") : value.replace(/,/g, "");
  } else if (lastComma >= 0) {
    const fraction = value.slice(lastComma + 1);
    value = fraction.length <= 2 ? value.replace(",", ".") : value.replace(/,/g, "");
  } else if (lastDot >= 0 && /^\d{1,3}(?:\.\d{3})+$/.test(value)) {
    value = value.replace(/\./g, "");
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function gleicheZahl(links: number, rechts: number): boolean {
  return Math.abs(links - rechts) < 0.001;
}

const GELD_ZAHL = String.raw`\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+[.,]\d{1,2}|\d+`;
const GELD_MIT_WAEHRUNG = new RegExp(String.raw`(?:€|\beur(?:o)?\b)\s*(?:${GELD_ZAHL})|(?:${GELD_ZAHL})\s*(?:€|\beur(?:o)?\b)`, "gi");
const GELD_DEZIMAL = /(?<![\d.])\d+[.,]\d{1,2}(?!\s*(?:%|prozent)\b)(?![.\d])/gi;

export type GeldTreffer = { value: number; index: number; length: number };

function ueberschneidet(bereiche: Array<[number, number]>, start: number, ende: number): boolean {
  return bereiche.some(([links, rechts]) => start < rechts && ende > links);
}

export function geldTreffer(text: string): GeldTreffer[] {
  const gefunden: GeldTreffer[] = [];
  const belegt: Array<[number, number]> = [];
  for (const muster of [GELD_MIT_WAEHRUNG, GELD_DEZIMAL]) {
    for (const match of text.matchAll(muster)) {
      if (match.index == null) continue;
      const start = match.index;
      const ende = start + match[0].length;
      if (ueberschneidet(belegt, start, ende)) continue;
      if (/§\s*$/.test(text.slice(Math.max(0, start - 4), start))) continue;
      const value = parseZahl(match[0]);
      if (value == null) continue;
      belegt.push([start, ende]);
      gefunden.push({ value, index: start, length: match[0].length });
    }
  }
  return gefunden;
}

export function geldVorhanden(text: string, value: number): boolean {
  return geldTreffer(text).some((item) => gleicheZahl(item.value, value));
}

export function zahlVorhanden(text: string, value: number): boolean {
  return geldVorhanden(text, value);
}

function textstellen(ranges: Array<[number, number]>, text: string): string[] {
  const geordnet = [...ranges].sort((links, rechts) => links[0] - rechts[0]);
  const vereint: Array<[number, number]> = [];
  for (const bereich of geordnet) {
    const letzter = vereint[vereint.length - 1];
    if (letzter && bereich[0] <= letzter[1]) letzter[1] = Math.max(letzter[1], bereich[1]);
    else vereint.push([bereich[0], bereich[1]]);
  }
  return vereint
    .slice(0, 8)
    .map(([anfang, ende]) => text.slice(anfang, ende).replace(/\s+/g, " ").trim())
    .filter(Boolean);
}

export function textstellenUmBetraege(text: string, betraege: number[], radius = 160): string[] {
  if (!text.trim() || betraege.length === 0) return [];
  const bereiche = geldTreffer(text)
    .filter((treffer) => betraege.some((betrag) => gleicheZahl(betrag, treffer.value)))
    .map((treffer) => [Math.max(0, treffer.index - radius), Math.min(text.length, treffer.index + treffer.length + radius)] as [number, number]);
  return textstellen(bereiche, text);
}

export const SCHLUESSELBEGRIFFE = ["verpflegungsmehraufwand", "ehrenamtspauschale", "fahrtkosten", "grenze"];

export function zahlenAusFrage(frage: string): { betraege: number[]; prozente: number[] } {
  const betraege = new Set<string>();
  for (const item of euroAmounts(frage)) betraege.add(item.value.toFixed(2));
  const muster = /\b\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\b\d+[.,]\d{1,2}|\b\d{2,5}\b/g;
  for (const match of frage.matchAll(muster)) {
    if (match.index == null || /^(?:19|20)\d{2}$/.test(match[0])) continue;
    const danach = frage.slice(match.index + match[0].length, match.index + match[0].length + 8);
    if (/^\s*(?:%|prozent)/i.test(danach)) continue;
    const value = parseZahl(match[0]);
    if (value == null || value <= 0) continue;
    betraege.add(value.toFixed(2));
  }
  return {
    betraege: [...betraege].map(Number),
    prozente: prozentWerte(frage).map((item) => item.value),
  };
}

export function textstellenUmBegriffe(text: string, begriffe: string[], radius = 220): string[] {
  if (!text.trim() || begriffe.length === 0) return [];
  const hay = text.toLowerCase();
  const bereiche: Array<[number, number]> = [];
  for (const begriff of begriffe) {
    const needle = begriff.trim().toLowerCase();
    if (needle.length < 4) continue;
    let from = 0;
    let count = 0;
    while (count < 3) {
      const index = hay.indexOf(needle, from);
      if (index < 0) break;
      bereiche.push([Math.max(0, index - radius), Math.min(text.length, index + needle.length + radius)]);
      from = index + needle.length;
      count += 1;
    }
  }
  return textstellen(bereiche, text);
}

export function textstellenUmProzente(text: string, werte: number[], radius = 160): string[] {
  if (!text.trim() || werte.length === 0) return [];
  const bereiche = prozentWerte(text)
    .filter((treffer) => werte.some((wert) => gleicheZahl(wert, treffer.value)))
    .map((treffer) => [Math.max(0, treffer.index - radius), Math.min(text.length, treffer.index + treffer.length + radius)] as [number, number]);
  return textstellen(bereiche, text);
}

export function istInterneQuelle(name: string): boolean {
  return /prompt-v12(?:\.md)?/i.test(name);
}

export const INTERNE_FUNDSTELLE = "🔴 Ungültige Fundstelle: interne Datei";

export function prozentWerte(text: string): Array<{ label: string; value: number; index: number; length: number }> {
  const pattern = /\d+(?:[.,]\d+)?\s*%/g;
  const found: Array<{ label: string; value: number; index: number; length: number }> = [];
  for (const match of text.matchAll(pattern)) {
    const label = match[0].replace(/\s+/g, " ").trim();
    const value = parseZahl(label);
    if (value == null || !Number.isFinite(value) || match.index == null) continue;
    found.push({ label, value, index: match.index, length: match[0].length });
  }
  return found;
}

export function euroTreffer(text: string): Array<{ label: string; value: number; index: number; length: number }> {
  const pattern = /€\s*\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|€\s*\d+(?:[.,]\d+)?|\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?\s*€|\d+[.,]\d{1,2}\s*€|\d+(?:,\d{1,2})?\s*€/g;
  const found: Array<{ label: string; value: number; index: number; length: number }> = [];
  for (const match of text.matchAll(pattern)) {
    const label = match[0].replace(/\s+/g, " ").trim();
    const value = parseZahl(label);
    if (value == null || match.index == null) continue;
    found.push({ label, value, index: match.index, length: match[0].length });
  }
  return found;
}

export function euroAmounts(text: string): Array<{ label: string; value: number; index: number }> {
  const found: Array<{ label: string; value: number; index: number }> = [];
  const seen = new Set<string>();
  for (const item of euroTreffer(text)) {
    const key = item.value.toFixed(2);
    if (seen.has(key)) continue;
    seen.add(key);
    found.push(item);
  }
  return found;
}

function corpusValues(corpus: string): Set<string> {
  return new Set(geldTreffer(corpus).map((item) => item.value.toFixed(2)));
}

export function matchedDocuments(answer: string, documentNames: string[]): string[] {
  const found: string[] = [];
  for (const name of documentNames) {
    if (istInterneQuelle(name)) continue;
    if (answer.toLowerCase().includes(name.toLowerCase())) {
      found.push(name);
      continue;
    }
    const info = name.match(/info[_ -]?(\d+)/i);
    if (info && new RegExp(`info\\s*[_-]?\\s*${info[1]}\\b`, "i").test(answer)) {
      found.push(name);
      continue;
    }
    const stem = name.replace(/\.[a-z0-9]+$/i, "").toLowerCase().replace(/[_-]+/g, " ");
    const hay = answer.toLowerCase().replace(/[_-]+/g, " ");
    if (stem.length >= 4 && hay.includes(stem)) found.push(name);
  }
  return [...new Set(found)].sort();
}

export function pruefeAntwort(input: {
  answer: string;
  zahlText?: string;
  documentNames: string[];
  citationsField: boolean;
  passages: string[];
  citationLabels: string[];
}): RagPruefung {
  const material = input.passages.map((item) => item.trim()).filter(Boolean);
  const canCheckNumbers = input.citationsField || material.length > 0;
  let zahlen: ZahlenPruefung;
  if (!canCheckNumbers) {
    zahlen = { status: "uebersprungen", checked: 0, lines: [SKIP_LINE] };
  } else {
    const amounts = euroAmounts(input.zahlText ?? input.answer);
    const known = corpusValues(material.join("\n"));
    const warnings = amounts
      .filter((amount) => !known.has(amount.value.toFixed(2)))
      .map((amount) => `⚠️ Zahl ohne Fundstelle: ${amount.label}`);
    zahlen = warnings.length > 0
      ? { status: "warnung", checked: amounts.length, lines: warnings }
      : { status: "bestanden", checked: amounts.length, lines: [] };
  }

  const documents = matchedDocuments([input.answer, ...input.citationLabels].join("\n"), input.documentNames);
  const library: LibraryPruefung = documents.length > 0
    ? { ok: true, documents, line: `Library-Bezug: ${documents.join(", ")}` }
    : { ok: false, documents: [], line: LIBRARY_WARN };
  const interne = istInterneQuelle([input.answer, ...input.citationLabels].join("\n")) ? INTERNE_FUNDSTELLE : null;

  return { zahlen, library, interne };
}
