import { readFileSync } from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { stelleTestSaetzeFrei } from "./berechnungsfreigabe";
import { confirmedFromParsed, reconcile, type StageReading } from "@/lib/domain/reconcile";
import { evaluateInvoice, totalsFromEvaluation } from "@/lib/domain/evaluate";
import { gateMath, allGates } from "@/lib/domain/gates";
import { levyCents } from "@/lib/domain/money";
import { readRuleSet } from "@/lib/domain/rules";
import type { ParsedReading } from "@/lib/domain/types";
import { buildReport } from "@/lib/domain/report";

const rules = readRuleSet();

function reading(partial: Partial<ParsedReading>): ParsedReading {
  return {
    readable: true,
    year: 2025,
    payerName: "Verlag Beispiel",
    payerRole: "typischer_verwerter",
    payeeName: "Ada Autor",
    payeeKind: "natuerliche_person",
    annualSumConfirmed: true,
    statedNetTotalCents: 0,
    positions: [],
    ...partial,
  };
}

beforeAll(() => {
  stelleTestSaetzeFrei();
});

describe("Rücktests v12", () => {
  it("rundet kaufmännisch auf ganze Cent", () => {
    expect(levyCents(1_000_000, 500)).toBe(50_000);
    expect(levyCents(10, 500)).toBe(1);
    expect(levyCents(9, 500)).toBe(0);
    expect(rules.rates.years["2027"]).toBeUndefined();
  });

  it("390-Euro-Fall bleibt ungeklärt, weil die Jahressumme fehlt", () => {
    const invoice = confirmedFromParsed(reading({
      payerRole: "eigenwerbung",
      annualSumConfirmed: false,
      statedNetTotalCents: 39000,
      positions: [{ label: "Text", kind: "honorar", category: "wort", netCents: 39000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.positions[0]?.state).toBe("UNGEKLÄRT");
    expect(evaluation.configError).toBeNull();
    const totals = totalsFromEvaluation(evaluation, rules);
    expect(totals.totalLevyCents).toBeNull();
    expect(allGates(invoice, evaluation).gates.every((gate) => gate.passed)).toBe(true);
  });

  it("5,0-Prozent-Fall auf 10.000 Euro ergibt 500 Euro", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 1_000_000,
      positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 1_000_000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    const totals = totalsFromEvaluation(evaluation, rules);
    expect(evaluation.positions[0]?.state).toBe("ABGABEPFLICHTIG");
    expect(totals.totalBasisCents).toBe(1_000_000);
    expect(totals.totalLevyCents).toBe(50_000);
    expect(evaluation.rateBps).toBe(500);
    const report = buildReport({
      invoice,
      evaluation,
      gates: allGates(invoice, evaluation).gates,
      validator: allGates(invoice, evaluation).validator,
      rules,
      libraryId: null,
      libraryVersion: null,
      readingMode: "mock",
      examinerMode: "code",
      now: new Date("2026-10-06T12:00:00Z"),
    });
    expect(report.methodologyVersion).toBe("v12");
    expect(report.categories.find((item) => item.category === "wort")?.levyCents).toBe(50_000);
  });

  it("fehlende Einzelpositionen bilden keine Nullsumme", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 895600,
      positions: [],
    }));
    const gate = gateMath(invoice);
    expect(gate.passed).toBe(true);
    expect(gate.layperson).toContain("nicht dreistimmig");
  });

  it("Summenfehler lässt das Mathe-Tor scheitern", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 35000,
      positions: [
        { label: "A", kind: "honorar", category: "wort", netCents: 10000 },
        { label: "B", kind: "honorar", category: "musik", netCents: 20000 },
      ],
    }));
    const gate = gateMath(invoice);
    expect(gate.passed).toBe(false);
    expect(gate.layperson).toContain("350,00");
    expect(gate.layperson).toContain("300,00");
  });

  it("S3a: genau 700 Euro im Jahr 2025 übersteigen die Grenze nicht", () => {
    const invoice = confirmedFromParsed(reading({
      payerRole: "generalklausel",
      annualSumConfirmed: true,
      statedNetTotalCents: 70000,
      positions: [{ label: "Gestaltung", kind: "honorar", category: "bildende_kunst", netCents: 70000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.thresholdResult).toBe("nicht_ueberstiegen");
    expect(evaluation.positions[0]?.state).toBe("NICHT_ABGABEPFLICHTIG");
    expect(totalsFromEvaluation(evaluation, rules).totalLevyCents).toBe(0);
  });

  it("2027 ist ein sichtbarer Konfigurationsfehler ohne Ersatzsatz", () => {
    const invoice = confirmedFromParsed(reading({
      year: 2027,
      statedNetTotalCents: 100000,
      positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 100000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.configError).toMatch(/2027/);
    expect(evaluation.rateBps).toBeNull();
    expect(allGates(invoice, evaluation).gates.find((gate) => gate.id === "validator")?.passed).toBe(false);
  });

  it("eine einzelne Rechnung über der Grenze ist pflichtig, auch ohne weitere Belege", () => {
    const invoice = confirmedFromParsed(reading({
      year: 2026,
      payerRole: "eigenwerbung",
      annualSumConfirmed: false,
      statedNetTotalCents: 150000,
      positions: [{ label: "Kampagne", kind: "honorar", category: "wort", netCents: 150000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.positions[0]?.state).toBe("ABGABEPFLICHTIG");
    expect(evaluation.rateBps).toBe(490);
    expect(totalsFromEvaluation(evaluation, rules).totalLevyCents).toBe(levyCents(150000, 490));
  });
});

describe("Formular führt", () => {
  it("behält den Formularbetrag, wenn der Fließtext abweicht", () => {
    const form: StageReading = {
      agreed: true,
      attempts: 1,
      reason: null,
      parsed: reading({
        statedNetTotalCents: 10000,
        positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 10000 }],
      }),
    };
    const text: StageReading = {
      agreed: true,
      attempts: 1,
      reason: null,
      parsed: reading({
        statedNetTotalCents: 20000,
        positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 20000 }],
      }),
    };
    const invoice = reconcile(form, text);
    expect(invoice.statedNetTotalCents.value).toBe(10000);
    expect(invoice.positions[0]?.netCents.value).toBe(10000);
    expect(invoice.conflicts.every((conflict) => conflict.resolution === "formular")).toBe(true);
  });
});

describe("Hinweise", () => {
  it("hängen an einer pflichtigen Reiseposition und ändern die Einordnung nicht", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 80000,
      positions: [
        { label: "Gage", kind: "honorar", category: "musik", netCents: 50000 },
        { label: "Fahrt", kind: "reise", category: "musik", netCents: 30000 },
      ],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    const travel = evaluation.positions[1];
    expect(travel?.state).toBe("ABGABEPFLICHTIG");
    expect(travel?.hint?.dependency).toBe("unselbstaendig");
    expect(travel?.hint?.classification).toBe("ABGABEPFLICHTIG");
    expect(travel?.hint?.note).toMatch(/erschafft ihn nicht/);
  });
});

describe("Fundstelle Werklieferung", () => {
  it("wird in der Methodik nicht als gültige Norm geführt", () => {
    const method = readFileSync(path.join(process.cwd(), "rules", "prompt-v12.md"), "utf8");
    expect(method).toContain("darf nicht zitiert werden");
    expect(method).not.toContain("Werklieferung ist nach § 23 Abs. 1 Satz 2 ausgenommen");
  });
});
