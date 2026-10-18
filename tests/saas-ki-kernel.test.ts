import { beforeAll, describe, expect, it } from "vitest";
import { stelleTestSaetzeFrei } from "./berechnungsfreigabe";
import { runSaasKiKernel } from "@/lib/saas-ki-kernel";

beforeAll(() => {
  stelleTestSaetzeFrei();
});

describe("SaaS-KI-Kernel", () => {
  it("rechnet 2025 mit dem freigegebenen Register und dem Regelcode", async () => {
    const ergebnis = await runSaasKiKernel({ auftrag: "berechnung", jahr: 2025, basisCents: 1_000_000 });
    expect(ergebnis.paket.version).toBe("v12");
    expect(ergebnis.paket.jahr).toBe(2025);
    expect(ergebnis.paket.registerSnapshot).toHaveLength(2);
    expect(ergebnis.konsensIstKeineFreigabe).toBe(true);
    expect(ergebnis.berechnung).toEqual({
      ausfuehrung: "regelcode",
      rateBps: 500,
      thresholdCents: 70_000,
      basisCents: 1_000_000,
      levyCents: 50_000,
    });
    expect(ergebnis.validierung.bestanden).toBe(true);
    expect(JSON.stringify(ergebnis)).not.toMatch(/python|sandbox/i);
  });

  it("meldet ein Jahr ohne freigegebenen Satz und rechnet nicht", async () => {
    const ergebnis = await runSaasKiKernel({ auftrag: "berechnung", jahr: 2031, basisCents: 1_000_000 });
    expect(ergebnis.berechnung?.levyCents).toBeNull();
    expect(ergebnis.berechnung?.ausfuehrung).toBe("regelcode");
    expect(ergebnis.validierung.bestanden).toBe(false);
    expect(ergebnis.validierung.meldungen.join(" ")).toMatch(/2031/);
    expect(ergebnis.validierung.meldungen.join(" ")).toMatch(/kein freigegebener Wert/);
    expect(ergebnis.validierung.meldungen.join(" ")).toMatch(/blockiert/);
  });
});
