import type { Audience, FrozenReport } from "./types";
import { METHODOLOGY_VERSION } from "./types";
import type { Evaluation } from "./evaluate";
import { totalsFromEvaluation } from "./evaluate";
import type { ConfirmedInvoice } from "./types";
import type { GateResult, ValidatorCheck } from "./types";
import type { RuleSet } from "./types";
import { formatEuro, formatPercentFromBps, isFilingSeason } from "./money";
import { CATEGORY_LABEL } from "./labels";

const CATEGORY_ORDER = ["wort", "bildende_kunst", "musik", "darstellende_kunst"] as const;

export function buildReport(input: {
  invoice: ConfirmedInvoice;
  evaluation: Evaluation;
  gates: GateResult[];
  validator: ValidatorCheck[];
  rules: RuleSet;
  libraryId: string | null;
  libraryVersion: string | null;
  readingMode: "mock" | "mistral";
  examinerMode: "code" | "mistral";
  now: Date;
}): FrozenReport {
  const totals = totalsFromEvaluation(input.evaluation, input.rules);
  const season = isFilingSeason(input.now);
  const summary = summarize(input.invoice, input.evaluation, totals.totalLevyCents, input.readingMode);
  return {
    methodologyVersion: METHODOLOGY_VERSION,
    rulesStamp: input.rules.rates.stamp,
    rounding: input.rules.rates.rounding,
    roundingNote: input.rules.rates.roundingNote,
    libraryId: input.libraryId,
    libraryVersion: input.libraryVersion,
    readingMode: input.readingMode,
    examinerMode: input.examinerMode,
    year: input.evaluation.year,
    rateBps: input.evaluation.rateBps,
    rateLabel: input.evaluation.rateLabel,
    thresholdCents: input.evaluation.thresholdCents,
    thresholdApplies: input.evaluation.thresholdApplies,
    configError: input.evaluation.configError,
    payerRole: input.invoice.payerRole.value,
    payeeKind: input.invoice.payeeKind.value,
    positions: input.evaluation.positions,
    categories: totals.buckets.map((bucket) => ({
      ...bucket,
      label: CATEGORY_LABEL[bucket.category],
    })),
    uncategorisedPositionIds: totals.uncategorisedPositionIds,
    totalBasisCents: totals.totalBasisCents,
    totalLevyCents: totals.totalLevyCents,
    totalNote: totalNote(input.evaluation, totals.totalLevyCents),
    conflicts: input.invoice.conflicts,
    notes: input.invoice.notes,
    gates: input.gates,
    validator: input.validator,
    filingDeadline: "31. März (§ 27 Abs. 1 KSVG)",
    filingSeason: season,
    laypersonSummary: summary.lay,
    advisorSummary: summary.advisor,
    registerIds: input.evaluation.registerIds,
    registerSnapshot: input.evaluation.registerSnapshot,
  };
}

function totalNote(evaluation: Evaluation, levy: number | null): string {
  if (evaluation.configError) return evaluation.configError;
  if (levy === null) {
    return "Es wird keine Abgabe als geschuldet ausgewiesen. Dafür fehlen eine vollständige Einordnung, ein bestätigter Betrag oder der Abgabesatz.";
  }
  if (evaluation.thresholdResult === "ueberstiegen" && evaluation.thresholdApplies) {
    return "Die Grenze ist überschritten. Ausgewiesen ist nur die Abgabe auf die Beträge dieses Falls. Weitere Entgelte desselben Jahres liegen hier nicht vor.";
  }
  return `Ausgewiesen ist die Abgabe auf die bestätigte Bemessungsgrundlage mit ${evaluation.rateBps ? formatPercentFromBps(evaluation.rateBps) : "ungeklärtem Satz"}.`;
}

function summarize(invoice: ConfirmedInvoice, evaluation: Evaluation, levy: number | null, readingMode: "mock" | "mistral"): { lay: string; advisor: string } {
  const mode = readingMode === "mock"
    ? " Die Ablesung lief im Mock-Modus und ist keine Mistral-Prüfung."
    : "";
  if (!invoice.readable) {
    const text = `Wir konnten die Rechnung nicht prüfen, weil sie nicht übereinstimmend lesbar war. Das sagt nichts darüber, ob eine Abgabe anfällt.${mode}`;
    return { lay: text, advisor: text };
  }
  if (invoice.positions.length === 0) {
    const text = `Gelesen wurde das Jahr ${evaluation.year ?? "nicht"}. Die Einzelpositionen waren nicht in allen drei Ablesungen gleich, deshalb werden keine Bemessungsgrundlage und keine Abgabe ausgewiesen.${mode}`;
    return { lay: text.trim(), advisor: text.trim() };
  }
  const unclear = evaluation.positions.filter((position) => position.state === "UNGEKLÄRT").length;
  const due = evaluation.positions.filter((position) => position.state === "ABGABEPFLICHTIG").length;
  const lay = unclear > 0
    ? `${unclear} Position${unclear === 1 ? "" : "en"} bleiben ungeklärt. ${due} Position${due === 1 ? " ist" : "en sind"} als abgabepflichtig eingeordnet. Eine Abgabe wird ${levy === null ? "nicht als Betrag ausgewiesen" : `mit ${formatEuro(levy)} auf der bestätigten Bemessungsgrundlage ausgewiesen`}.${mode}`
    : `Alle Positionen sind eingeordnet. ${levy === null ? "Eine Abgabe wird nicht ausgewiesen." : `Die Abgabe auf der bestätigten Bemessungsgrundlage beträgt ${formatEuro(levy)}.`} ${mode}`.trim();
  const advisor = `Methodik ${METHODOLOGY_VERSION}, Quellenstand ${evaluation.rateLabel ?? "ohne Satzfundstelle"}. Bemessungsgrundlage und Abgabe nur, wo die Tore das tragen. ${lay}`;
  return { lay, advisor };
}

export function audienceSummary(report: FrozenReport, audience: Audience): string {
  return audience === "steuerberater" ? report.advisorSummary : report.laypersonSummary;
}

export const categoryOrder = CATEGORY_ORDER;
