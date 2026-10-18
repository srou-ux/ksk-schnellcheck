import { describe, expect, it } from "vitest";
import { dokumentZahlen, ergaenzeZahlen, fehlendeBetragszeilen, grenzenAusAntwort, parseAbschnitte, zahlenAusNachfrage } from "../src/lib/mistral/abschnitte";
import { konsensVergleich } from "../src/lib/model-consensus";
import { RAG_SYSTEM_PROMPT } from "../src/lib/rag-system-prompt";
import { nurGueltigeBetraege, vorlageAusDatei } from "../src/lib/mistral/zahlen-werte";

const answer = `KERNAUSSAGEN:
- Mindestens vier Veranstaltungen.

ZAHLEN:
- 700 € | Info 12
- 1.500 € | erfunden

NUTZERANGABEN-PRÜFUNG:
- 1.500 € | abweichend (Dokument sagt: 1.000 €, Fundstelle: Info 12)
- 400 € | nicht belegt
- 250 € | nicht belegt
- 4,9 % | nicht belegt

FUNDSTELLEN:
- Info 12, Abschnitt Nicht kommerzielle Veranstalter

LÜCKEN:
- nicht belegt`;

describe("Abschnitte", () => {
  it("toleriert fette Markdown-Überschriften", () => {
    const sections = parseAbschnitte("**ZAHLEN:**\n- 700 € | Info 12\n**NUTZERANGABEN-PRÜFUNG:**\n- 600 € | nicht belegt\n**FUNDSTELLEN:**\n- Info 12\n**LÜCKEN:**\n- nicht belegt\n**KERNAUSSAGEN:**\n- Vier Veranstaltungen.");
    expect(sections.vollstaendig).toBe(true);
    expect(sections.zahlen).toContain("700 €");
  });

  it("zerlegt die fünf Überschriften", () => {
    const sections = parseAbschnitte(answer);
    expect(sections.vollstaendig).toBe(true);
    expect(sections.zahlen).toContain("700 €");
    expect(sections.nutzerangaben).toContain("400 €");
    expect(sections.fundstellen).toContain("Info 12");
  });

  it("lässt Nutzer-Zahlen aus dem Konsens und verwirft unbelegte Zahlen im ZAHLEN-Abschnitt", () => {
    const corpus = "450 € (in 2025: 700 €, ab 2026: 1.000 €)";
    const dok = dokumentZahlen({
      answer,
      corpus,
      documentNames: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      prueferLabel: "Prüfer 3 (large)",
    });
    expect(dok.labels).toEqual(["700 €"]);
    expect(dok.keys).not.toContain("1500.00");
    expect(dok.hinweise.some((line) => line.includes("1.500 €") && line.includes("Prüfer 3"))).toBe(true);
    expect(dok.documents).toEqual(["Info_12_Abgabepflicht_von_Musikvereinen.pdf"]);
  });

  it("nutzt bei fehlender ZAHLEN-Überschrift die Rückfall-Extraktion", () => {
    const dok = dokumentZahlen({
      answer: "Die Grenze liegt bei 1.000 € laut Info 12.",
      corpus: "ab 2026: 1.000 €",
      documentNames: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      prueferLabel: "Prüfer 1 (small)",
    });
    expect(dok.hinweise[0]).toBe("⚠️ Antwortformat von Prüfer 1 abweichend — Rückfall-Extraktion verwendet");
    expect(dok.labels).toEqual(["1.000 €"]);
  });

  it("vergleicht im Konsens nur die belegten Dokument-Zahlen", () => {
    const row = {
      ok: true,
      answer: "Nutzer nannte 600 €",
      documents: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      amountKeys: ["700.00", "1000.00"],
      amountLabels: ["700 €", "1.000 €"],
    };
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ...row },
      { id: "P2", label: "Prüfer 2 (medium)", ...row },
      { id: "P3", label: "Prüfer 3 (large)", ...row },
    ]);
    expect(result.line).toBe("✅ Konsens 3/3");
  });

  it("zeitprüft nur den ZAHLEN-Abschnitt und markiert unbekannte Beträge rot", () => {
    const text = `ZAHLEN:\n- 450 € | Info 12\nNUTZERANGABEN-PRÜFUNG:\n- 600 € | abweichend\nFUNDSTELLEN:\n- Info 12\nLÜCKEN:\n- nicht belegt\nKERNAUSSAGEN:\n- Grenze.`;
    expect(grenzenAusAntwort(text).map((item) => item.value)).toEqual([450]);
    const dok = dokumentZahlen({
      answer: `ZAHLEN:\n- 77 € | KSVG\nNUTZERANGABEN-PRÜFUNG:\n- keine\nFUNDSTELLEN:\n- KSVG\nLÜCKEN:\n- keine\nKERNAUSSAGEN:\n- Satz.`,
      corpus: "Die Grenze beträgt 450 Euro.",
      documentNames: ["KSVG.pdf"],
      prueferLabel: "Prüfer 2 (medium)",
      liste: vorlageAusDatei(),
    });
    expect(dok.hinweise).toContain("🔴 Unbekannter Wert: 77 € (Prüfer 2)");
    expect(dok.keys).not.toContain("77.00");
    const gueltig = nurGueltigeBetraege(["450.00", "77.00", "12.00"], ["450 €", "77 €", "12 €"], vorlageAusDatei(), 2024);
    expect(gueltig.keys).toEqual(["450.00"]);
    const konsens = konsensVergleich(["P1", "P2", "P3"].map((id, index) => ({
      id,
      label: `Prüfer ${index + 1}`,
      ok: true,
      answer: "",
      documents: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      amountKeys: gueltig.keys,
      amountLabels: gueltig.labels,
    })));
    expect(konsens.line).toBe("✅ Konsens 3/3");
  });

  it("übernimmt aus der Nachfrage nur Beträge, die in der Liste stehen", () => {
    const erste = `KERNAUSSAGEN:\n- Grenze.\n\nZAHLEN:\nIn den vorliegenden Dokumenten nicht belegt\n\nNUTZERANGABEN-PRÜFUNG:\n- nicht belegt\n\nFUNDSTELLEN:\n- Info_12\n\nLÜCKEN:\n- keine Aussage`;
    const liste = ["0,30 € in Info_10", "1.000 € in Info_12", "28 € in Info_10"];
    const fehlend = fehlendeBetragszeilen(erste, liste, [0.3, 28]);
    expect(fehlend).toEqual(["0,30 € in Info_10", "28 € in Info_10"]);
    const zusatz = zahlenAusNachfrage("ZAHLEN:\n- 0,30 € | Info_10\n- 28 € | Info_10\n- 999 € | Info_10", fehlend);
    expect(zusatz).toBe("- 0,30 € | Info_10\n- 28 € | Info_10");
    const text = ergaenzeZahlen(erste, zusatz ?? "");
    expect(parseAbschnitte(text).zahlen).toContain("0,30 €");
    expect(parseAbschnitte(text).zahlen).not.toContain("nicht belegt");
    expect(parseAbschnitte(text).fundstellen).toContain("Info_10");
  });

  it("bleibt ein Auskunftsdienst und rechnet keine Sachverhalte aus", () => {
    expect(RAG_SYSTEM_PROMPT).toContain("Du rechnest nicht und entscheidest keinen Sachverhalt.");
    expect(RAG_SYSTEM_PROMPT).not.toContain("ANWENDUNG");
    expect(RAG_SYSTEM_PROMPT).not.toContain("Rechnungen sind auszuführen");
  });
});
