import { describe, expect, it } from "vitest";
import { mergeUnanimous, readingsAgree } from "@/lib/domain/consensus";
import { parseMarker } from "@/lib/domain/parse-reading";
import type { ParsedReading } from "@/lib/domain/types";
import { readFileSync } from "node:fs";
import path from "node:path";
import { PHASE2_MESSAGE, startEvidenceRerun } from "@/lib/phase2/nachweis";

const sample: ParsedReading = {
  readable: true,
  year: 2025,
  payerName: "Verlag",
  payerRole: "typischer_verwerter",
  payeeName: "Ada",
  payeeKind: "natuerliche_person",
  annualSumConfirmed: true,
  statedNetTotalCents: 100,
  positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 100 }],
};

describe("Stufen", () => {
  it("verlangt drei gleiche Ablesungen", () => {
    expect(readingsAgree([sample, sample])).toBe(false);
    expect(readingsAgree([sample, sample, sample])).toBe(true);
    expect(readingsAgree([sample, sample, { ...sample, year: 2026 }])).toBe(false);
  });

  it("übernimmt bei Abweichung nur die dreistimmigen Felder", () => {
    const other = { ...sample, year: 2026, payerName: "Anderer Verlag" };
    const merged = mergeUnanimous([sample, sample, other]);
    expect(merged.readable).toBe(true);
    expect(merged.year).toBeNull();
    expect(merged.payerName).toBeNull();
    expect(merged.statedNetTotalCents).toBe(100);
    expect(merged.positions[0]?.netCents).toBe(100);
  });

  it("liest nur den markierten Block und keinen geratenen Betrag", () => {
    const parsed = parseMarker("Freitext ohne Block");
    expect(parsed).toBeNull();
    const marked = parseMarker("---KSK-FELDER---\njahr: 2026\nrolle: eigenwerbung\nempfaengerart: natuerliche_person\njahressumme: nein\nsumme_netto: 39000\nposition: Text|honorar|wort|39000\n---ENDE---");
    expect(marked?.year).toBe(2026);
    expect(marked?.statedNetTotalCents).toBe(39000);
  });
});

describe("Grenzen der Phase", () => {
  it("bietet keinen Re-Run", () => {
    expect(() => startEvidenceRerun()).toThrow(PHASE2_MESSAGE);
  });

  it("importiert den Library-Upload nicht in die Pipeline", () => {
    const source = readFileSync(path.join(process.cwd(), "src", "lib", "pipeline", "run.ts"), "utf8");
    expect(source.includes("uploadReferenceFile")).toBe(false);
  });

  it("hält den Schlüssel aus dem Client", () => {
    const files = ["src/components/case-workspace.tsx", "src/components/admin-console.tsx", "src/components/chat-panel.tsx", "src/app/faelle/neu/page.tsx"];
    for (const file of files) {
      const source = readFileSync(path.join(process.cwd(), file), "utf8");
      expect(source.includes("MISTRAL_API_KEY")).toBe(false);
      expect(source.includes("secrets.env")).toBe(false);
    }
  });
});
