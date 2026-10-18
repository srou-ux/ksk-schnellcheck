import { describe, expect, it } from "vitest";
import { RAG_SYSTEM_PROMPT } from "../src/lib/rag-system-prompt";
import { stellenBlock, type ChunkBeleg } from "../src/lib/mistral/chunks";
import { euroAmounts, geldVorhanden, pruefeAntwort, textstellenUmBetraege, textstellenUmBegriffe, zahlenAusFrage, zahlVorhanden } from "../src/lib/mistral/rag-pruefung";
import { alleThemenBetraege, vorlageAusDatei } from "../src/lib/mistral/zahlen-werte";

describe("Zahl-Check", () => {
  it("ignoriert Zahlen ohne Eurozeichen", () => {
    expect(euroAmounts("Die Grenze liegt bei 16 und bei 600 €.").map((item) => item.value)).toEqual([600]);
  });

  it("erkennt einen Betrag nur, wenn er in den Retrieval-Abschnitten steht", () => {
    const result = pruefeAntwort({
      answer: "Belegt sind 450 € und 1.000 €. In der Frage steht 600 €.",
      documentNames: ["Info_10_Ausnahmen.pdf"],
      citationsField: false,
      passages: ["Die Grenze beträgt 450 Euro und 1000 Euro."],
      citationLabels: [],
    });
    expect(result.zahlen.status).toBe("warnung");
    expect(result.zahlen.lines).toEqual(["⚠️ Zahl ohne Fundstelle: 600 €"]);
    expect(result.zahlen.checked).toBe(3);
  });

  it("überspringt den Zahl-Check ohne Citations und ohne Retrieval-Text", () => {
    const result = pruefeAntwort({
      answer: "600 €",
      documentNames: ["Info_10_Ausnahmen.pdf"],
      citationsField: false,
      passages: [],
      citationLabels: [],
    });
    expect(result.zahlen).toEqual({
      status: "uebersprungen",
      checked: 0,
      lines: ["Citations nicht verfügbar — Zahl-Check übersprungen"],
    });
  });

  it("meldet Library-Bezug über den Dokumentnamen", () => {
    const hit = pruefeAntwort({
      answer: "Siehe Info_10_Ausnahmen.pdf.",
      documentNames: ["Info_10_Ausnahmen.pdf", "KSVG.pdf"],
      citationsField: true,
      passages: ["keine Beträge"],
      citationLabels: [],
    });
    expect(hit.library.ok).toBe(true);
    expect(hit.library.documents).toEqual(["Info_10_Ausnahmen.pdf"]);
    const miss = pruefeAntwort({
      answer: "Zu dieser Frage enthalten die vorliegenden Dokumente keine Aussage.",
      documentNames: ["Info_10_Ausnahmen.pdf"],
      citationsField: true,
      passages: ["keine Beträge"],
      citationLabels: [],
    });
    expect(miss.library.ok).toBe(false);
    expect(miss.library.line).toBe("Antwort ohne Library-Bezug — Ergebnis ungültig (Testmodus)");
  });

  it("erkennt 0,30 € und 14 € auch bei Punkt als Dezimaltrenner", () => {
    expect(zahlVorhanden("0.30 je km und 14.00", 0.3)).toBe(true);
    expect(zahlVorhanden("0.30 je km und 14.00", 14)).toBe(true);
    expect(euroAmounts("0,30 € und 14 € und 14.00 €").map((item) => item.value)).toEqual([0.3, 14]);
    const result = pruefeAntwort({
      answer: "ZAHLEN:\n- 0,30 € | Info 10\n- 14 € | Info 10",
      zahlText: "0,30 €\n14 €",
      documentNames: ["Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf"],
      citationsField: true,
      passages: ["0.30 EUR je km, Bewirtung 14.00"],
      citationLabels: [],
    });
    expect(result.zahlen.status).toBe("bestanden");
    expect(result.zahlen.checked).toBe(2);
  });

  it("erkennt Info 10 ohne volle Überschrift und sperrt prompt-v12.md", () => {
    const result = pruefeAntwort({
      answer: "Siehe Info_10 mehrfach. Fundstelle prompt-v12.md",
      documentNames: ["Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf", "prompt-v12.md"],
      citationsField: true,
      passages: ["0,30 €"],
      citationLabels: [],
    });
    expect(result.library.ok).toBe(true);
    expect(result.library.documents).toEqual(["Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf"]);
    expect(result.interne).toBe("🔴 Ungültige Fundstelle: interne Datei");
    expect(RAG_SYSTEM_PROMPT).toContain("ZAHLEN enthält nur für die Frage relevante Zahlen. Belegte, aber nicht fragen-relevante Werte aus dem Material gehören NICHT hinein.");
  });

  it("zählt § 28 nicht als 28 € und schneidet nur die Stelle um den gesuchten Betrag aus", () => {
    expect(geldVorhanden("Nachweispflichten gemäß § 28 KSVG", 28)).toBe(false);
    expect(geldVorhanden("Bewirtung 28 Euro und 0,30 je km", 28)).toBe(true);
    expect(zahlVorhanden("0.30 je km und 14.00", 14)).toBe(true);
    const warnung = pruefeAntwort({
      answer: "ZAHLEN:\n28 €",
      zahlText: "28 €",
      documentNames: ["Info_10_Ausnahmen.pdf"],
      citationsField: true,
      passages: ["Nachweispflichten gemäß § 28 KSVG"],
      citationLabels: [],
    });
    expect(warnung.zahlen.status).toBe("warnung");
    expect(warnung.zahlen.lines).toEqual(["⚠️ Zahl ohne Fundstelle: 28 €"]);
    const text = `${"Vorbemerkung ".repeat(80)}960 € am Anfang. ${"Zwischentext ".repeat(80)}Kilometerpauschale 0,30 € je km.`;
    const stellen = textstellenUmBetraege(text, [0.3]);
    expect(stellen.join(" ")).toContain("0,30");
    expect(stellen.join(" ")).not.toContain("960");
  });

  it("zieht Zahlen und Schlüsselbegriffe aus der Frage und holt die Pauschalentabelle", () => {
    const zahlen = zahlenAusFrage("14,00 und 28,00 sowie 450, 960 und 4,9 % Grenze");
    expect(zahlen.betraege).toEqual(expect.arrayContaining([14, 28, 450, 960]));
    expect(zahlen.prozente).toEqual([4.9]);
    const thema = alleThemenBetraege("Was gilt für Reisekosten bei Musikvereinen?", vorlageAusDatei());
    expect(thema.map((item) => item.value)).toEqual(expect.arrayContaining([0.3, 12, 14, 24, 28]));
    const tabelle = "Fahrtkosten 0,30 Euro. Verpflegungsmehraufwand 2014 bis 2019: 24,00 Euro und 12,00 Euro. Ab 2020: 28,00 Euro und 14,00 Euro.";
    const stellen = [
      ...textstellenUmBetraege(tabelle, [12, 14, 24, 28]),
      ...textstellenUmBegriffe(tabelle, ["verpflegungsmehraufwand", "fahrtkosten"]),
    ];
    expect(stellen.join(" ")).toContain("12,00");
    expect(stellen.join(" ")).toContain("24,00");
    expect(stellen.join(" ")).toContain("14,00");
    expect(stellen.join(" ")).toContain("28,00");
  });

  it("stellt die wörtlichen Beträge vor die Dokumentstellen und ohne interne Kennung", () => {
    const chunk: ChunkBeleg = {
      id: "0854f98f-060b-41bd-a2b7-f80b416f25fc:suche",
      dokument: "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      seite: null,
      text: "PKW ab 01.01.2002 in Höhe von 0,30 € je Kilometer. Ab 2020: 28 Euro und 14 Euro.",
    };
    const block = stellenBlock([chunk]);
    expect(block).toContain("0,30 € in Info_10");
    expect(block).toContain("28 € in Info_10");
    expect(block).toContain("14 € in Info_10");
    expect(block).not.toContain("0854f98f");
    expect(RAG_SYSTEM_PROMPT).toContain("Nimm jeden");
    expect(RAG_SYSTEM_PROMPT).toContain("Betrag aus dieser Liste in ZAHLEN auf");
  });
});
