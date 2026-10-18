import { euroAmounts, euroTreffer, gleicheZahl, matchedDocuments, parseZahl, prozentWerte, zahlVorhanden } from "@/lib/mistral/rag-pruefung";
import { stehtInListe, type Grenze, type ZahlenListe } from "@/lib/mistral/zahlen-werte";

export type AntwortAbschnitte = {
  kernaussagen: string;
  zahlen: string;
  nutzerangaben: string;
  fundstellen: string;
  luecken: string;
  vollstaendig: boolean;
};

const HEADING = /(?:^|\n)[ \t]*#{0,3}[ \t]*(?:\*\*|__)?[ \t]*(KERNAUSSAGEN|ZAHLEN|NUTZERANGABEN-PR(?:Ü|UE)FUNG|FUNDSTELLEN|L(?:Ü|UE)CKEN)[ \t]*(?:\*\*|__)?[ \t]*:/gi;

function keyOf(heading: string): keyof Omit<AntwortAbschnitte, "vollstaendig"> | null {
  const name = heading.toUpperCase().replace("UE", "Ü");
  if (name === "KERNAUSSAGEN") return "kernaussagen";
  if (name === "ZAHLEN") return "zahlen";
  if (name.startsWith("NUTZERANGABEN")) return "nutzerangaben";
  if (name === "FUNDSTELLEN") return "fundstellen";
  if (name === "LÜCKEN" || name === "LUECKEN") return "luecken";
  return null;
}

export function parseAbschnitte(answer: string): AntwortAbschnitte {
  const sections: AntwortAbschnitte = {
    kernaussagen: "",
    zahlen: "",
    nutzerangaben: "",
    fundstellen: "",
    luecken: "",
    vollstaendig: false,
  };
  const marks: Array<{ key: keyof Omit<AntwortAbschnitte, "vollstaendig">; start: number; end: number }> = [];
  for (const match of answer.matchAll(HEADING)) {
    const key = keyOf(match[1] ?? "");
    if (!key || match.index == null) continue;
    marks.push({ key, start: match.index, end: match.index + match[0].length });
  }
  for (let index = 0; index < marks.length; index += 1) {
    const mark = marks[index];
    const next = marks[index + 1]?.start ?? answer.length;
    sections[mark.key] = answer.slice(mark.end, next).trim();
  }
  sections.vollstaendig = Boolean(sections.kernaussagen || marks.some((mark) => mark.key === "kernaussagen"))
    && marks.some((mark) => mark.key === "zahlen")
    && marks.some((mark) => mark.key === "nutzerangaben")
    && marks.some((mark) => mark.key === "fundstellen")
    && marks.some((mark) => mark.key === "luecken");
  return sections;
}

function jahrDavor(line: string, index: number): number | null {
  const before = line.slice(Math.max(0, index - 24), index);
  const match = before.match(/(?:für|in|ab|seit)\s+((?:19|20)\d{2})\s*:\s*$/i);
  return match ? Number(match[1]) : null;
}

function jahrDanach(line: string, end: number): number | null {
  const after = line.slice(end, end + 36);
  const match = after.match(/^\s*(?:€)?\s*(?:für|im Jahr)\s+((?:19|20)\d{2})\b/i);
  if (!match) return null;
  const rest = after.slice(match[0].length);
  if (/^\s*:/.test(rest)) return null;
  return Number(match[1]);
}

export function grenzenAusText(text: string): Grenze[] {
  const grenzen: Grenze[] = [];
  for (const line of text.split(/\n/)) {
    const euros = euroTreffer(line).map((item) => ({ ...item, unit: "euro" as const }));
    const prozente = prozentWerte(line).map((item) => ({ ...item, unit: "prozent" as const }));
    for (const item of [...euros, ...prozente].sort((a, b) => a.index - b.index)) {
      const jahr = jahrDavor(line, item.index) ?? jahrDanach(line, item.index + item.length);
      grenzen.push({ value: item.value, unit: item.unit, jahr, label: item.label });
    }
  }
  return grenzen;
}

const NAECHSTE_UEBERSCHRIFT = String.raw`\n[ \t]*#{0,3}[ \t]*(?:\*\*|__)?[ \t]*(?:NUTZERANGABEN-PR(?:Ü|UE)FUNG|FUNDSTELLEN|L(?:Ü|UE)CKEN|KERNAUSSAGEN)[ \t]*(?:\*\*|__)?[ \t]*:`;

export function fehlendeBetragszeilen(answer: string, zeilen: string[], relevante: number[]): string[] {
  const sections = parseAbschnitte(answer);
  const vorhanden = euroAmounts(sections.zahlen || (sections.vollstaendig ? "" : answer));
  return zeilen.filter((zeile) => {
    const betrag = euroAmounts(zeile)[0];
    if (!betrag) return false;
    if (!relevante.some((wert) => gleicheZahl(wert, betrag.value))) return false;
    return !vorhanden.some((item) => gleicheZahl(item.value, betrag.value));
  });
}

export function zahlenAusNachfrage(text: string, erlaubt: string[]): string | null {
  const werte = erlaubt.flatMap((zeile) => euroAmounts(zeile).map((item) => item.value));
  const behalten = text.split(/\n/).map((zeile) => zeile.trim()).filter((zeile) => {
    const betraege = euroAmounts(zeile);
    return betraege.some((betrag) => werte.some((wert) => gleicheZahl(wert, betrag.value)));
  });
  return behalten.length > 0 ? behalten.join("\n") : null;
}

export function ergaenzeZahlen(answer: string, zusatz: string): string {
  const extra = zusatz.trim();
  if (!extra) return answer;
  const sections = parseAbschnitte(answer);
  const hatBetrag = euroAmounts(sections.zahlen).length > 0;
  let text = answer;
  if (!/ZAHLEN\s*:/i.test(text)) text = `${text.trim()}\n\nZAHLEN:\n${extra}`;
  else if (!hatBetrag) {
    text = text.replace(
      new RegExp(String.raw`ZAHLEN\s*:\s*[\s\S]*?(?=${NAECHSTE_UEBERSCHRIFT}|$)`, "i"),
      `ZAHLEN:\n${extra}\n\n`,
    );
  } else text = text.replace(/ZAHLEN\s*:/i, (heading) => `${heading}\n${extra}`);
  const namen = [...new Set(extra.split("\n").map((zeile) => zeile.split("|")[1]?.trim() ?? "").filter((name) => name.length >= 4))];
  const fundstellen = parseAbschnitte(text).fundstellen.toLowerCase();
  const fehlend = namen.filter((name) => !fundstellen.includes(name.toLowerCase()));
  if (fehlend.length === 0 || !/FUNDSTELLEN\s*:/i.test(text)) return text;
  return text.replace(/FUNDSTELLEN\s*:/i, (heading) => `${heading}\n${fehlend.map((name) => `- ${name}`).join("\n")}`);
}

export function nenntKeineZahlen(answer: string): boolean {
  const sections = parseAbschnitte(answer);
  const quelle = sections.vollstaendig ? sections.zahlen : answer.replace(sections.nutzerangaben, " ");
  if (euroAmounts(quelle).length > 0) return false;
  if (/keine\s+zahlen/i.test(answer)) return true;
  return sections.vollstaendig;
}

export function grenzenAusAntwort(answer: string): Grenze[] {
  const sections = parseAbschnitte(answer);
  if (sections.vollstaendig || sections.zahlen) return grenzenAusText(sections.zahlen);
  return grenzenAusText(sections.nutzerangaben ? answer.replace(sections.nutzerangaben, " ") : answer);
}

function corpusHasProzent(corpus: string, value: number): boolean {
  const pattern = /\d+(?:[.,]\d+)?\s*(?:%|prozent)/gi;
  for (const match of corpus.matchAll(pattern)) {
    const parsed = parseZahl(match[0]);
    if (parsed != null && Math.abs(parsed - value) < 0.001) return true;
  }
  return false;
}

function corpusHas(corpus: string, value: number): boolean {
  return zahlVorhanden(corpus, value);
}

export function pruefeBestaetigt(nutzerangaben: string, corpus: string, pruefer: string): { text: string; hinweise: string[] } {
  const hinweise: string[] = [];
  const text = nutzerangaben.split(/\n/).map((line) => {
    if (!/bestätigt/i.test(line)) return line;
    const zahlen = [
      ...euroAmounts(line).map((item) => ({ label: item.label, belegt: corpusHas(corpus, item.value) })),
      ...prozentWerte(line).map((item) => ({ label: item.label, belegt: corpusHasProzent(corpus, item.value) })),
    ];
    if (zahlen.length === 0) {
      const links = line.includes("|") ? line.split("|")[0].trim() : line.trim();
      return `${links} | Regel bestätigt, Zahl unbelegt`;
    }
    const fehlend = zahlen.filter((item) => !item.belegt);
    if (fehlend.length === 0) return line;
    for (const zahl of fehlend) hinweise.push(`⚠️ Ungültiges "bestätigt": ${zahl.label} (${pruefer})`);
    const links = line.includes("|") ? line.split("|")[0].trim() : line.trim();
    return `${links} | nicht belegt`;
  }).join("\n");
  return { text, hinweise };
}

export function dokumentZahlen(input: {
  answer: string;
  corpus: string;
  documentNames: string[];
  prueferLabel: string;
  liste?: ZahlenListe;
}): {
  keys: string[];
  labels: string[];
  documents: string[];
  nutzerangaben: string;
  hinweise: string[];
} {
  const sections = parseAbschnitte(input.answer);
  const hinweise: string[] = [];
  const pruefer = input.prueferLabel.match(/Prüfer\s+\d+/)?.[0] ?? input.prueferLabel;
  const corpus = input.corpus.trim();
  let source = sections.zahlen;
  if (!sections.vollstaendig) {
    hinweise.push(`⚠️ Antwortformat von ${pruefer} abweichend — Rückfall-Extraktion verwendet`);
    source = sections.nutzerangaben
      ? input.answer.replace(sections.nutzerangaben, " ")
      : input.answer;
  }
  const kept: Array<{ label: string; value: number }> = [];
  for (const amount of euroAmounts(source)) {
    const unbekannt = Boolean(input.liste) && !stehtInListe(amount.value, "euro", input.liste as ZahlenListe);
    if (corpus && !corpusHas(corpus, amount.value) && unbekannt) {
      hinweise.push(`🔴 Unbekannter Wert: ${amount.label} (${pruefer})`);
      continue;
    }
    if (corpus && !corpusHas(corpus, amount.value)) {
      hinweise.push(`⚠️ Zahl im ZAHLEN-Abschnitt ohne Beleg: ${amount.label} (${pruefer})`);
      continue;
    }
    kept.push(amount);
  }
  const fundstellenText = sections.fundstellen || (sections.vollstaendig ? "" : input.answer);
  const bestaetigt = pruefeBestaetigt(sections.nutzerangaben, corpus, pruefer);
  hinweise.push(...bestaetigt.hinweise);
  return {
    keys: kept.map((item) => item.value.toFixed(2)),
    labels: kept.map((item) => item.label),
    documents: matchedDocuments(fundstellenText, input.documentNames),
    nutzerangaben: bestaetigt.text,
    hinweise,
  };
}
