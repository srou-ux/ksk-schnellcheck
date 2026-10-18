import type { ConfirmedInvoice, ConfirmedPosition } from "./types";
import { UNCLEAR } from "./types";
import { fieldFromUnanimous } from "./consensus";

const BETRAG = /-?\d{1,3}(?:\.\d{3})*,\d{2}/;

function centAusText(value: string): number {
  const negative = value.trim().startsWith("-");
  const cents = Math.round(Number(value.replace("-", "").replace(/\./g, "").replace(",", ".")) * 100);
  return negative ? -cents : cents;
}

function betragAmEnde(line: string): number | null {
  const match = line.trim().match(new RegExp(`(${BETRAG.source})\\s*(?:EUR)?\\s*$`));
  return match ? centAusText(match[1]) : null;
}

export function zeilenAusRechnungstext(text: string): { statedNetCents: number; positions: Array<{ label: string; netCents: number }> } | null {
  const candidates = [
    ...text.matchAll(new RegExp(`Nettosumme:\\s*(${BETRAG.source})`, "g")),
    ...text.matchAll(new RegExp(`Summe der Positionen netto\\s+(${BETRAG.source})`, "g")),
  ].map((item) => centAusText(item[1]));
  if (candidates.length === 0) return null;
  const headers = [...text.matchAll(new RegExp(`(?:^|\\n)(\\d{2})[ \\t]+(?:·[ \\t]+)?([^\\n]+)`, "g"))];
  if (headers.length === 0) return null;
  const positions: Array<{ label: string; netCents: number }> = [];
  for (let index = 0; index < headers.length; index += 1) {
    const header = headers[index];
    const start = header.index ?? 0;
    const end = index + 1 < headers.length ? (headers[index + 1].index ?? text.length) : text.length;
    const block = text.slice(start, end).split(/\n(?:Nettosumme:|Summe der Positionen netto)/)[0];
    const headerLine = header[0].replace(/^\n/, "");
    const onLine = betragAmEnde(headerLine);
    const amounts = [...block.matchAll(new RegExp(BETRAG.source, "g"))].map((item) => centAusText(item[0]));
    const netCents = onLine ?? amounts.at(-1);
    if (netCents === undefined || netCents === null) return null;
    const labelBody = header[2].replace(new RegExp(`\\s*${BETRAG.source}\\s*(?:EUR)?\\s*$`), "").trim();
    positions.push({ label: `${header[1]} ${labelBody}`, netCents });
  }
  const sum = positions.reduce((total, item) => total + item.netCents, 0);
  if (!candidates.includes(sum)) return null;
  return { statedNetCents: sum, positions };
}

export function uebernehmeTextzeilen(invoice: ConfirmedInvoice, text: string): ConfirmedInvoice {
  const zeilen = zeilenAusRechnungstext(text);
  if (!zeilen) return invoice;
  const vorhandeneSumme = invoice.positions.reduce((total, position) => {
    return typeof position.netCents.value === "number" ? total + position.netCents.value : total;
  }, 0);
  if (invoice.positions.length > 0 && vorhandeneSumme === zeilen.statedNetCents) return invoice;
  const positions: ConfirmedPosition[] = zeilen.positions.map((line, index) => ({
    id: `p${index + 1}`,
    label: fieldFromUnanimous(line.label, 1, null),
    kind: { value: UNCLEAR, agreement: "ungeklaert", attempts: 1, reason: "Die Zeile nennt den Betrag. Ob sie Honorar, Reise, Material oder eine Gesellschaftsleistung ist, bleibt offen." },
    category: { value: UNCLEAR, agreement: "ungeklaert", attempts: 1, reason: "Die KSK-Kategorie steht nicht ausdrücklich in der Zeile." },
    netCents: fieldFromUnanimous(line.netCents, 1, null),
    source: "fliesstext",
  }));
  return {
    ...invoice,
    readable: true,
    unreadableReason: null,
    statedNetTotalCents: fieldFromUnanimous(zeilen.statedNetCents, 1, null),
    positions,
    notes: [...invoice.notes, "Die Zeilenbeträge sind der jeweils letzte Nettobetrag im Rechnungstext. Ihre Summe entspricht der Nettosumme."],
  };
}
