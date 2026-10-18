import type { ConfirmedInvoice, Field, GateResult, ReportPosition, ValidatorCheck } from "./types";
import { UNCLEAR } from "./types";
import type { Evaluation } from "./evaluate";

function numericFieldPublished<T>(field: Field<T>, label: string): string | null {
  if (typeof field.value === "number" && field.agreement !== "einstimmig") {
    return `${label} wäre als Zahl ausgegeben, obwohl die Ablesung nicht einstimmig war.`;
  }
  if (field.agreement === "ungeklaert" && field.value !== UNCLEAR) {
    return `${label} ist weder einstimmig noch als ungeklärt gekennzeichnet.`;
  }
  return null;
}

export function gateNumbers(invoice: ConfirmedInvoice): GateResult {
  const problems: string[] = [];
  const year = numericFieldPublished(invoice.year, "Das Jahr");
  const total = numericFieldPublished(invoice.statedNetTotalCents, "Die Nettosumme");
  if (year) problems.push(year);
  if (total) problems.push(total);
  for (const position of invoice.positions) {
    const found = numericFieldPublished(position.netCents, `Der Betrag von ${position.id}`);
    if (found) problems.push(found);
  }
  return {
    id: "dreistimmigkeit_zahlen",
    title: "Dreistimmigkeit der Zahlen",
    passed: problems.length === 0,
    layperson: problems.length === 0
      ? "Jede genannte Zahl ist entweder einstimmig abgelesen oder ausdrücklich ungeklärt."
      : `Wir konnten die Zahlen nicht freigeben, weil ${problems.join(" ")}`,
  };
}

export function gateForm(invoice: ConfirmedInvoice): GateResult {
  const broken = invoice.conflicts.filter((conflict) => conflict.resolution !== "formular");
  return {
    id: "form_konsens",
    title: "Form-Konsens",
    passed: broken.length === 0,
    layperson: broken.length === 0
      ? invoice.conflicts.length
        ? "Wo Formular und Fließtext voneinander abweichen, bleibt der Formularwert."
        : "Formular und Fließtext widersprechen sich nicht."
      : "Ein abweichender Fließtext hätte den Formularwert verdrängt. Das lassen wir nicht zu.",
  };
}

export function comparableNet(invoice: ConfirmedInvoice): { sum: number | null; stated: number | null; reason: string | null } {
  if (invoice.statedNetTotalCents.value === UNCLEAR) {
    return { sum: null, stated: null, reason: "Die ausgewiesene Nettosumme ist ungeklärt. Es gibt deshalb keinen Summenwiderspruch, aber auch keine bestätigte Gesamtsumme." };
  }
  if (invoice.positions.length === 0) {
    return { sum: null, stated: invoice.statedNetTotalCents.value, reason: "Die Einzelpositionen waren nicht dreistimmig. Die ausgewiesene Summe wird nicht aus 0,00 € bestätigt." };
  }
  let sum = 0;
  for (const position of invoice.positions) {
    if (position.kind.value === "umsatzsteuer") continue;
    if (position.netCents.value === UNCLEAR) {
      return { sum: null, stated: invoice.statedNetTotalCents.value, reason: "Mindestens ein Nettobetrag ist ungeklärt. Die Summe lässt sich nicht gegenprüfen." };
    }
    sum += position.netCents.value;
  }
  return { sum, stated: invoice.statedNetTotalCents.value, reason: null };
}

export function gateMath(invoice: ConfirmedInvoice): GateResult {
  const compared = comparableNet(invoice);
  if (compared.sum === null || compared.stated === null) {
    return {
      id: "mathematik",
      title: "Mathematik",
      passed: true,
      layperson: compared.reason ?? "Die Summe war nicht vollständig gegenprüfbar und wird nicht als bestätigt ausgegeben.",
    };
  }
  if (compared.sum !== compared.stated) {
    return {
      id: "mathematik",
      title: "Mathematik",
      passed: false,
      layperson: `Wir konnten die Summe nicht prüfen, weil die Netto-Positionen ${format(compared.sum)} ergeben, die Rechnung aber ${format(compared.stated)} ausweist.`,
    };
  }
  return {
    id: "mathematik",
    title: "Mathematik",
    passed: true,
    layperson: "Die Netto-Positionen ergeben in Cent genau die ausgewiesene Nettosumme.",
  };
}

function format(cents: number): string {
  const euros = Math.floor(cents / 100);
  const rest = cents % 100;
  return `${euros.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${rest.toString().padStart(2, "0")} €`;
}

export function gateContent(invoice: ConfirmedInvoice): GateResult {
  const fields = [invoice.payerName, invoice.payeeName, invoice.payerRole, invoice.payeeKind, ...invoice.positions.flatMap((position) => [position.label, position.kind, position.category])];
  const broken = fields.filter((field) => field.agreement === "ungeklaert" && field.value !== UNCLEAR);
  return {
    id: "dreistimmigkeit_inhalte",
    title: "Dreistimmigkeit der Inhalte",
    passed: broken.length === 0,
    layperson: broken.length === 0
      ? "Texte und Einordnungen sind entweder wörtlich gleichlautend oder ungeklärt."
      : "Ein Inhalt wäre ohne einstimmige Ablesung in den Bericht gelangt.",
  };
}

export function runValidators(invoice: ConfirmedInvoice, evaluation: Evaluation): ValidatorCheck[] {
  const cents = [
    invoice.year.value,
    invoice.statedNetTotalCents.value,
    ...invoice.positions.map((position) => position.netCents.value),
    ...evaluation.positions.map((position) => position.amountCents),
  ];
  const badCents = cents.filter((value) => typeof value === "number" && !Number.isSafeInteger(value));
  const math = gateMath(invoice);
  const hintsOk = evaluation.positions.every((position) => !position.hint || (position.hint.classification === "ABGABEPFLICHTIG" && position.state === "ABGABEPFLICHTIG"));
  const yearKnown = typeof invoice.year.value === "number";
  return [
    {
      id: "V01",
      passed: !yearKnown || evaluation.configError === null,
      layperson: !yearKnown
        ? "Das Jahr ist ungeklärt, deshalb wird kein Abgabesatz angesetzt."
        : evaluation.configError ?? "Für das abgelesene Jahr liegt ein Abgabesatz in der Konfiguration.",
    },
    {
      id: "V02",
      passed: badCents.length === 0,
      layperson: badCents.length === 0 ? "Alle Beträge sind ganze Cent." : "Ein Betrag ist keine ganze Cent-Zahl.",
    },
    {
      id: "V03",
      passed: math.passed,
      layperson: math.layperson,
    },
    {
      id: "V04",
      passed: invoice.conflicts.every((conflict) => conflict.resolution === "formular"),
      layperson: "Konflikte zwischen Formular und Fließtext sind zugunsten des Formulars aufgelöst.",
    },
    {
      id: "V05",
      passed: hintsOk,
      layperson: hintsOk
        ? "Kein Klärungshinweis verändert die Einordnung."
        : "Ein Hinweis hätte die Einordnung verändert. Das ist unzulässig.",
    },
    {
      id: "V06",
      passed: evaluation.configError === null || evaluation.rateBps === null,
      layperson: evaluation.configError
        ? evaluation.configError
        : "Es wurde kein Ersatzsatz für ein fehlendes Jahr verwendet.",
    },
  ];
}

export function gateValidator(checks: ValidatorCheck[]): GateResult {
  const failed = checks.filter((check) => !check.passed);
  return {
    id: "validator",
    title: "Validator",
    passed: failed.length === 0,
    layperson: failed.length === 0
      ? "Die Prüfpunkte V01 bis V06 sind bestanden."
      : failed.map((check) => `${check.id}: ${check.layperson}`).join(" "),
  };
}

export function allGates(invoice: ConfirmedInvoice, evaluation: Evaluation): { gates: GateResult[]; validator: ValidatorCheck[] } {
  const validator = runValidators(invoice, evaluation);
  return {
    validator,
    gates: [gateNumbers(invoice), gateForm(invoice), gateMath(invoice), gateContent(invoice), gateValidator(validator)],
  };
}

export function codeExamine(engine: ReportPosition[], proposal: ReportPosition[]): { consistent: boolean; finding: string | null } {
  if (engine.length !== proposal.length) {
    return { consistent: false, finding: "Der Prüfer sieht eine andere Anzahl von Positionen als die Bewertung." };
  }
  for (let index = 0; index < engine.length; index += 1) {
    const left = engine[index];
    const right = proposal[index];
    if (left.id !== right.id || left.state !== right.state || left.amountCents !== right.amountCents) {
      return {
        consistent: false,
        finding: `Widerspruch bei ${left.id}: die Bewertung sagt ${left.state} und ${left.amountCents ?? "ungeklärter Betrag"}, der Prüfer weicht davon ab.`,
      };
    }
  }
  return { consistent: true, finding: null };
}
