import { describe, expect, it } from "vitest";
import { matchedDocuments } from "../src/lib/mistral/rag-pruefung";
import { konsensVergleich, vergleicheLaeufe } from "../src/lib/model-consensus";
import { RAG_SYSTEM_PROMPT } from "../src/lib/rag-system-prompt";

const names = ["Info_12_Abgabepflicht_von_Musikvereinen.pdf", "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf"];

describe("Dreifach-Konsens", () => {
  it("erkennt Info 12 auch in der Kurzform", () => {
    expect(matchedDocuments("Siehe Info 12, Abschnitt Veranstalter.", names)).toEqual(["Info_12_Abgabepflicht_von_Musikvereinen.pdf"]);
  });

  it("meldet Konsens 3/3 bei gleichen Beträgen und Fundstellen", () => {
    const row = { ok: true, answer: "Grenze 1.000 € laut Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] };
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ...row },
      { id: "P2", label: "Prüfer 2 (medium)", ...row },
      { id: "P3", label: "Prüfer 3 (large)", ...row },
    ]);
    expect(result.line).toBe("✅ Konsens 3/3");
  });

  it("zeigt die Abweichung 2/3 mit den Beträgen", () => {
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P2", label: "Prüfer 2 (medium)", ok: true, answer: "600 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P3", label: "Prüfer 3 (large)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
    ]);
    expect(result.line).toBe("⚠️ Abweichung 2/3 — NICHT OK, keine Mehrheitsentscheidung");
    expect(result.detail).toContain("Prüfer 2: 600 €");
    expect(result.detail).toContain("Prüfer 1 & 3: 1.000 €");
  });

  it("lässt einen ausgefallenen Prüfer sichtbar und prüft den Konsens nicht", () => {
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ok: true, answer: "keine Aussage", documents: [] },
      { id: "P2", label: "Prüfer 2 (medium)", ok: false, answer: "", documents: [] },
      { id: "P3", label: "Prüfer 3 (large)", ok: true, answer: "keine Aussage", documents: [] },
    ]);
    expect(result.line).toBe("⚠️ nicht prüfbar (2/3 geantwortet)");
  });

  it("meldet bei zwei Prüfern nur die Übereinstimmung beider", () => {
    const row = { ok: true, answer: "Grenze 1.000 € laut Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] };
    const gleich = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (medium)", ...row },
      { id: "P2", label: "Prüfer 2 (large)", ...row },
    ]);
    expect(gleich.line).toBe("✅ Konsens 2/2");
    const verschieden = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (medium)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P2", label: "Prüfer 2 (large)", ok: true, answer: "600 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
    ]);
    expect(verschieden.line).toBe("❌ Kein Konsens — UNGEKLÄRT");
    expect(verschieden.line).not.toContain("2/3");
  });

  it("nimmt eine Antwort nur an, wenn drei Läufe dasselbe sagen", () => {
    const lauf = { signatur: "konsens|1000.00|Info_12", einig: true, kurz: "Prüfer 1 & 2 & 3: 1.000 € / Info_12" };
    const gleich = vergleicheLaeufe([lauf, lauf, { ...lauf }]);
    expect(gleich.status).toBe("konsens");
    expect(gleich.line).toBe("✅ Dieselbe Antwort in 3 von 3 Läufen");
    const abweichend = vergleicheLaeufe([lauf, lauf, { signatur: "anders", einig: true, kurz: "Prüfer 2: 600 €" }]);
    expect(abweichend.status).toBe("keiner");
    expect(abweichend.line).toBe("❌ Kein Konsens — die drei Läufe stimmen nicht überein");
    expect(abweichend.detail).toContain("Lauf 3: Prüfer 2: 600 €");
  });

  it("behält den System-Prompt aus Schritt 1b vollständig", () => {
    expect(RAG_SYSTEM_PROMPT.startsWith("Du bist der Zitat-Dienst eines KSK-Prüfsystems.")).toBe(true);
    expect(RAG_SYSTEM_PROMPT).toContain("## DIE GOLDENE REGEL");
    expect(RAG_SYSTEM_PROMPT).toContain("Zu dieser Frage enthalten die vorliegenden Dokumente keine Aussage.");
    expect(RAG_SYSTEM_PROMPT).toContain("## ANTWORTFORMAT");
  });
});
