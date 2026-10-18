import type {
  ConfirmedInvoice,
  ConfirmedPosition,
  KskCategory,
  PositionState,
  ReportPosition,
  RuleSet,
} from "./types";
import { UNCLEAR } from "./types";
import type { RegisterSnapshot } from "@/lib/register-kennungen";
import { missingRateMessage, satzlage } from "./rules";
import { levyCents } from "./money";

export interface Evaluation {
  year: number | null;
  rateBps: number | null;
  rateLabel: string | null;
  thresholdCents: number | null;
  thresholdApplies: boolean | null;
  configError: string | null;
  positions: ReportPosition[];
  knownIncludedCents: number | null;
  thresholdResult: "ueberstiegen" | "nicht_ueberstiegen" | "offen" | "nicht_anwendbar";
  registerIds: string[];
  registerSnapshot: RegisterSnapshot[];
}

const HINT_NOTE =
  "Ein Nachweis beweist einen realen Vorgang. Er erschafft ihn nicht. Dieser Hinweis ändert die Einordnung nicht.";

function includedCents(invoice: ConfirmedInvoice, rules: RuleSet): number | null {
  let sum = 0;
  for (const position of invoice.positions) {
    if (position.kind.value === "umsatzsteuer") continue;
    if (position.kind.value === UNCLEAR || position.netCents.value === UNCLEAR) return null;
    if (!rules.scenarios.includedInBase.includes(position.kind.value)) return null;
    sum += position.netCents.value;
  }
  return sum;
}

function hintFor(position: ConfirmedPosition, rules: RuleSet) {
  if (position.kind.value === UNCLEAR) return null;
  const rule = rules.scenarios.hints.find((item) => item.kind === position.kind.value);
  if (!rule) return null;
  return {
    positionId: position.id,
    classification: "ABGABEPFLICHTIG" as const,
    dependency: rule.dependency,
    possibleExclusionReason: rule.reason,
    citation: rule.citation,
    requiredEvidence: rule.requiredEvidence,
    whenEvidenceDoesNotWork: rule.whenEvidenceDoesNotWork,
    note: HINT_NOTE,
  };
}

function decideThreshold(invoice: ConfirmedInvoice, rules: RuleSet, thresholdCents: number): Evaluation["thresholdResult"] {
  const known = includedCents(invoice, rules);
  const annualComplete = invoice.annualSumConfirmed.value === true;
  if (known !== null && known > thresholdCents) return "ueberstiegen";
  if (known !== null && annualComplete && known <= thresholdCents) return "nicht_ueberstiegen";
  return "offen";
}

function basePosition(position: ConfirmedPosition, state: PositionState, citation: string | null, rationale: string, rules: RuleSet): ReportPosition {
  const cents = position.netCents.value;
  const hint = state === "ABGABEPFLICHTIG" ? hintFor(position, rules) : null;
  return {
    id: position.id,
    label: position.label.value,
    state,
    amountCents: typeof cents === "number" ? cents : null,
    amountState: typeof cents === "number" ? "BESTAETIGT" : UNCLEAR,
    category: position.category.value,
    kind: position.kind.value,
    citation,
    rationaleLayperson: rationale,
    hint,
    source: position.source,
  };
}

export function evaluateInvoice(invoice: ConfirmedInvoice, rules: RuleSet): Evaluation {
  const year = invoice.year.value === UNCLEAR ? null : invoice.year.value;
  const lage = year === null ? null : satzlage(year);
  const rate = lage?.rate ?? null;
  const configError = year !== null && !rate ? (lage?.fehler || missingRateMessage(year)) : null;
  const role = invoice.payerRole.value === UNCLEAR ? null : rules.scenarios.roles[invoice.payerRole.value];
  const thresholdApplies = role ? role.thresholdApplies : null;
  const thresholdCents = rate?.thresholdCents ?? null;
  const thresholdResult: Evaluation["thresholdResult"] = !role
    ? "offen"
    : !role.thresholdApplies
      ? "nicht_anwendbar"
      : thresholdCents === null
        ? "offen"
        : decideThreshold(invoice, rules, thresholdCents);

  const positions = invoice.positions.map((position) =>
    classifyPosition(invoice, position, rules, { configError, thresholdResult, roleCitation: role?.citation ?? null, roleLay: role?.layperson ?? null, thresholdSource: rate?.thresholdSource ?? null }),
  );

  return {
    year,
    rateBps: rate?.rateBps ?? null,
    rateLabel: rate?.rateSource ?? null,
    thresholdCents,
    thresholdApplies,
    configError,
    positions,
    knownIncludedCents: includedCents(invoice, rules),
    thresholdResult,
    registerIds: lage?.registerIds ?? [],
    registerSnapshot: lage?.registerSnapshot ?? [],
  };
}

function classifyPosition(
  invoice: ConfirmedInvoice,
  position: ConfirmedPosition,
  rules: RuleSet,
  ctx: {
    configError: string | null;
    thresholdResult: Evaluation["thresholdResult"];
    roleCitation: string | null;
    roleLay: string | null;
    thresholdSource: string | null;
  },
): ReportPosition {
  if (!invoice.readable) {
    return basePosition(position, UNCLEAR, null, invoice.unreadableReason ?? "Die Rechnung war nicht lesbar.", rules);
  }
  if (position.kind.value === "umsatzsteuer") {
    return basePosition(
      position,
      "NICHT_ABGABEPFLICHTIG",
      "§ 25 Abs. 2 Satz 1 KSVG",
      "Gesondert ausgewiesene Umsatzsteuer gehört nicht zum Entgelt.",
      rules,
    );
  }
  if (position.netCents.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, position.netCents.reason ?? "Der Betrag ist ungeklärt.", rules);
  }
  if (position.kind.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Die Art der Position ist ungeklärt. Ohne Art lässt sich nicht sagen, ob sie zum Entgelt gehört.", rules);
  }
  if (invoice.payeeKind.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Es ist ungeklärt, ob eine natürliche Person oder eine Gesellschaft geleistet hat.", rules);
  }
  if (invoice.payeeKind.value === "gesellschaft") {
    const rule = rules.scenarios.payeeGesellschaft;
    return basePosition(position, rule.state, rule.citation, rule.reason, rules);
  }
  if (invoice.payerRole.value === UNCLEAR || !ctx.roleCitation) {
    return basePosition(position, UNCLEAR, null, "Die Rolle des Auftraggebers ist ungeklärt. Deshalb lässt sich die Abgabepflicht nicht einordnen.", rules);
  }
  if (invoice.year.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Das Kalenderjahr der Leistung ist ungeklärt. Abgabesatz und Jahresgrenze hängen am Jahr.", rules);
  }
  if (ctx.configError) {
    return basePosition(position, UNCLEAR, null, ctx.configError, rules);
  }
  if (ctx.thresholdResult === "offen") {
    return basePosition(
      position,
      UNCLEAR,
      ctx.roleCitation,
      "Die Jahresgrenze gilt für die Summe eines Kalenderjahres. Diese Rechnung allein zeigt nicht, ob die Grenze überschritten ist, und sie liegt nicht schon für sich darüber.",
      rules,
    );
  }
  if (ctx.thresholdResult === "nicht_ueberstiegen") {
    return basePosition(
      position,
      "NICHT_ABGABEPFLICHTIG",
      `${ctx.roleCitation}; ${ctx.thresholdSource ?? "Jahresgrenze"}`,
      "Die bestätigte Jahressumme übersteigt die Jahresgrenze nicht. Erst ein Überschreiten löst die Abgabepflicht aus. Genau die Grenze genügt nicht.",
      rules,
    );
  }
  const citation = ctx.roleCitation;
  const extra = ctx.thresholdResult === "ueberstiegen"
    ? " Die Jahresgrenze ist überschritten. Es zählt die betroffene Summe, nicht nur der Teil oberhalb der Grenze."
    : "";
  return basePosition(
    position,
    "ABGABEPFLICHTIG",
    `${citation}; § 25 Abs. 2 Satz 1 KSVG`,
    `${ctx.roleLay} Der Betrag bleibt im Entgelt.${extra}`,
    rules,
  );
}

export function totalsFromEvaluation(evaluation: Evaluation, rules: RuleSet) {
  const open = evaluation.positions.some((position) => position.state === UNCLEAR || position.amountState === UNCLEAR);
  const categories: KskCategory[] = ["wort", "bildende_kunst", "musik", "darstellende_kunst"];
  const buckets = categories.map((category) => {
    const rows = evaluation.positions.filter((position) => position.state === "ABGABEPFLICHTIG" && position.category === category && position.amountCents !== null);
    const basisCents = rows.reduce((sum, position) => sum + (position.amountCents ?? 0), 0);
    return {
      category,
      label: category,
      basisCents,
      levyCents: !open && evaluation.rateBps !== null && !evaluation.configError ? levyCents(basisCents, evaluation.rateBps) : null,
      positionIds: rows.map((position) => position.id),
    };
  });
  const uncategorisedPositionIds = evaluation.positions
    .filter((position) => position.state === "ABGABEPFLICHTIG" && position.category === UNCLEAR)
    .map((position) => position.id);
  const decidedBasis = evaluation.positions
    .filter((position) => position.state === "ABGABEPFLICHTIG" && position.amountCents !== null)
    .reduce((sum, position) => sum + (position.amountCents ?? 0), 0);
  const nothingDue = evaluation.positions.length > 0 && evaluation.positions.every((position) => position.state === "NICHT_ABGABEPFLICHTIG");
  const complete = !open && !evaluation.configError && evaluation.rateBps !== null && uncategorisedPositionIds.length === 0;
  const totalBasisCents = complete ? decidedBasis : nothingDue ? 0 : null;
  const totalLevyCents = complete && evaluation.rateBps !== null
    ? levyCents(decidedBasis, evaluation.rateBps)
    : nothingDue
      ? 0
      : null;
  void rules;
  return { buckets, uncategorisedPositionIds, totalBasisCents, totalLevyCents, complete };
}
