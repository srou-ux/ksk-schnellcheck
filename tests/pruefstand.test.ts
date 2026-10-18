import { describe, expect, it } from "vitest";
import {
  abgabeEuro,
  jahresbild,
  naechsterStatus,
  vorschlagPositionen,
  type Dokument,
} from "../src/lib/pruefstand";

function dokument(name: string): Dokument {
  return { id: "d1", name, zeit: "2026-10-18T00:00:00.000Z", positionen: vorschlagPositionen("d1", name) };
}

describe("Prüfstand Anzeige", () => {
  it("bleibt offen, solange eine Position offen ist", () => {
    const bild = jahresbild([dokument("verein.pdf")]);
    expect(bild.stufe).toBe("offen");
    expect(bild.summe).toBe(550);
    expect(bild.titel).toBe("Offen");
  });

  it("wird grün, wenn nichts offen oder gesperrt ist und die Summe unter der Grenze liegt", () => {
    const basis = dokument("verein.pdf");
    basis.positionen = basis.positionen.map((position) =>
      position.status === "OFFEN" ? { ...position, status: "AUSGENOMMEN" } : position,
    );
    expect(jahresbild([basis])).toMatchObject({ stufe: "ok", titel: "Nicht abgabepflichtig", summe: 550 });
  });

  it("sperrt bei Summenfehler", () => {
    expect(jahresbild([dokument("Summenfehler.xlsx")]).stufe).toBe("sperre");
  });

  it("übernehmen zählt, verwerfen nimmt aus, Auskunft lässt offen", () => {
    expect(naechsterStatus("uebernehmen", "OFFEN")).toBe("ZAEHLT");
    expect(naechsterStatus("verwerfen", "OFFEN")).toBe("AUSGENOMMEN");
    expect(naechsterStatus("ksk-auskunft", "OFFEN")).toBe("OFFEN");
  });

  it("beziffert die Abgabe auf Cent", () => {
    expect(abgabeEuro(200)).toBe(9.8);
  });
});
