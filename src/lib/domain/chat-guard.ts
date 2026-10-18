import type { FrozenReport } from "./types";

const REFUSAL_USER =
  "Ich kann das nicht neu bewerten und nichts neu berechnen. Ich kann nur erklären, was im gespeicherten Bericht steht, und eine Fundstelle nennen, wenn sie dort oder in der Referenz-Library liegt.";
const REFUSAL_ADVISOR =
  "Keine Neubewertung, keine eigene Berechnung, keine Auflösung des Hinweises. Zulässig ist nur das Zitat des eingefrorenen Berichts und der aktiven Referenz-Library mit Fundstelle.";

export type ChatMode = "nutzer" | "steuerberater";

export function questionViolatesGuard(question: string): boolean {
  const text = question.toLowerCase();
  const patterns = [
    /neu\s*bewert/,
    /änder(e|n) die einordnung/,
    /stufe .* um/,
    /rechne/,
    /berechne/,
    /lösung/,
    /loesung/,
    /hinweis auflösen/,
    /hinweis aufloesen/,
    /setz(e|en) .* auf nicht/,
    /ohne nachweis/,
    /schreib .* um/,
    /gestalt/,
  ];
  return patterns.some((pattern) => pattern.test(text));
}

export function refusal(mode: ChatMode): string {
  return mode === "steuerberater" ? REFUSAL_ADVISOR : REFUSAL_USER;
}

export function buildChatUserMessage(question: string, report: FrozenReport, mode: ChatMode): string {
  const context = {
    modus: mode,
    methodik: report.methodologyVersion,
    libraryId: report.libraryId,
    positionen: report.positions.map((position) => ({
      id: position.id,
      zustand: position.state,
      betragCent: position.amountCents,
      fundstelle: position.citation,
      hinweis: position.hint
        ? {
            grund: position.hint.possibleExclusionReason,
            fundstelle: position.hint.citation,
            nachweis: position.hint.requiredEvidence,
            wirktNicht: position.hint.whenEvidenceDoesNotWork,
          }
        : null,
    })),
  };
  return [`Frage: ${question}`, `Modus: ${mode}`, `Berichts-Kontext: ${JSON.stringify(context)}`].join("\n");
}

export function guardAnswer(answer: string, report: FrozenReport, mode: ChatMode): string {
  const lowered = answer.toLowerCase();
  const banned = [/neu einzustufen/, /ich berechne/, /die lösung ist/, /die loesung ist/, /damit entfällt die abgabe/, /damit faellt die abgabe/, /ich setze .* auf/];
  if (banned.some((pattern) => pattern.test(lowered))) return refusal(mode);
  const allowed = amountsInReport(report);
  const mentioned = answer.match(/\d{1,3}(?:\.\d{3})*,\d{2}\s*€/g) ?? [];
  for (const amount of mentioned) {
    if (!allowed.has(normalizeAmount(amount))) return refusal(mode);
  }
  return answer;
}

function amountsInReport(report: FrozenReport): Set<string> {
  const values = [report.totalLevyCents, report.totalBasisCents, report.thresholdCents, ...report.positions.map((position) => position.amountCents)];
  return new Set(values.filter((value): value is number => typeof value === "number").map((value) => formatKey(value)));
}

function formatKey(cents: number): string {
  const euros = Math.floor(Math.abs(cents) / 100);
  const rest = Math.abs(cents) % 100;
  return `${euros},${rest.toString().padStart(2, "0")}`;
}

function normalizeAmount(value: string): string {
  return value.replace(/\./g, "").replace("€", "").trim().replace(/\s/g, "");
}

export const CHAT_SYSTEM = [
  "Du bist das Lese-Interface eines eingefrorenen KSK-Berichts.",
  "Du bewertest nicht neu, du rechnest nicht, du löst keine Klärungshinweise und du glättest keine Widersprüche.",
  "Du zitierst nur den mitgeschickten Berichts-Kontext und, wenn eine Library-ID gesetzt ist, Fundstellen aus genau dieser Library.",
  "Die Regeldokumente werden dir nicht mitgeschickt. Erfinde keine Paragraphen.",
  "Wenn die Library nichts hergibt, sag das.",
  "Ein Nachweis beweist einen Vorgang. Er erschafft ihn nicht.",
].join(" ");
