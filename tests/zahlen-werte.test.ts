import { mkdtempSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { konsensVergleich } from "../src/lib/model-consensus";
import { RAG_SYSTEM_PROMPT, ragUserPrompt } from "../src/lib/rag-system-prompt";
import { grenzenAusText, nenntKeineZahlen, pruefeBestaetigt } from "../src/lib/mistral/abschnitte";
import { chunkZeile, dokumentbasisWarnung, type ChunkBeleg } from "../src/lib/mistral/chunks";
import {
  bezugsjahr,
  ergaenzeZeile,
  f05Hinweis,
  jahreswechselHinweis,
  klassifiziereProzent,
  kontextBlock,
  mitZeitabweichung,
  nurGueltigeBetraege,
  relevanteWerte,
  zeitHinweisEintraege,
  schreibeZahlenWerte,
  zahlenWertePfad,
  vorlageAusDatei,
  wertFuerJahr,
  zeitHinweise,
} from "../src/lib/mistral/zahlen-werte";

const liste = vorlageAusDatei();

describe("Werteliste", () => {
  it("liest für 2024, 2025, 2026 und 2027 den passenden Betrag", () => {
    const grenze = liste.wertegruppen[0];
    expect(wertFuerJahr(grenze, 2024)?.betrag).toBe(450);
    expect(wertFuerJahr(grenze, 2025)?.betrag).toBe(700);
    expect(wertFuerJahr(grenze, 2026)?.betrag).toBe(1000);
    expect(wertFuerJahr(grenze, 2027)?.betrag).toBe(1000);
  });

  it("baut für 2025 den Kontext mit 700 € und ohne die alte Grenze", () => {
    const text = kontextBlock(liste, 2025);
    expect(text).toContain("Bezugsjahr: 2025");
    expect(text).toContain("Abgabepflichtgrenze Veranstalter: 700 € (Quelle: Info_12)");
    expect(text).toContain("Bagatellgrenze je Zahlungsvorgang: 20 € (Quelle: KSVEntgV)");
    expect(text).toContain("Abgabesatz: 5,0 % (Quelle: Künstlersozialkasse, Abgabesatz)");
    expect(kontextBlock(liste, 2026)).toContain("Abgabepflichtgrenze Veranstalter: 1.000 €");
    expect(kontextBlock(liste, 2026)).toContain("Abgabesatz: 4,9 %");
    expect(text).not.toContain("450 €");
    const prompt = ragUserPrompt("Gilt 2025 die Grenze von 600 €?");
    expect(prompt.startsWith("## Nutzerfrage")).toBe(true);
    expect(prompt).toContain("Gilt 2025 die Grenze von 600 €?");
    expect(prompt).not.toContain("zahlen-werte.json");
    expect(prompt).not.toContain(text);
    expect(RAG_SYSTEM_PROMPT).toContain("Eine Systemliste ist keine Fundstelle und wird nicht abgeschrieben.");
    expect(RAG_SYSTEM_PROMPT).toContain("Der ZAHLEN-Abschnitt enthält nur Werte, die im Bezugsjahr GELTEN.");
    expect(RAG_SYSTEM_PROMPT).not.toContain("## KONTEXT-REGEL");
    expect(ragUserPrompt("Was gilt für Reisekosten bei Musikvereinen?", 2026)).toContain("Bezugsjahr: 2026");
  });

  it("nimmt das laufende Jahr, wenn die Frage keines nennt", () => {
    expect(bezugsjahr("Ab wann sind Musikvereine abgabepflichtig?", new Date(2026, 9, 7))).toEqual({
      jahr: 2026,
      angenommen: true,
    });
    expect(bezugsjahr("Gilt 2025 die Grenze von 600 €?")).toEqual({ jahr: 2025, angenommen: false });
  });

  it("meldet 450 € im Bezugsjahr 2025 als abgelaufen", () => {
    const hinweise = zeitHinweise([
      { value: 450, unit: "euro", jahr: null, label: "450 €" },
      { value: 700, unit: "euro", jahr: null, label: "700 €" },
    ], liste, 2025, "Prüfer 2 (medium)");
    expect(hinweise).toEqual(["⚠️ Zeit-Check: 450 € gilt nur bis 31.12.2024 (Prüfer 2)"]);
  });

  it("markiert historische Werte als Hinweis und blockt einen falsch zugeordneten gültigen Wert", () => {
    const historisch = mitZeitabweichung(
      { status: "konsens", line: "✅ Konsens 3/3", detail: null },
      zeitHinweisEintraege([{ value: 450, unit: "euro", jahr: null, label: "450 €" }], liste, 2025, "Prüfer 1 (small)"),
      false,
    );
    expect(historisch.status).toBe("hinweis");
    expect(historisch.line).toBe("⚠️ Gültige Werte konsistent — historische Werte im Zeit-Check");
    const mitGueltigen = mitZeitabweichung(
      { status: "konsens", line: "✅ Konsens 3/3", detail: null },
      zeitHinweisEintraege([{ value: 12, unit: "euro", jahr: null, label: "12 €" }], liste, 2026, "Prüfer 1 (small)"),
      true,
    );
    expect(mitGueltigen.status).toBe("konsens");
    expect(mitGueltigen.line).toBe("✅ Konsens 3/3");
    const verletzt = mitZeitabweichung(
      { status: "konsens", line: "✅ Konsens 3/3", detail: null },
      zeitHinweisEintraege([{ value: 700, unit: "euro", jahr: 2024, label: "700 €" }], liste, 2025, "Prüfer 1 (small)"),
    );
    expect(verletzt.status).toBe("abweichung");
    expect(verletzt.line).toBe("⚠️ Abweichung — Zeit-Check, kein Konsens 3/3");
  });

  it("lässt 12 € den Konsens der gültigen Reisekosten nicht zum Widerspruch werden", () => {
    const docs = ["Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf"];
    const zeilen = [
      { id: "P1", label: "Prüfer 1 (small)", keys: ["0.30", "12.00", "14.00", "28.00"], labels: ["0,30 €", "12 €", "14 €", "28 €"] },
      { id: "P2", label: "Prüfer 2 (medium)", keys: ["0.30", "12.00", "14.00", "28.00"], labels: ["0,30 €", "12 €", "14 €", "28 €"] },
      { id: "P3", label: "Prüfer 3 (large)", keys: ["0.30", "14.00", "28.00"], labels: ["0,30 €", "14 €", "28 €"] },
    ];
    const vergleich = konsensVergleich(zeilen.map((zeile) => {
      const gueltig = nurGueltigeBetraege(zeile.keys, zeile.labels, liste, 2026);
      return { id: zeile.id, label: zeile.label, ok: true, answer: "", documents: docs, amountKeys: gueltig.keys, amountLabels: gueltig.labels };
    }));
    expect(vergleich.status).toBe("konsens");
    const ergebnis = mitZeitabweichung(vergleich, zeitHinweisEintraege(
      [{ value: 12, unit: "euro", jahr: null, label: "12 €" }],
      liste,
      2026,
      "Prüfer 1 (small)",
    ));
    expect(ergebnis.status).toBe("konsens");
    expect(ergebnis.line).toBe("✅ Konsens 3/3");
    expect(zeitHinweisEintraege(
      [{ value: 12, unit: "euro", jahr: null, label: "12 €" }],
      liste,
      2026,
      "Prüfer 1 (small)",
    )[0]?.text).toContain("12 € gilt nur bis 31.12.2019");
  });

  it("hängt eine Zeile an, ohne die gültige Vorgängerzeile zu beenden", () => {
    const next = ergaenzeZeile(liste, {
      gruppe: "abgabepflichtgrenze_veranstalter",
      betrag: 1200,
      gueltig_ab: "2027-01-01",
      gueltig_bis: null,
    }, "2026-10-07");
    const werte = next.wertegruppen[0].werte;
    expect(werte.find((zeile) => zeile.betrag === 1000)?.gueltig_bis).toBeNull();
    expect(werte.find((zeile) => zeile.betrag === 1200)?.gueltig_bis).toBeNull();
    expect(liste.wertegruppen[0].werte.find((zeile) => zeile.betrag === 1000)?.gueltig_bis).toBeNull();
    const dir = mkdtempSync(path.join(tmpdir(), "ksk-werte-"));
    const file = path.join(dir, "zahlen-werte.json");
    schreibeZahlenWerte(next, file);
    expect(JSON.parse(readFileSync(file, "utf8")).wertegruppen[0].werte).toHaveLength(4);
    expect(existsSync(`${file}.tmp`)).toBe(false);
    expect(existsSync(`${file}.bak`)).toBe(false);
    expect(jahreswechselHinweis(new Date(2026, 9, 7))).toBe("⚠️ Für 2027 prüfen!");
    const datei = readFileSync(zahlenWertePfad(), "utf8");
    expect(() => schreibeZahlenWerte(next, zahlenWertePfad())).toThrow(/nicht überschrieben/);
    expect(readFileSync(zahlenWertePfad(), "utf8")).toBe(datei);
  });

  it("markiert 450 € für 2025 als vertauscht und stuft ein unbelegtes bestätigt herab", () => {
    const nennungen = grenzenAusText("450 € für 2025\nin 2025: 700 €\n450 € (in 2025: 700 €, ab 2026: 1.000 €)");
    expect(nennungen.find((item) => item.value === 450 && item.jahr === 2025)).toBeTruthy();
    expect(nennungen.find((item) => item.value === 700 && item.jahr === 2025)).toBeTruthy();
    expect(nennungen.find((item) => item.value === 1000 && item.jahr === 2026)).toBeTruthy();
    const hinweise = zeitHinweise(grenzenAusText("450 € für 2025"), liste, 2026, "Prüfer 1 (small)");
    expect(hinweise).toEqual(["⚠️ Zeit-Check: 450 € gilt nicht für 2025, sondern nur bis 31.12.2024 (Prüfer 1)"]);
    const bestaetigt = pruefeBestaetigt("4,9 % | bestätigt (Fundstelle: Info 12)\nEntgelte sind meldepflichtig | bestätigt", "Grenze 700 €", "Prüfer 3");
    expect(bestaetigt.text).toContain("4,9 % | nicht belegt");
    expect(bestaetigt.text).toContain("Entgelte sind meldepflichtig | Regel bestätigt, Zahl unbelegt");
    expect(bestaetigt.hinweise).toEqual(['⚠️ Ungültiges "bestätigt": 4,9 % (Prüfer 3)']);
    expect(pruefeBestaetigt("700 € | bestätigt", "in 2025: 700 €", "Prüfer 3").hinweise).toEqual([]);
    expect(klassifiziereProzent(4.9, "Gilt 4,9 %?", liste)).toBe("belegt");
    expect(klassifiziereProzent(3.5, "Der Satz ist 3,5 %.", liste)).toBe("nutzerangabe");
    expect(klassifiziereProzent(8, "Ab wann?", liste)).toBe("unbekannt");
  });

  it("nennt die Info-10-Werte zum Thema und stuft den Konsens nicht um", () => {
    expect(relevanteWerte("Was gilt für Reisekosten bei Musikvereinen?", liste, 2026)).toEqual(["0,30 €", "28 €", "14 €"]);
    expect(relevanteWerte("Was gilt für Reisekosten bei Musikvereinen?", liste, 2016)).toEqual(["0,30 €", "24 €", "12 €"]);
    expect(relevanteWerte("Ehrenamtspauschale 2026", liste, 2026)).toEqual(["960 €"]);
    const nachweis = liste.wertegruppen.find((gruppe) => gruppe.name === "bewirtung_nachweispflicht");
    expect(nachweis?.thema).toBe("bewirtung");
    expect(nachweis?.bedingung).toBe("ohne Einzelnachweis → zuzurechnen");
    const ermaessigung = liste.wertegruppen.find((gruppe) => gruppe.name === "ermaessigung_paragraph_50");
    expect(ermaessigung?.thema).toBe("ermäßigung");
    expect(wertFuerJahr(ermaessigung!, 1995)?.betrag).toBe(25);
    expect(wertFuerJahr(ermaessigung!, 2026)).toBeNull();
    const hinweis = f05Hinweis({
      nenntKeine: nenntKeineZahlen("ZAHLEN:\nkeine Zahlen belegt\nNUTZERANGABEN-PRÜFUNG:\n-\nFUNDSTELLEN:\n-\nLÜCKEN:\n-\nKERNAUSSAGEN:\n-"),
      frage: "Was gilt für Reisekosten bei Musikvereinen?",
      jahr: 2026,
      liste,
      prueferLabel: "Prüfer 3 (large)",
    });
    expect(hinweis).toBe("⚠️ Prüfer 3 nennt keine Zahlen — Dokument enthält laut Liste: 0,30 €, 28 €, 14 €. Lesefehler wahrscheinlich.");
    const konsens = { status: "konsens" as const, line: "✅ Konsens 3/3", detail: null };
    expect(mitZeitabweichung(konsens, [])).toEqual(konsens);
    const info = (seite: string): ChunkBeleg => ({ id: seite, dokument: "Info_10_Ausnahmen.pdf", seite, text: "0,30 €" });
    expect(chunkZeile([info("3"), info("5")])).toBe("Info_10, Seite 3 / Seite 5");
    expect(dokumentbasisWarnung([
      { label: "Prüfer 1 (small)", chunks: [info("3")] },
      { label: "Prüfer 2 (medium)", chunks: [info("3"), info("5")] },
    ])).toBe("⚠️ Uneinheitliche Dokumentbasis: Prüfer 1 erhielt 1 Chunks, Prüfer 2 erhielt 2 Chunks — Retrieval variiert, Konsens verzerrend.");
    expect(dokumentbasisWarnung([
      { label: "Prüfer 1 (small)", chunks: [info("3")] },
      { label: "Prüfer 2 (medium)", chunks: [info("3")] },
    ])).toBeNull();
  });
});
