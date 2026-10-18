import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { createCase, getDb, getReportByCase, insertReport, korrigiereImportfreigaben } from "../src/lib/db";
import { confirmedFromParsed } from "../src/lib/domain/reconcile";
import { evaluateInvoice } from "../src/lib/domain/evaluate";
import { levyCents } from "../src/lib/domain/money";
import { readRuleSet, satzlage } from "../src/lib/domain/rules";
import type { ParsedReading } from "../src/lib/domain/types";
import { ladeZahlenWerte, zahlenWertePfad } from "../src/lib/mistral/zahlen-werte";
import { ABGABEGRENZE, ABGABESATZ, BEREICH_ABGABESATZ, BEREICH_GRENZE } from "../src/lib/register-kennungen";
import {
  bearbeiteEntwurf,
  berechnungswert,
  gebeFrei,
  importiereVorlage,
  ladeEintraege,
  legeEntwurfAn,
  parseWert,
  revisionenZu,
  wertAm,
} from "../src/lib/zahlen-register";

const rules = readRuleSet();

function lesung(year: number): ParsedReading {
  return {
    readable: true,
    year,
    payerName: "Verlag",
    payerRole: "typischer_verwerter",
    payeeName: "Ada",
    payeeKind: "natuerliche_person",
    annualSumConfirmed: true,
    statedNetTotalCents: 100000,
    positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 100000 }],
  };
}

describe("Zahlenregister", () => {
  it("lässt den Import ohne Freigabenachweis einen Entwurf und die Vorlage unangetastet", () => {
    const datei = readFileSync(zahlenWertePfad(), "utf8");
    importiereVorlage();
    expect(readFileSync(zahlenWertePfad(), "utf8")).toBe(datei);
    const importe = ladeEintraege().filter((eintrag) => eintrag.herkunft === "import");
    expect(importe.length).toBeGreaterThan(0);
    expect(importe.every((eintrag) => eintrag.freigabe === "entwurf" && eintrag.freigabeNachweis === null)).toBe(true);
    const satz = importe.find((eintrag) => eintrag.gruppe === "abgabesatz" && eintrag.wertExakt === "4.9");
    const kilometer = importe.find((eintrag) => eintrag.gruppe === "kilometerpauschale" && eintrag.wertExakt === "0.30");
    expect(satz?.wertBps).toBe(490);
    expect(kilometer?.wertCent).toBe(30);
    expect(ladeZahlenWerte().wertegruppen.every((gruppe) => gruppe.werte.every((zeile) => zeile.freigabe === "freigegeben"))).toBe(true);
  });

  it("korrigiert eine automatische Freigabe ohne Nachweis und lässt den Fallbericht stehen", () => {
    const fall = createCase({ title: "Historischer Bericht", audience: "verein" });
    insertReport({
      runId: crypto.randomUUID(),
      caseId: fall.id,
      methodologyVersion: "v12",
      payload: { marker: "historisch", totalLevyCents: 111 },
    });
    const vorher = getReportByCase(fall.id)?.payload_json;
    const id = crypto.randomUUID();
    getDb().prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at, herkunft
      ) VALUES (?, 'alt_import', 1, 10, 'euro', '2020-01-01', NULL, 'alte Quelle', 'freigegeben', 'Alt', NULL, '[]', NULL, ?, 'import')`).run(id, new Date().toISOString());
    expect(korrigiereImportfreigaben()).toBeGreaterThan(0);
    const zeile = ladeEintraege().find((eintrag) => eintrag.id === id);
    expect(zeile?.freigabe).toBe("entwurf");
    expect(revisionenZu(id).some((revision) => revision.grund.includes("Import ohne Freigabenachweis"))).toBe(true);
    expect(getReportByCase(fall.id)?.payload_json).toBe(vorher);
  });

  it("lässt einen neuen Entwurf den gültigen Vorgänger unverändert", () => {
    const vorgaenger = gebeFrei({
      gruppe: "test_entwurf",
      beschreibung: "Testentwurf",
      betrag: "80",
      einheit: "euro",
      gueltigAb: "2024-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Entwurf",
    });
    const entwurf = legeEntwurfAn({
      gruppe: "test_entwurf",
      beschreibung: "Testentwurf",
      betrag: "90",
      einheit: "euro",
      gueltigAb: "2028-01-01",
      gueltigBis: null,
    });
    bearbeiteEntwurf(entwurf.id, {
      gruppe: "test_entwurf",
      beschreibung: "Testentwurf",
      betrag: "91",
      einheit: "euro",
      gueltigAb: "2028-06-01",
      gueltigBis: null,
    });
    const danach = ladeEintraege().find((eintrag) => eintrag.id === vorgaenger.id);
    expect(danach?.gueltigBis).toBeNull();
    expect(danach?.wertCent).toBe(8000);
    expect(danach?.freigabe).toBe("freigegeben");
    expect(ladeEintraege().find((eintrag) => eintrag.id === entwurf.id)?.freigabe).toBe("entwurf");
    const weiter = wertAm("test_entwurf", "Testbereich Entwurf", "2028-06-01");
    expect(weiter.ok && weiter.eintrag.id).toBe(vorgaenger.id);
    expect(weiter.ok && weiter.eintrag.wertCent).toBe(8000);
  });

  it("gibt frei und löst den Vorgänger in einer Transaktion ab", () => {
    const alt = gebeFrei({
      gruppe: "test_abloesung",
      beschreibung: "Ablösung",
      betrag: "100",
      einheit: "euro",
      gueltigAb: "2026-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "§ 1",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Ablösung",
    });
    const neu = gebeFrei({
      gruppe: "test_abloesung",
      beschreibung: "Ablösung",
      betrag: "120",
      einheit: "euro",
      gueltigAb: "2027-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "§ 1 neu",
      dokumentstand: "2026-10-07",
      anwendungsbereich: "Testbereich Ablösung",
    });
    expect(ladeEintraege().find((eintrag) => eintrag.id === alt.id)?.gueltigBis).toBe("2026-12-31");
    expect(neu.freigabe).toBe("freigegeben");
    expect(neu.wertCent).toBe(12000);
    expect(revisionenZu(alt.id)[0]?.zustand.gueltig_bis).toBeNull();
    expect(wertAm("test_abloesung", "Testbereich Ablösung", "2026-12-31").ok).toBe(true);
    expect(wertAm("test_abloesung", "Testbereich Ablösung", "2027-01-01").ok && (wertAm("test_abloesung", "Testbereich Ablösung", "2027-01-01") as { eintrag: { id: string } }).eintrag.id).toBe(neu.id);
  });

  it("nimmt eine gescheiterte Freigabe vollständig zurück", () => {
    const alt = gebeFrei({
      gruppe: "test_abbruch",
      beschreibung: "Abbruch",
      betrag: "50",
      einheit: "euro",
      gueltigAb: "2025-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Abbruch",
    });
    expect(() => gebeFrei({
      gruppe: "test_abbruch",
      beschreibung: "Abbruch",
      betrag: "60",
      einheit: "euro",
      gueltigAb: "2026-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Abbruch",
      abbruchNachSchreiben: true,
    })).toThrow(/Testabbruch/);
    const danach = ladeEintraege().filter((eintrag) => eintrag.gruppe === "test_abbruch" && eintrag.freigabe === "freigegeben");
    expect(danach).toHaveLength(1);
    expect(danach[0]?.id).toBe(alt.id);
    expect(danach[0]?.gueltigBis).toBeNull();
    expect(revisionenZu(alt.id)).toHaveLength(0);
  });

  it("blockiert fehlende Werte, Überschneidungen und unbekannte Kennungen", () => {
    expect(() => gebeFrei({
      gruppe: "test_unvollstaendig",
      beschreibung: "Unvollständig",
      betrag: "10",
      einheit: "euro",
      gueltigAb: "2025-01-01",
      gueltigBis: null,
      quelle: "Quelle",
      anwendungsbereich: "Bereich",
    })).toThrow(/Vollständigkeit/);
    gebeFrei({
      gruppe: "test_ueberlappung",
      beschreibung: "Überlappung",
      betrag: "10",
      einheit: "euro",
      gueltigAb: "2020-01-01",
      gueltigBis: "2024-12-31",
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Überlappung",
    });
    expect(() => gebeFrei({
      gruppe: "test_ueberlappung",
      beschreibung: "Überlappung",
      betrag: "12",
      einheit: "euro",
      gueltigAb: "2024-06-01",
      gueltigBis: null,
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Überlappung",
    })).toThrow(/überschneiden/);
    expect(ladeEintraege().find((eintrag) => eintrag.gruppe === "test_ueberlappung")?.gueltigBis).toBe("2024-12-31");
    const leer = satzlage(2031);
    expect(leer.rate).toBeNull();
    expect(leer.fehler).toMatch(/2031/);
    expect(leer.fehler).toMatch(/kein freigegebener Wert/);
    expect(leer.fehler).toMatch(/anderen Jahr/);
    legeEntwurfAn({
      gruppe: ABGABESATZ,
      beschreibung: "Entwurf 2031",
      betrag: "5",
      einheit: "prozent",
      gueltigAb: "2031-01-01",
      gueltigBis: "2031-12-31",
      anwendungsbereich: BEREICH_ABGABESATZ,
    });
    expect(satzlage(2031).rate).toBeNull();
    expect(berechnungswert({
      kennung: "sonderpauschale",
      anwendungsbereich: "irgendwo",
      von: "2030-01-01",
      bis: "2030-12-31",
    })).toMatchObject({ ok: false, grund: "unbekannt" });
  });

  it("rechnet an den Zeitraumgrenzen exakt und übernimmt keine fremde Kennung", () => {
    expect(parseWert("euro", "0,30")).toEqual({ wertExakt: "0.30", wertCent: 30, wertBps: null });
    expect(parseWert("prozent", "4,9")).toEqual({ wertExakt: "4.9", wertCent: null, wertBps: 490 });
    expect(() => parseWert("euro", "10,005")).toThrow(/Nachkommastellen/);
    expect(levyCents(1_000_000, 490)).toBe(49_000);
    gebeFrei({
      gruppe: "test_rand",
      beschreibung: "Rand",
      betrag: "20",
      einheit: "euro",
      gueltigAb: "2025-01-01",
      gueltigBis: "2025-12-31",
      quelle: "Quelle",
      fundstelle: "Fundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Testbereich Rand",
    });
    expect(wertAm("test_rand", "Testbereich Rand", "2025-01-01").ok).toBe(true);
    expect(wertAm("test_rand", "Testbereich Rand", "2025-12-31").ok).toBe(true);
    expect(wertAm("test_rand", "Testbereich Rand", "2024-12-31").ok).toBe(false);
    expect(wertAm("test_rand", "Testbereich Rand", "2026-01-01").ok).toBe(false);
    gebeFrei({
      gruppe: ABGABESATZ,
      beschreibung: "Satz 2030",
      betrag: "1,23",
      einheit: "prozent",
      gueltigAb: "2030-01-01",
      gueltigBis: "2030-12-31",
      quelle: "Testquelle",
      fundstelle: "Testfundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: BEREICH_ABGABESATZ,
    });
    gebeFrei({
      gruppe: ABGABEGRENZE,
      beschreibung: "Grenze 2030",
      betrag: "123,45",
      einheit: "euro",
      gueltigAb: "2030-01-01",
      gueltigBis: "2030-12-31",
      quelle: "Testquelle",
      fundstelle: "Testfundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: BEREICH_GRENZE,
    });
    gebeFrei({
      gruppe: "sonderpauschale",
      beschreibung: "Keine Berechnungsregel",
      betrag: "999",
      einheit: "euro",
      gueltigAb: "2030-01-01",
      gueltigBis: "2030-12-31",
      quelle: "Testquelle",
      fundstelle: "Testfundstelle",
      dokumentstand: "2026-10-05",
      anwendungsbereich: "Sonderfall",
    });
    const lage = satzlage(2030);
    expect(lage.rate).toEqual({
      rateBps: 123,
      thresholdCents: 12345,
      rateSource: "Testquelle",
      thresholdSource: "Testquelle",
    });
    expect(rules.rates.years["2030"]).toBeUndefined();
    const evaluation = evaluateInvoice(confirmedFromParsed(lesung(2030)), rules);
    expect(evaluation.rateBps).toBe(123);
    expect(evaluation.thresholdCents).toBe(12345);
    expect(evaluation.registerIds).toHaveLength(2);
    expect(evaluation.configError).toBeNull();
  });
});
