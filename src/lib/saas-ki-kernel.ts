import { appConfig } from "@/lib/config";
import { activeLibrary, addArtifact, getReportByCase, getRun } from "@/lib/db";
import { levyCents } from "@/lib/domain/money";
import { readRuleSet, satzlage } from "@/lib/domain/rules";
import { METHODOLOGY_VERSION } from "@/lib/domain/types";
import type { LlmClient } from "@/lib/llm/types";
import { bezugsjahr } from "@/lib/mistral/zahlen-werte";
import { executeRun } from "@/lib/pipeline/run";
import type { RegisterSnapshot } from "@/lib/register-kennungen";
import { pruefeRagFrage, type RagAntwort } from "@/lib/rag-analysis";
import { client, findLibrary, LIBRARY_NAME } from "@/lib/rag-retrieval";

export type JahresPaket = {
  version: string;
  regelnStand: string;
  jahr: number | null;
  libraryId: string | null;
  libraryVersion: string | null;
  registerIds: string[];
  registerSnapshot: RegisterSnapshot[];
};

export type KernelAuftrag =
  | { auftrag: "rag"; frage: string; jahr?: number }
  | { auftrag: "fall"; runId: string; client?: LlmClient }
  | { auftrag: "berechnung"; jahr: number; basisCents: number };

export type KernelBerechnung = {
  ausfuehrung: "regelcode";
  rateBps: number | null;
  thresholdCents: number | null;
  basisCents: number | null;
  levyCents: number | null;
};

export type KernelErgebnis = {
  auftrag: KernelAuftrag["auftrag"];
  paket: JahresPaket;
  schritte: string[];
  hinweise: string[];
  widersprueche: string[];
  konsensIstKeineFreigabe: true;
  berechnung: KernelBerechnung | null;
  validierung: { bestanden: boolean; meldungen: string[] };
  rag?: RagAntwort;
  fall?: { runId: string; status: string | null; report: unknown };
};

const SCHRITTE = [
  "Sachverhalt erfassen",
  "Jahrespaket festlegen",
  "Quellen abrufen",
  "KI-Analyse",
  "Regel- und Zahlenprüfung",
  "Berechnung",
  "Validierung",
  "strukturiertes Ergebnis",
];

const KEINE_FREIGABE = "Modellkonsens ist keine fachliche Freigabe.";

function legePaket(input: { jahr: number | null; libraryId: string | null; libraryVersion: string | null }): { paket: JahresPaket; hinweise: string[] } {
  const rules = readRuleSet();
  const lage = input.jahr === null ? null : satzlage(input.jahr);
  const hinweise = lage && !lage.rate && lage.fehler ? [lage.fehler] : [];
  return {
    paket: {
      version: appConfig().methodologyVersion || METHODOLOGY_VERSION,
      regelnStand: rules.rates.stamp,
      jahr: input.jahr,
      libraryId: input.libraryId,
      libraryVersion: input.libraryVersion,
      registerIds: lage?.registerIds ?? [],
      registerSnapshot: lage?.registerSnapshot ?? [],
    },
    hinweise,
  };
}

function ergebnis(input: Omit<KernelErgebnis, "schritte" | "konsensIstKeineFreigabe">): KernelErgebnis {
  return { ...input, schritte: SCHRITTE, konsensIstKeineFreigabe: true };
}

async function ragAuftrag(frage: string, jahr?: number): Promise<KernelErgebnis> {
  const trimmed = frage.trim();
  if (!trimmed) throw new Error("Die Frage fehlt.");
  const bezug = typeof jahr === "number" ? { jahr, angenommen: false } : bezugsjahr(trimmed);
  const library = await findLibrary(client());
  if (!library) throw new Error(`Die Library ${LIBRARY_NAME} gibt es nicht. Lege sie zuerst an.`);
  const { paket, hinweise } = legePaket({ jahr: bezug.jahr, libraryId: library.id, libraryVersion: library.name });
  const antwort = await pruefeRagFrage(trimmed, library.id);
  const widersprueche = [antwort.konsens.status === "abweichung" || antwort.konsens.status === "keiner" ? antwort.konsens.line : null, antwort.basis]
    .filter((item): item is string => Boolean(item));
  const alleHinweise = [...hinweise, ...antwort.listeHinweise, "Für diese Anfrage wird nicht gerechnet.", KEINE_FREIGABE];
  return ergebnis({
    auftrag: "rag",
    paket,
    hinweise: alleHinweise,
    widersprueche,
    berechnung: null,
    validierung: { bestanden: widersprueche.length === 0 && hinweise.length === 0, meldungen: [...alleHinweise, ...widersprueche] },
    rag: antwort,
  });
}

async function fallAuftrag(runId: string, llm?: LlmClient): Promise<KernelErgebnis> {
  const run = getRun(runId);
  if (!run) throw new Error("Diesen Lauf gibt es nicht.");
  const library = activeLibrary();
  const { paket, hinweise } = legePaket({
    jahr: null,
    libraryId: run.library_id ?? library?.mistral_library_id ?? null,
    libraryVersion: run.library_version ?? library?.version_label ?? null,
  });
  addArtifact(runId, "paket", paket, true, false);
  await executeRun(runId, llm);
  const danach = getRun(runId);
  const reportRow = getReportByCase(run.case_id);
  const report = reportRow ? JSON.parse(reportRow.payload_json) as {
    year?: number | null;
    configError?: string | null;
    rateBps?: number | null;
    thresholdCents?: number | null;
    totalBasisCents?: number | null;
    totalLevyCents?: number | null;
    registerIds?: string[];
    registerSnapshot?: RegisterSnapshot[];
  } : null;
  const widersprueche = danach && (danach.status === "examiner_stop" || danach.status === "gate_failed")
    ? [danach.error_layperson ?? "Die Prüfung ist an einem Widerspruch oder einem Tor stehen geblieben."]
    : [];
  if (report?.configError) hinweise.push(report.configError);
  const paketMitJahr: JahresPaket = report
    ? {
      ...paket,
      jahr: report.year ?? paket.jahr,
      registerIds: report.registerIds ?? paket.registerIds,
      registerSnapshot: report.registerSnapshot ?? paket.registerSnapshot,
    }
    : paket;
  const alleHinweise = [...hinweise, KEINE_FREIGABE];
  const berechnung: KernelBerechnung | null = report
    ? {
      ausfuehrung: "regelcode",
      rateBps: report.rateBps ?? null,
      thresholdCents: report.thresholdCents ?? null,
      basisCents: report.totalBasisCents ?? null,
      levyCents: report.totalLevyCents ?? null,
    }
    : null;
  return ergebnis({
    auftrag: "fall",
    paket: paketMitJahr,
    hinweise: alleHinweise,
    widersprueche,
    berechnung,
    validierung: { bestanden: widersprueche.length === 0 && berechnung?.levyCents != null, meldungen: [...alleHinweise, ...widersprueche] },
    fall: { runId, status: danach?.status ?? null, report },
  });
}

function berechnungsAuftrag(jahr: number, basisCents: number): KernelErgebnis {
  if (!Number.isSafeInteger(jahr) || jahr < 1900 || jahr > 2200) throw new Error("Das Jahr ist ungültig.");
  if (!Number.isSafeInteger(basisCents) || basisCents < 0) throw new Error("Die Bemessungsgrundlage muss eine ganze Centzahl ab 0 sein.");
  const { paket, hinweise } = legePaket({ jahr, libraryId: null, libraryVersion: null });
  const lage = satzlage(jahr);
  if (!lage.rate) {
    const alleHinweise = [...hinweise, "Es wird kein Ersatzwert und keine andere Jahreszahl verwendet."];
    return ergebnis({
      auftrag: "berechnung",
      paket,
      hinweise: alleHinweise,
      widersprueche: [],
      berechnung: { ausfuehrung: "regelcode", rateBps: null, thresholdCents: null, basisCents, levyCents: null },
      validierung: { bestanden: false, meldungen: alleHinweise },
    });
  }
  const levy = levyCents(basisCents, lage.rate.rateBps);
  return ergebnis({
    auftrag: "berechnung",
    paket,
    hinweise: [KEINE_FREIGABE],
    widersprueche: [],
    berechnung: {
      ausfuehrung: "regelcode",
      rateBps: lage.rate.rateBps,
      thresholdCents: lage.rate.thresholdCents,
      basisCents,
      levyCents: levy,
    },
    validierung: { bestanden: true, meldungen: [KEINE_FREIGABE] },
  });
}

export async function runSaasKiKernel(auftrag: KernelAuftrag): Promise<KernelErgebnis> {
  if (auftrag.auftrag === "rag") return ragAuftrag(auftrag.frage, auftrag.jahr);
  if (auftrag.auftrag === "fall") return fallAuftrag(auftrag.runId, auftrag.client);
  return berechnungsAuftrag(auftrag.jahr, auftrag.basisCents);
}
