import { readFileSync } from "node:fs";
import path from "node:path";
import { ABGABEGRENZE, ABGABESATZ, BEREICH_ABGABESATZ, BEREICH_GRENZE, type RegisterSnapshot } from "@/lib/register-kennungen";
import { berechnungswert, snapshotVon } from "@/lib/zahlen-register";
import type { RateTable, RateYear, RuleSet, ScenarioTable } from "./types";

export type Satzlage = {
  rate: RateYear | null;
  fehler: string | null;
  registerIds: string[];
  registerSnapshot: RegisterSnapshot[];
};

let cached: RuleSet | null = null;

export function loadRules(cwd = process.cwd()): RuleSet {
  if (cached && cwd === process.cwd()) return cached;
  const rules = readRuleSet(cwd);
  if (cwd === process.cwd()) cached = rules;
  return rules;
}

export function readRuleSet(cwd = process.cwd()): RuleSet {
  const dir = path.join(cwd, "rules");
  const rates = JSON.parse(readFileSync(path.join(dir, "saetze.json"), "utf8")) as RateTable;
  const scenarios = JSON.parse(readFileSync(path.join(dir, "szenarien.json"), "utf8")) as ScenarioTable;
  return { rates, scenarios };
}

export function satzlage(year: number): Satzlage {
  const von = `${year}-01-01`;
  const bis = `${year}-12-31`;
  const satz = berechnungswert({ kennung: ABGABESATZ, anwendungsbereich: BEREICH_ABGABESATZ, von, bis });
  const grenze = berechnungswert({ kennung: ABGABEGRENZE, anwendungsbereich: BEREICH_GRENZE, von, bis });
  const treffer = [satz, grenze].flatMap((item) => item.ok ? [item.eintrag] : []);
  const registerIds = treffer.map((item) => item.id);
  const registerSnapshot = treffer.map(snapshotVon);
  if (!satz.ok || !grenze.ok) {
    return {
      rate: null,
      fehler: [satz.ok ? null : satz.meldung, grenze.ok ? null : grenze.meldung].filter((item): item is string => Boolean(item)).join(" "),
      registerIds,
      registerSnapshot,
    };
  }
  if (satz.eintrag.wertBps == null || satz.eintrag.einheit !== "prozent" || grenze.eintrag.wertCent == null || grenze.eintrag.einheit !== "euro") {
    return {
      rate: null,
      fehler: `Für ${year} hat ein freigegebener Wert nicht die Einheit, die diese Berechnung braucht. Es wird kein Ersatzwert verwendet.`,
      registerIds,
      registerSnapshot,
    };
  }
  return {
    rate: {
      rateBps: satz.eintrag.wertBps,
      thresholdCents: grenze.eintrag.wertCent,
      rateSource: satz.eintrag.quelle,
      thresholdSource: grenze.eintrag.quelle,
    },
    fehler: null,
    registerIds,
    registerSnapshot,
  };
}

export function rateForYear(_rules: RuleSet, year: number): RateYear | null {
  return satzlage(year).rate;
}

export function missingRateMessage(year: number): string {
  return `Wir konnten die Abgabe für ${year} nicht prüfen, weil für dieses Jahr kein freigegebener Abgabesatz oder keine freigegebene Jahresgrenze vorliegt. Der Satz wird nicht geschätzt und es wird kein Wert aus einem anderen Jahr übernommen.`;
}
