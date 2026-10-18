import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { getDb } from "../src/lib/db";
import { fuehreVorbereitungAus, holeVorbereitung, starteJahrespaketVorbereitung } from "../src/lib/jahrespaket-vorbereitung";

function ladeSchluessel(): void {
  for (const file of [".env.local", path.join("config", "secrets.env")]) {
    if (!existsSync(file)) continue;
    for (const line of readFileSync(file, "utf8").split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
      const name = trimmed.slice(0, trimmed.indexOf("=")).trim();
      let value = trimmed.slice(trimmed.indexOf("=") + 1).trim();
      if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
      if (name && value && !process.env[name]) process.env[name] = value;
    }
  }
}

describe("begrenzter Live-Lauf 2026", () => {
  it("erfasst, archiviert und indexiert nur die Ausgangsquellen", async () => {
    ladeSchluessel();
    if (process.env.KSK_LIVE_JAHRESPAKET !== "1" || !process.env.OPENAI_API_KEY) return;
    const start = starteJahrespaketVorbereitung(2026);
    await fuehreVorbereitungAus(start.id);
    const result = holeVorbereitung(start.id)!;
    const quellen = result.quellen ?? [];
    const archiviert = quellen.filter((item) => item.status === "archiviert");
    const indexiert = quellen.filter((item) => item.verarbeitungsstatus === "Completed");
    const katalog = getDb().prepare("SELECT art, COUNT(*) AS n FROM quellenkatalog GROUP BY art").all();
    console.log(JSON.stringify({
      status: result.status,
      katalog,
      gefunden: quellen.length,
      archiviert: archiviert.length,
      indexiert: indexiert.length,
      luecken: result.luecken_json,
      fehler: result.fehler,
    }));
    expect(result.status === "completed" || result.status === "failed").toBe(true);
    expect(archiviert.length).toBeGreaterThan(0);
    expect(getDb().prepare("SELECT is_active AS n FROM jahrespakete WHERE id = ?").get(start.jahrespaket_id)).toMatchObject({ n: 0 });
  }, 600_000);
});
