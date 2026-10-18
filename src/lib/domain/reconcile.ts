import type {
  ConfirmedInvoice,
  ConfirmedPosition,
  Field,
  ParsedPosition,
  ParsedReading,
  ValueConflict,
} from "./types";
import { UNCLEAR } from "./types";
import { fieldFromUnanimous, normText, unclearField } from "./consensus";

export interface StageReading {
  parsed: ParsedReading | null;
  attempts: number;
  agreed: boolean;
  reason: string | null;
}

function pickScalar<T>(form: T | null, text: T | null, attempts: number, label: string, conflicts: ValueConflict[], notes: string[]): Field<T> {
  const formOk = form !== null;
  const textOk = text !== null;
  if (formOk && textOk && JSON.stringify(form) !== JSON.stringify(text)) {
    conflicts.push({
      field: label,
      formValue: String(form),
      textValue: String(text),
      resolution: "formular",
    });
    return fieldFromUnanimous(form, attempts, null);
  }
  if (formOk) return fieldFromUnanimous(form, attempts, null);
  if (textOk) {
    notes.push(`${label} steht nur im Fließtext. Das Formular hatte dazu keinen bestätigten Wert.`);
    return fieldFromUnanimous(text, attempts, null);
  }
  return unclearField(attempts, `${label} war im Formular und im Fließtext nicht übereinstimmend lesbar.`);
}

function positionField<T>(value: T | null, attempts: number, reason: string): Field<T> {
  return value === null ? unclearField(attempts, reason) : fieldFromUnanimous(value, attempts, null);
}

function mergePosition(index: number, form: ParsedPosition | undefined, text: ParsedPosition | undefined, attempts: number, conflicts: ValueConflict[], notes: string[]): ConfirmedPosition {
  const id = `p${index + 1}`;
  const formUsable = Boolean(form && (form.netCents !== null || form.label || form.kind));
  const textUsable = Boolean(text && (text.netCents !== null || text.label || text.kind));
  const chosen = formUsable ? form : textUsable ? text : undefined;
  const source = formUsable ? "formular" : textUsable ? "fliesstext" : "ungeklaert";
  if (formUsable && textUsable && JSON.stringify(form) !== JSON.stringify(text)) {
    conflicts.push({
      field: `Position ${id}`,
      formValue: JSON.stringify(form),
      textValue: JSON.stringify(text),
      resolution: "formular",
    });
  } else if (!formUsable && textUsable) {
    notes.push(`Position ${id} wurde nur aus dem Fließtext übernommen.`);
  }
  return {
    id,
    label: positionField(normText(chosen?.label ?? null), attempts, `Die Bezeichnung von ${id} ist ungeklärt.`),
    kind: positionField(chosen?.kind ?? null, attempts, `Die Art von ${id} ist ungeklärt.`),
    category: positionField(chosen?.category ?? null, attempts, `Die KSK-Kategorie von ${id} ist ungeklärt.`),
    netCents: positionField(chosen?.netCents ?? null, attempts, `Der Betrag von ${id} ist ungeklärt.`),
    source,
  };
}

export function reconcile(form: StageReading, text: StageReading): ConfirmedInvoice {
  const attempts = Math.max(form.attempts, text.attempts);
  const conflicts: ValueConflict[] = [];
  const notes: string[] = [];
  const formParsed = form.agreed ? form.parsed : null;
  const textParsed = text.agreed ? text.parsed : null;

  if (!form.agreed) notes.push(form.reason ?? "Die Formular-Ablesung war nicht dreistimmig.");
  else if (form.reason) notes.push(form.reason);
  if (!text.agreed) notes.push(text.reason ?? "Die Freitext-Ablesung war nicht dreistimmig.");
  else if (text.reason) notes.push(text.reason);

  const readable = Boolean(formParsed?.readable || textParsed?.readable);
  const count = Math.max(formParsed?.positions.length ?? 0, textParsed?.positions.length ?? 0);
  const positions = Array.from({ length: count }, (_, index) =>
    mergePosition(index, formParsed?.positions[index], textParsed?.positions[index], attempts, conflicts, notes),
  );

  return {
    readable,
    unreadableReason: readable ? null : "Wir konnten die Rechnung nicht lesen. Formular und Fließtext haben keinen übereinstimmenden Inhalt ergeben.",
    year: pickScalar(formParsed?.year ?? null, textParsed?.year ?? null, attempts, "Jahr", conflicts, notes),
    payerName: pickScalar(normText(formParsed?.payerName ?? null), normText(textParsed?.payerName ?? null), attempts, "Auftraggeber", conflicts, notes),
    payerRole: pickScalar(formParsed?.payerRole ?? null, textParsed?.payerRole ?? null, attempts, "Rolle des Auftraggebers", conflicts, notes),
    payeeName: pickScalar(normText(formParsed?.payeeName ?? null), normText(textParsed?.payeeName ?? null), attempts, "Leistender", conflicts, notes),
    payeeKind: pickScalar(formParsed?.payeeKind ?? null, textParsed?.payeeKind ?? null, attempts, "Art des Leistenden", conflicts, notes),
    annualSumConfirmed: pickScalar(formParsed?.annualSumConfirmed ?? null, textParsed?.annualSumConfirmed ?? null, attempts, "Jahressumme", conflicts, notes),
    statedNetTotalCents: pickScalar(formParsed?.statedNetTotalCents ?? null, textParsed?.statedNetTotalCents ?? null, attempts, "Ausgewiesene Nettosumme", conflicts, notes),
    positions,
    conflicts,
    notes,
  };
}

export function confirmedFromParsed(parsed: ParsedReading, attempts = 1): ConfirmedInvoice {
  const stage: StageReading = { parsed, attempts, agreed: true, reason: null };
  return reconcile(stage, { parsed: null, attempts, agreed: false, reason: null });
}

export { UNCLEAR };
