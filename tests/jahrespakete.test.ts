import { describe, expect, it } from "vitest";
import { createCase, getCase, getDb, legeJahrespaketEntwurfAn, listJahrespakete } from "../src/lib/db";

describe("Jahrespakete", () => {
  it("vergibt je Jahr eigenständige fortlaufende Versionen", () => {
    const erstes = legeJahrespaketEntwurfAn({ jahr: 2041, methodologyVersion: "v12", rulesStamp: "2040-10-01" });
    const zweites = legeJahrespaketEntwurfAn({ jahr: 2041, methodologyVersion: "v13", rulesStamp: "2040-11-15" });
    const anderesJahr = legeJahrespaketEntwurfAn({ jahr: 2042, methodologyVersion: "v13", rulesStamp: "2041-10-01" });

    expect([erstes.version, zweites.version, anderesJahr.version]).toEqual([1, 2, 1]);
    expect([erstes.status, zweites.status, anderesJahr.status]).toEqual(["entwurf", "entwurf", "entwurf"]);
    expect([erstes.is_active, zweites.is_active, anderesJahr.is_active]).toEqual([0, 0, 0]);
    expect(listJahrespakete()).toEqual(expect.arrayContaining([
      expect.objectContaining({ jahr: 2041, version: 1 }),
      expect.objectContaining({ jahr: 2041, version: 2 }),
      expect.objectContaining({ jahr: 2042, version: 1 }),
    ]));
  });

  it("weist ungültige Jahre und unvollständige technische Metadaten zurück", () => {
    expect(() => legeJahrespaketEntwurfAn({ jahr: 0, methodologyVersion: "v12", rulesStamp: "2026-10-05" })).toThrow(/Paketjahr/);
    expect(() => legeJahrespaketEntwurfAn({ jahr: 2043, methodologyVersion: "", rulesStamp: "2026-10-05" })).toThrow(/Methodikversion/);
  });

  it("verhindert doppelte Jahresversionen auch auf Datenbankebene", () => {
    const paket = legeJahrespaketEntwurfAn({ jahr: 2044, methodologyVersion: "v12", rulesStamp: "2043-10-01" });
    expect(() => getDb().prepare(`INSERT INTO jahrespakete (
        id, jahr, version, status, methodology_version, rules_stamp, is_active, created_at
      ) VALUES (?, ?, ?, 'entwurf', ?, ?, 0, ?)`).run(
      crypto.randomUUID(), paket.jahr, paket.version, "v12", "2043-10-01", new Date().toISOString(),
    )).toThrow();
  });

  it("erlaubt keine Aktivierung eines nicht freigegebenen Pakets", () => {
    const paket = legeJahrespaketEntwurfAn({ jahr: 2045, methodologyVersion: "v12", rulesStamp: "2044-10-01" });
    expect(() => getDb().prepare("UPDATE jahrespakete SET is_active = 1 WHERE id = ?").run(paket.id)).toThrow(/freigegeben/);
    expect(listJahrespakete().find((item) => item.id === paket.id)).toMatchObject({ status: "entwurf", is_active: 0 });
  });

  it("lässt bestehende Falldaten beim Anlegen von Paketversionen unverändert", () => {
    const fall = createCase({ title: "Bestehender Testfall", audience: "verein" });
    legeJahrespaketEntwurfAn({ jahr: 2046, methodologyVersion: "v12", rulesStamp: "2045-10-01" });
    expect(getCase(fall.id)).toEqual(fall);
  });
});
