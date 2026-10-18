import type { Field, ParsedPosition, ParsedReading } from "./types";
import { UNCLEAR } from "./types";

export function isSafeCents(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function samePosition(a: ParsedPosition, b: ParsedPosition): boolean {
  return a.label === b.label && a.kind === b.kind && a.category === b.category && a.netCents === b.netCents;
}

export function readingsAgree(voices: ParsedReading[]): boolean {
  if (voices.length < 3) return false;
  const [first, ...rest] = voices;
  return rest.every((voice) => JSON.stringify(canonical(voice)) === JSON.stringify(canonical(first)));
}

function sameValue<T>(values: Array<T | null>): T | null {
  if (values.length !== 3) return null;
  const first = values[0];
  if (first === null) return null;
  return values.every((value) => value === first) ? first : null;
}

/** Nur Werte, die in allen drei Ablesungen gleich und vorhanden sind. Abweichungen bleiben leer. */
export function mergeUnanimous(voices: ParsedReading[]): ParsedReading {
  const positions = mergePositions(voices);
  const reading: ParsedReading = {
    readable: false,
    year: sameValue(voices.map((voice) => voice.year)),
    payerName: sameValue(voices.map((voice) => normText(voice.payerName))),
    payerRole: sameValue(voices.map((voice) => voice.payerRole)),
    payeeName: sameValue(voices.map((voice) => normText(voice.payeeName))),
    payeeKind: sameValue(voices.map((voice) => voice.payeeKind)),
    annualSumConfirmed: sameValue(voices.map((voice) => voice.annualSumConfirmed)),
    statedNetTotalCents: sameValue(voices.map((voice) => voice.statedNetTotalCents)),
    positions,
  };
  reading.readable = voices.every((voice) => voice.readable) && (
    reading.year !== null
    || reading.payerName !== null
    || reading.payeeName !== null
    || reading.statedNetTotalCents !== null
    || positions.some((position) => position.netCents !== null || position.kind !== null)
  );
  return reading;
}

function mergePositions(voices: ParsedReading[]): ParsedPosition[] {
  const count = voices[0]?.positions.length ?? 0;
  if (voices.length !== 3 || voices.some((voice) => voice.positions.length !== count)) return [];
  return voices[0].positions.map((_, index) => ({
    label: sameValue(voices.map((voice) => normText(voice.positions[index]?.label ?? null))),
    kind: sameValue(voices.map((voice) => voice.positions[index]?.kind ?? null)),
    category: sameValue(voices.map((voice) => voice.positions[index]?.category ?? null)),
    netCents: sameValue(voices.map((voice) => voice.positions[index]?.netCents ?? null)),
  }));
}

function canonical(reading: ParsedReading): ParsedReading {
  return {
    ...reading,
    payerName: normText(reading.payerName),
    payeeName: normText(reading.payeeName),
    positions: reading.positions.map((position) => ({
      ...position,
      label: normText(position.label),
    })),
  };
}

/** NFC und Trimmen. Großschreibung bleibt, weil der Text wörtlich gleich sein muss. */
export function normText(value: string | null): string | null {
  if (value === null) return null;
  const trimmed = value.normalize("NFC").trim().replace(/\s+/g, " ");
  return trimmed.length ? trimmed : null;
}

export function fieldFromUnanimous<T>(value: T | null, attempts: number, reason: string | null): Field<T> {
  if (value === null) {
    return { value: UNCLEAR, agreement: "ungeklaert", attempts, reason: reason ?? "Alle drei Ablesungen kamen ohne Wert zurück." };
  }
  return { value, agreement: "einstimmig", attempts, reason: null };
}

export function unclearField<T>(attempts: number, reason: string): Field<T> {
  return { value: UNCLEAR, agreement: "ungeklaert", attempts, reason };
}

export function positionsAgree(voices: ParsedReading[]): boolean {
  const counts = new Set(voices.map((voice) => voice.positions.length));
  if (counts.size !== 1) return false;
  const count = voices[0]?.positions.length ?? 0;
  for (let index = 0; index < count; index += 1) {
    const items = voices.map((voice) => voice.positions[index]);
    if (items.some((item) => !item)) return false;
    const first = items[0];
    if (!items.every((item) => samePosition(item, first))) return false;
  }
  return true;
}
