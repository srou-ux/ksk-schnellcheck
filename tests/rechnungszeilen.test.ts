import { describe, expect, it } from "vitest";
import { zeilenAusRechnungstext } from "../src/lib/domain/rechnungszeilen";

const TEXT = `
01 · Kommunikationspaket
1 Paket
2.400,00 EUR
2.400,00 EUR
03 · Regiekoordination
2 Tage
680,00 EUR 1.360,00 EUR
Nettosumme: 3.760,00 EUR
`;

describe("Zeilen aus dem Rechnungstext", () => {
  it("nimmt den letzten Nettobetrag je Position, wenn die Summe die Nettosumme trifft", () => {
    const zeilen = zeilenAusRechnungstext(TEXT);
    expect(zeilen?.statedNetCents).toBe(376000);
    expect(zeilen?.positions.map((line) => line.netCents)).toEqual([240000, 136000]);
  });

  it("verwirft die Zeilen, wenn die Summe nicht zur Nettosumme passt", () => {
    expect(zeilenAusRechnungstext(TEXT.replace("3.760,00", "1,00"))).toBeNull();
  });

  it("nimmt den Betrag auf der Positionszeile und lässt Beträge im Beschreibungstext stehen", () => {
    const text = `
01 Künstlerischer Unterricht K-15 1.450,00 EUR
Vier Kurstage. Bahn 10,00 EUR steht nur im Text.
07 Reise zum Kurs K-28 220,00 EUR
Bahn 96 EUR; Hotel 124,00 EUR.
10 Preisnachlass zu Pos. 01 -100,00 EUR
Summe der Positionen netto 1.570,00 EUR
`;
    const zeilen = zeilenAusRechnungstext(text);
    expect(zeilen?.positions.map((line) => line.netCents)).toEqual([145000, 22000, -10000]);
    expect(zeilen?.statedNetCents).toBe(157000);
  });
});
