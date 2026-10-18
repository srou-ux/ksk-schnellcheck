import type { RegisterSnapshot } from "@/lib/register-kennungen";

export const METHODOLOGY_VERSION = "v12" as const;
export const UNCLEAR = "UNGEKLÄRT" as const;

export type Unclear = typeof UNCLEAR;
export type Audience = "verein" | "steuerberater";
export type PayerRole = "typischer_verwerter" | "eigenwerbung" | "generalklausel";
export type PayeeKind = "natuerliche_person" | "gesellschaft";
export type PositionKind =
  | "honorar"
  | "material"
  | "reise"
  | "bewirtung"
  | "gemischt"
  | "drittleistung"
  | "umsatzsteuer";
export type KskCategory = "wort" | "bildende_kunst" | "musik" | "darstellende_kunst";
export type PositionState = "ABGABEPFLICHTIG" | "NICHT_ABGABEPFLICHTIG" | Unclear;
export type Agreement = "einstimmig" | "ungeklaert";
export type HintDependency = "unselbstaendig" | "eigenstaendig" | "gemischt";

export interface Field<T> {
  value: T | Unclear;
  agreement: Agreement;
  attempts: number;
  reason: string | null;
}

export interface ParsedPosition {
  label: string | null;
  kind: PositionKind | null;
  category: KskCategory | null;
  netCents: number | null;
}

export interface ParsedReading {
  readable: boolean;
  year: number | null;
  payerName: string | null;
  payerRole: PayerRole | null;
  payeeName: string | null;
  payeeKind: PayeeKind | null;
  annualSumConfirmed: boolean | null;
  statedNetTotalCents: number | null;
  positions: ParsedPosition[];
}

export interface ConfirmedPosition {
  id: string;
  label: Field<string>;
  kind: Field<PositionKind>;
  category: Field<KskCategory>;
  netCents: Field<number>;
  source: "formular" | "fliesstext" | "ungeklaert";
}

export interface ValueConflict {
  field: string;
  formValue: string;
  textValue: string;
  resolution: "formular";
}

export interface ConfirmedInvoice {
  readable: boolean;
  unreadableReason: string | null;
  year: Field<number>;
  payerName: Field<string>;
  payerRole: Field<PayerRole>;
  payeeName: Field<string>;
  payeeKind: Field<PayeeKind>;
  annualSumConfirmed: Field<boolean>;
  statedNetTotalCents: Field<number>;
  positions: ConfirmedPosition[];
  conflicts: ValueConflict[];
  notes: string[];
}

export interface ClarificationHint {
  positionId: string;
  classification: "ABGABEPFLICHTIG";
  dependency: HintDependency;
  possibleExclusionReason: string;
  citation: string;
  requiredEvidence: string;
  whenEvidenceDoesNotWork: string;
  note: string;
}

export interface ReportPosition {
  id: string;
  label: string | Unclear;
  state: PositionState;
  amountCents: number | null;
  amountState: "BESTAETIGT" | Unclear;
  category: KskCategory | Unclear;
  kind: PositionKind | Unclear;
  citation: string | null;
  rationaleLayperson: string;
  hint: ClarificationHint | null;
  source: ConfirmedPosition["source"];
}

export interface CategoryBucket {
  category: KskCategory;
  label: string;
  basisCents: number;
  levyCents: number | null;
  positionIds: string[];
}

export interface GateResult {
  id: "dreistimmigkeit_zahlen" | "form_konsens" | "mathematik" | "dreistimmigkeit_inhalte" | "validator";
  title: string;
  passed: boolean;
  layperson: string;
}

export interface ValidatorCheck {
  id: "V01" | "V02" | "V03" | "V04" | "V05" | "V06";
  passed: boolean;
  layperson: string;
}

export interface FrozenReport {
  methodologyVersion: typeof METHODOLOGY_VERSION;
  rulesStamp: string;
  rounding: "half_up_integer_cents";
  roundingNote: string;
  libraryId: string | null;
  libraryVersion: string | null;
  readingMode: "mock" | "mistral";
  examinerMode: "code" | "mistral";
  year: number | null;
  rateBps: number | null;
  rateLabel: string | null;
  thresholdCents: number | null;
  thresholdApplies: boolean | null;
  configError: string | null;
  payerRole: PayerRole | Unclear;
  payeeKind: PayeeKind | Unclear;
  positions: ReportPosition[];
  categories: CategoryBucket[];
  uncategorisedPositionIds: string[];
  totalBasisCents: number | null;
  totalLevyCents: number | null;
  totalNote: string;
  conflicts: ValueConflict[];
  notes: string[];
  gates: GateResult[];
  validator: ValidatorCheck[];
  filingDeadline: string;
  filingSeason: boolean;
  laypersonSummary: string;
  advisorSummary: string;
  registerIds?: string[];
  registerSnapshot?: RegisterSnapshot[];
}

export interface RateYear {
  rateBps: number;
  thresholdCents: number;
  rateSource: string;
  thresholdSource: string;
}

export interface RateTable {
  stamp: string;
  rounding: "half_up_integer_cents";
  roundingNote: string;
  thresholdScope: string;
  years: Record<string, RateYear>;
}

export interface HintRule {
  kind: PositionKind;
  dependency: HintDependency;
  citation: string;
  reason: string;
  requiredEvidence: string;
  whenEvidenceDoesNotWork: string;
}

export interface ScenarioTable {
  version: string;
  stamp: string;
  roles: Record<
    PayerRole,
    { thresholdApplies: boolean; citation: string; layperson: string }
  >;
  payeeGesellschaft: {
    state: "NICHT_ABGABEPFLICHTIG";
    citation: string;
    reason: string;
  };
  includedInBase: PositionKind[];
  hints: HintRule[];
}

export interface RuleSet {
  rates: RateTable;
  scenarios: ScenarioTable;
}
