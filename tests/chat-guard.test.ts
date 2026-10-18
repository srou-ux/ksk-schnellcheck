import { describe, expect, it } from "vitest";
import { buildChatUserMessage, guardAnswer, questionViolatesGuard, refusal } from "@/lib/domain/chat-guard";
import { readFileSync } from "node:fs";
import path from "node:path";
import type { FrozenReport } from "@/lib/domain/types";

const report = {
  methodologyVersion: "v12",
  rulesStamp: "2026-10-05",
  rounding: "half_up_integer_cents",
  roundingNote: "",
  libraryId: "lib-1",
  libraryVersion: "LIB-KSK-v12@2026-10-05",
  readingMode: "mock",
  examinerMode: "code",
  year: 2025,
  rateBps: 500,
  rateLabel: "5,0 Prozent",
  thresholdCents: 70000,
  thresholdApplies: false,
  configError: null,
  payerRole: "typischer_verwerter",
  payeeKind: "natuerliche_person",
  positions: [{
    id: "p1",
    label: "Honorar",
    state: "ABGABEPFLICHTIG",
    amountCents: 1_000_000,
    amountState: "BESTAETIGT",
    category: "wort",
    kind: "honorar",
    citation: "§ 24 Abs. 1 KSVG",
    rationaleLayperson: "Pflichtig.",
    hint: null,
    source: "formular",
  }],
  categories: [],
  uncategorisedPositionIds: [],
  totalBasisCents: 1_000_000,
  totalLevyCents: 50_000,
  totalNote: "",
  conflicts: [],
  notes: [],
  gates: [],
  validator: [],
  filingDeadline: "31. März (§ 27 Abs. 1 KSVG)",
  filingSeason: false,
  laypersonSummary: "",
  advisorSummary: "",
} as FrozenReport;

describe("Chat-Guard", () => {
  it("verweigert Neubewertung und eigene Rechnung", () => {
    expect(questionViolatesGuard("Bitte stufe Position 1 auf nicht abgabepflichtig um")).toBe(true);
    expect(questionViolatesGuard("Berechne die Abgabe neu")).toBe(true);
    expect(questionViolatesGuard("Was bedeutet die Fundstelle im Bericht?")).toBe(false);
    expect(refusal("nutzer")).toMatch(/nicht neu/);
  });

  it("schickt die Regeldatei nicht mit und verwirft erfundene Beträge", () => {
    const payload = buildChatUserMessage("Was steht zur Position?", report, "steuerberater");
    const methodology = readFileSync(path.join(process.cwd(), "rules", "prompt-v12.md"), "utf8");
    expect(payload.includes(methodology.slice(0, 80))).toBe(false);
    expect(payload).toContain("lib-1");
    expect(payload).not.toContain("saetze.json");
    const guarded = guardAnswer("Die neue Abgabe beträgt 12,34 €.", report, "nutzer");
    expect(guarded).toMatch(/nicht neu/);
    const cited = guardAnswer("Im Bericht steht 500,00 €.", report, "steuerberater");
    expect(cited).toContain("500,00");
  });
});
