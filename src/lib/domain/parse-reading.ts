import type { ParsedPosition, ParsedReading, PayerRole, PayeeKind, PositionKind, KskCategory } from "./types";
import { isSafeCents, normText } from "./consensus";

const ROLES = new Set<PayerRole>(["typischer_verwerter", "eigenwerbung", "generalklausel"]);
const PAYEES = new Set<PayeeKind>(["natuerliche_person", "gesellschaft"]);
const KINDS = new Set<PositionKind>(["honorar", "material", "reise", "bewirtung", "gemischt", "drittleistung", "umsatzsteuer"]);
const CATEGORIES = new Set<KskCategory>(["wort", "bildende_kunst", "musik", "darstellende_kunst"]);

export function parseModelJson(text: string): ParsedReading | null {
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) return null;
  try {
    return parseUnknown(JSON.parse(match[0]) as unknown);
  } catch {
    return null;
  }
}

export function parseMarker(text: string): ParsedReading | null {
  const match = text.match(/---KSK-FELDER---([\s\S]*?)---ENDE---/);
  if (!match) return null;
  const lines = match[1].split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const reading: ParsedReading = {
    readable: true,
    year: null,
    payerName: null,
    payerRole: null,
    payeeName: null,
    payeeKind: null,
    annualSumConfirmed: null,
    statedNetTotalCents: null,
    positions: [],
  };
  for (const line of lines) {
    const [rawKey, ...rest] = line.split(":");
    const key = rawKey.trim().toLowerCase();
    const value = rest.join(":").trim();
    if (key === "jahr") reading.year = parseYear(value);
    if (key === "auftraggeber") reading.payerName = normText(value);
    if (key === "rolle") reading.payerRole = asRole(value);
    if (key === "leistender") reading.payeeName = normText(value);
    if (key === "empfaengerart") reading.payeeKind = asPayee(value);
    if (key === "jahressumme") reading.annualSumConfirmed = value === "ja" ? true : value === "nein" ? false : null;
    if (key === "summe_netto") reading.statedNetTotalCents = parseCents(value);
    if (key === "position") {
      const position = parsePositionLine(value);
      if (position) reading.positions.push(position);
    }
  }
  return reading;
}

function parsePositionLine(value: string): ParsedPosition | null {
  const [label, kind, category, cents] = value.split("|").map((part) => part.trim());
  if (!label || !kind || !category || !cents) return null;
  return {
    label: normText(label),
    kind: asKind(kind),
    category: asCategory(category),
    netCents: parseCents(cents),
  };
}

function parseUnknown(value: unknown): ParsedReading | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const positions = Array.isArray(row.positions) ? row.positions.map(parsePositionObject).filter((item): item is ParsedPosition => item !== null) : [];
  return {
    readable: row.readable !== false,
    year: parseYear(row.year),
    payerName: typeof row.payerName === "string" ? normText(row.payerName) : null,
    payerRole: asRole(row.payerRole),
    payeeName: typeof row.payeeName === "string" ? normText(row.payeeName) : null,
    payeeKind: asPayee(row.payeeKind),
    annualSumConfirmed: typeof row.annualSumConfirmed === "boolean" ? row.annualSumConfirmed : null,
    statedNetTotalCents: parseCents(row.statedNetTotalCents),
    positions,
  };
}

function parsePositionObject(value: unknown): ParsedPosition | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  return {
    label: typeof row.label === "string" ? normText(row.label) : null,
    kind: asKind(row.kind),
    category: asCategory(row.category),
    netCents: parseCents(row.netCents),
  };
}

function parseYear(value: unknown): number | null {
  const year = typeof value === "number" ? value : typeof value === "string" && /^\d{4}$/.test(value) ? Number(value) : null;
  if (year === null || !Number.isInteger(year) || year < 1990 || year > 2100) return null;
  return year;
}

function parseCents(value: unknown): number | null {
  if (typeof value === "string" && /^\d+$/.test(value)) return isSafeCents(Number(value)) ? Number(value) : null;
  return isSafeCents(value) ? value : null;
}

function asRole(value: unknown): PayerRole | null {
  return typeof value === "string" && ROLES.has(value as PayerRole) ? (value as PayerRole) : null;
}

function asPayee(value: unknown): PayeeKind | null {
  return typeof value === "string" && PAYEES.has(value as PayeeKind) ? (value as PayeeKind) : null;
}

function asKind(value: unknown): PositionKind | null {
  return typeof value === "string" && KINDS.has(value as PositionKind) ? (value as PositionKind) : null;
}

function asCategory(value: unknown): KskCategory | null {
  return typeof value === "string" && CATEGORIES.has(value as KskCategory) ? (value as KskCategory) : null;
}

export function emptyReading(): ParsedReading {
  return {
    readable: false,
    year: null,
    payerName: null,
    payerRole: null,
    payeeName: null,
    payeeKind: null,
    annualSumConfirmed: null,
    statedNetTotalCents: null,
    positions: [],
  };
}
