# SaaS-KI-Kernel — Prüfexport

Stand: 7. Oktober 2026. Diese Datei ist ein Export zum Lesen und Hochladen. Sie führt keinen Code aus und ersetzt die Moduldateien nicht. Der Anwendungscode bleibt in den ursprünglichen Dateien.

## Auslassungen

Ausdrücklich nicht enthalten:

- `config/secrets.env`, `.env.local` und jeder konkrete API-Schlüssel oder jedes Passwort. `src/lib/rag-retrieval.ts` zeigt nur, wie ein Schlüssel aus diesen Dateien gelesen wird. Die Werte selbst stehen hier nicht.
- `src/lib/secrets.ts` und `src/lib/admin/session.ts`.
- SQLite-Dateien, Fallzeilen, Chatverläufe, hochgeladene Rechnungen und sonstige Kundenunterlagen.
- Oberflächen, Admin-Komponenten und die übrigen API-Routen außer dem RAG-Aufruf.
- `src/lib/llm/mistral.ts`, `src/lib/llm/mock.ts`, `src/lib/llm/index.ts`, `src/lib/pipeline/prepare.ts`, `src/lib/domain/reconcile.ts`, `src/lib/domain/parse-reading.ts`, `src/lib/domain/consensus.ts`, `rules/prompt-v12.md`, `rules/szenarien.json`.
- Der übrige Teil von `src/lib/db.ts` nach den abgedruckten Auszügen: Fall-, Dokument- und Chat-Zugriffe.
- `tests/stages.test.ts`, `tests/chat-guard.test.ts` und die Playwright-Dateien. Playwright wurde für diesen Stand nicht ausgeführt.
- `node_modules` und der Mistral-SDK.

## Ablauf

Einstieg: `runSaasKiKernel(auftrag)` in `src/lib/saas-ki-kernel.ts`.

Jeder Auftrag durchläuft dieselben Schritte: Sachverhalt erfassen, Jahrespaket festlegen, Quellen abrufen, KI-Analyse, Regel- und Zahlenprüfung, Berechnung, Validierung, strukturiertes Ergebnis. Das Ergebnis trägt immer `konsensIstKeineFreigabe: true`.

| Auftrag | Was der Kernel selbst tut | Welches Modul die Arbeit macht |
|---|---|---|
| `rag` | Jahr aus der Frage oder aus dem Argument, Library `KSK-Referenzen` festlegen, Paket bauen | `pruefeRagFrage` in `rag-analysis.ts`. Die Suche läuft nur mit der festgelegten Library-ID. Berechnung bleibt `null`; der Hinweis lautet, dass nicht gerechnet wird. |
| `fall` | Paket mit Methodenversion, Regelstand und aktiver Library anlegen und als Artefakt `paket` mit `temporary = 0` speichern. Das Jahr ist zu diesem Zeitpunkt leer. | `executeRun` in `pipeline/run.ts`. Danach übernimmt der Kernel Jahr, Register-Snapshot und Abgabe aus dem Bericht. |
| `berechnung` | Jahr und ganze Cent prüfen, Paket aus dem freigegebenen Register bauen | `satzlage` in `domain/rules.ts` und `levyCents` in `domain/money.ts`. `ausfuehrung` ist `regelcode`. Fehlt der Satz, bleibt `levyCents` leer. |

Verbindliche Sätze und Grenzen kommen aus `zahlen_register`, und nur mit Status `freigegeben` plus Freigabenachweis. `rules/saetze.json` liefert Rundung und den Geltungsbereich der Grenze. Die Jahreszahlen in dieser Datei sind nicht die Quelle der Berechnung.

Modellkonsens vergleicht Prüferantworten. Er gibt keinen Wert frei.

## Code


### `src/lib/saas-ki-kernel.ts`

```ts
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
```

### `src/lib/saas_kernel.ts`

```ts
export {
  LIBRARY_NAME,
  MistralConfigError,
  createLibrary,
  deleteDocument,
  deleteLibrary,
  explainMistralError,
  getLibrary,
  mistralConnected,
  uploadDocument,
  type LibraryDocumentView,
  type LibraryView,
} from "@/lib/rag-retrieval";
export { RAG_SYSTEM_PROMPT, ragUserPrompt } from "@/lib/rag-system-prompt";
export {
  amountKeys,
  konsensVergleich,
  laufSchluessel,
  vergleicheLaeufe,
  type KonsensErgebnis,
  type PrueferSicht,
} from "@/lib/model-consensus";
export { askLibrary, type PrueferErgebnis, type RagAntwort } from "@/lib/rag-analysis";
export { matchedDocuments } from "@/lib/mistral/rag-pruefung";
export { runSaasKiKernel, type JahresPaket, type KernelErgebnis } from "@/lib/saas-ki-kernel";
```

### `src/lib/rag-analysis.ts`

```ts
import { readFileSync } from "node:fs";
import path from "node:path";
import type { Mistral } from "@mistralai/mistralai";
import { dokumentZahlen, ergaenzeZahlen, fehlendeBetragszeilen, grenzenAusAntwort, nenntKeineZahlen, parseAbschnitte, zahlenAusNachfrage } from "@/lib/mistral/abschnitte";
import { betraegeImText, chunkZeile, dokumentbasisWarnung, stellenBlock, type ChunkBeleg } from "@/lib/mistral/chunks";
import { prozentWerte, pruefeAntwort, type RagPruefung } from "@/lib/mistral/rag-pruefung";
import { bezugsjahr, f05Hinweis, klassifiziereProzent, ladeZahlenWerte, mitZeitabweichung, nurGueltigeBetraege, relevanteBetraege, zeitErgebnis, zeitHinweisEintraege, type ProzentZeile, type ZeitCheck } from "@/lib/mistral/zahlen-werte";
import { konsensVergleich, laufSchluessel, vergleicheLaeufe, type KonsensErgebnis, type PrueferSicht } from "@/lib/model-consensus";
import { ragUserPrompt } from "@/lib/rag-system-prompt";
import { askOneModel, client, ergaenzeBetragsstellen, explainMistralError, findLibrary, hybridZiele } from "@/lib/rag-retrieval";

type PrueferConfig = { id: string; label: string; modell: string };

export type PrueferErgebnis = {
  id: string;
  label: string;
  modell: string;
  ok: boolean;
  answer: string;
  gezeigt: boolean;
  nutzerangaben: string;
  hinweise: string[];
  chunks: string;
};

function loadPrueferConfig(): { pruefer: PrueferConfig[]; angezeigt: string } {
  const file = path.join(/*turbopackIgnore: true*/ process.cwd(), "config", "rag-pruefer.json");
  const parsed = JSON.parse(readFileSync(file, "utf8")) as { pruefer?: PrueferConfig[]; angezeigte_antwort?: string };
  const pruefer = parsed.pruefer ?? [];
  if (pruefer.length !== 2) throw new Error("Die Prüfer-Konfiguration braucht genau zwei Modelle.");
  return { pruefer, angezeigt: parsed.angezeigte_antwort || pruefer[1].id };
}

async function assertPrueferModels(api: Mistral, models: string[]): Promise<void> {
  const listed = await api.models.list();
  const available = new Set((listed.data ?? []).flatMap((item) => "id" in item && typeof item.id === "string" ? [item.id] : []));
  const missing = models.filter((model) => !available.has(model));
  if (missing.length > 0) {
    throw new Error(`Diese Prüfer-Modelle sind unter diesem Schlüssel nicht verfügbar: ${missing.join(", ")}. Die Prüfung wird nicht auf weniger Modelle verkürzt.`);
  }
}

function nachfragePrompt(frage: string, zeilen: string[]): string {
  return [
    `Frage: ${frage}`,
    "",
    "Diese Beträge stehen wörtlich in den abgerufenen Dokumentstellen:",
    ...zeilen.map((zeile) => `- ${zeile}`),
    "",
    "Schreibe nur diesen Abschnitt:",
    "ZAHLEN:",
    "- <Betrag> | <Dokumentname>",
    "Nimm jeden Betrag aus der Liste auf, dessen Dokument die Frage beantwortet.",
  ].join("\n");
}

export type RagAntwort = {
  answer: string;
  sources: string[];
  pruefung: RagPruefung | null;
  konsens: KonsensErgebnis;
  pruefer: PrueferErgebnis[];
  zeit: ZeitCheck;
  prozent: ProzentZeile[];
  listeHinweise: string[];
  basis: string | null;
};

function laufAus(zeilen: PrueferSicht[], konsens: KonsensErgebnis): { signatur: string; einig: boolean; kurz: string } {
  const basis = laufSchluessel(zeilen);
  const einig = konsens.status === "konsens" || konsens.status === "hinweis";
  return { signatur: `${konsens.status}|${basis.signatur}`, einig, kurz: konsens.detail ?? konsens.line };
}

async function frageEinmal(question: string, libraryId: string): Promise<{ ergebnis: RagAntwort; lauf: { signatur: string; einig: boolean; kurz: string } }> {
  const trimmed = question.trim();
  if (!trimmed) throw new Error("Die Frage fehlt.");
  const liste = ladeZahlenWerte();
  const bezug = bezugsjahr(trimmed);
  const userPrompt = ragUserPrompt(trimmed, bezug.jahr);
  const api = client();
  const { pruefer, angezeigt } = loadPrueferConfig();
  await assertPrueferModels(api, pruefer.map((item) => item.modell));
  const listedDocuments = await api.beta.libraries.documents.list({ libraryId, pageSize: 100 });
  const documentNames = listedDocuments.data.map((document) => document.name).filter(Boolean);
  let gemeinsame: ChunkBeleg[] = [];
  try {
    const suche = await askOneModel(api, pruefer[0].modell, userPrompt, libraryId);
    gemeinsame = suche.chunks.filter((chunk) => chunk.text.trim());
  } catch {
    gemeinsame = [];
  }
  gemeinsame = await ergaenzeBetragsstellen(
    api,
    libraryId,
    gemeinsame,
    listedDocuments.data.map((document) => ({ id: document.id, name: document.name })),
    hybridZiele(trimmed, liste),
  );
  const prompt = gemeinsame.length > 0 ? `${userPrompt}\n\n${stellenBlock(gemeinsame)}` : userPrompt;
  const settled = await Promise.all(pruefer.map(async (item) => {
    try {
      const result = await askOneModel(api, item.modell, prompt, gemeinsame.length > 0 ? null : libraryId);
      if (gemeinsame.length > 0) {
        result.chunks = gemeinsame;
        result.passages = gemeinsame.map((chunk) => chunk.text);
        result.citationsField = true;
      }
      return { item, ok: true as const, result };
    } catch (error) {
      return { item, ok: false as const, error: explainMistralError(error) };
    }
  }));
  if (settled.every((item) => !item.ok)) {
    const first = settled.find((item) => !item.ok);
    throw new Error(`Die Frage ist fehlgeschlagen, weil ${first && !first.ok ? first.error : "kein Prüfer geantwortet hat."}`);
  }
  const nachgefragt = new Set<string>();
  if (gemeinsame.length > 0) {
    const relevante = relevanteBetraege(trimmed, liste, bezug.jahr)
      .filter((item) => item.unit === "euro")
      .map((item) => item.value);
    const zeilen = betraegeImText(gemeinsame);
    await Promise.all(settled.map(async (entry) => {
      if (!entry.ok) return;
      const fehlend = fehlendeBetragszeilen(entry.result.answer, zeilen, relevante);
      if (fehlend.length === 0) return;
      try {
        const retry = await askOneModel(
          api,
          entry.item.modell,
          nachfragePrompt(trimmed, fehlend),
          null,
          "Du schreibst nur den Abschnitt ZAHLEN. Übernimm jeden Betrag aus der Liste, dessen Dokument die Frage beantwortet. Nenne den Dokumentnamen, keine Kennung.",
        );
        const zusatz = zahlenAusNachfrage(retry.answer, fehlend);
        if (!zusatz) return;
        entry.result.answer = ergaenzeZahlen(entry.result.answer, zusatz);
        nachgefragt.add(entry.item.id);
      } catch {
        // Die erste Antwort bleibt stehen.
      }
    }));
  }
  const ausgewertet = settled.map((entry) => {
    if (!entry.ok) {
      return {
        id: entry.item.id,
        label: entry.item.label,
        modell: entry.item.modell,
        ok: false as const,
        answer: "",
        sources: [] as string[],
        passages: [] as string[],
        citationsField: false,
        chunks: [] as ChunkBeleg[],
        dok: null,
      };
    }
    return {
      id: entry.item.id,
      label: entry.item.label,
      modell: entry.item.modell,
      ok: true as const,
      answer: entry.result.answer,
      sources: entry.result.sources,
      passages: entry.result.passages,
      citationsField: entry.result.citationsField,
      chunks: entry.result.chunks,
      dok: dokumentZahlen({
        answer: entry.result.answer,
        corpus: entry.result.passages.join("\n"),
        documentNames,
        prueferLabel: entry.item.label,
        liste,
      }),
    };
  });
  const zeitEintraege = ausgewertet.flatMap((entry) => zeitHinweisEintraege(
    entry.ok ? grenzenAusAntwort(entry.answer) : [],
    liste,
    bezug.jahr,
    entry.label,
  ));
  const zeit = zeitErgebnis({ jahr: bezug.jahr, angenommen: bezug.angenommen, hinweise: zeitEintraege.map((eintrag) => eintrag.text) });
  const prozent = ausgewertet.flatMap((entry) => {
    if (!entry.ok) return [];
    const sections = parseAbschnitte(entry.answer);
    const text = [sections.zahlen, sections.nutzerangaben].filter(Boolean).join("\n") || entry.answer;
    const gesehen = new Set<string>();
    const zeilen: ProzentZeile[] = [];
    for (const wert of prozentWerte(text)) {
      const key = wert.value.toFixed(2);
      if (gesehen.has(key)) continue;
      gesehen.add(key);
      zeilen.push({
        pruefer: entry.label.match(/Prüfer\s+\d+/)?.[0] ?? entry.label,
        label: wert.label,
        status: klassifiziereProzent(wert.value, trimmed, liste),
      });
    }
    return zeilen;
  });
  const listeHinweise = ausgewertet.flatMap((entry) => {
    if (!entry.ok) return [];
    const hinweis = f05Hinweis({
      nenntKeine: nenntKeineZahlen(entry.answer),
      frage: trimmed,
      jahr: bezug.jahr,
      liste,
      prueferLabel: entry.label,
    });
    return hinweis ? [hinweis] : [];
  });
  const basis = dokumentbasisWarnung(ausgewertet.map((entry) => ({ label: entry.label, chunks: entry.chunks })));
  const konsensZeilen = ausgewertet.map((entry) => {
    const gueltig = nurGueltigeBetraege(entry.dok?.keys ?? [], entry.dok?.labels ?? [], liste, bezug.jahr);
    return {
      id: entry.id,
      label: entry.label,
      ok: entry.ok,
      answer: entry.answer,
      documents: entry.dok?.documents ?? [],
      amountKeys: gueltig.keys,
      amountLabels: gueltig.labels,
    };
  });
  const konsens = mitZeitabweichung(
    konsensVergleich(konsensZeilen),
    zeitEintraege,
    konsensZeilen.some((entry) => entry.ok && entry.amountKeys.length > 0),
  );
  const shown = ausgewertet.find((entry) => entry.id === angezeigt) ?? ausgewertet[ausgewertet.length - 1];
  const prueferErgebnis: PrueferErgebnis[] = ausgewertet.map((entry) => ({
    id: entry.id,
    label: entry.label,
    modell: entry.modell,
    ok: entry.ok,
    answer: entry.answer,
    gezeigt: entry.id === angezeigt,
    nutzerangaben: entry.dok?.nutzerangaben ?? "",
    hinweise: [
      ...(entry.dok?.hinweise ?? []),
      ...(nachgefragt.has(entry.id) ? ["Nachfrage: im Text stehende Beträge waren in der ersten Antwort nicht genannt."] : []),
    ],
    chunks: chunkZeile(entry.chunks),
  }));
  const lauf = laufAus(konsensZeilen, konsens);
  if (!shown.ok) {
    return { ergebnis: { answer: "", sources: [], pruefung: null, konsens, pruefer: prueferErgebnis, zeit, prozent, listeHinweise, basis }, lauf };
  }
  const sections = parseAbschnitte(shown.answer);
  const zahlText = sections.vollstaendig
    ? [sections.kernaussagen, sections.zahlen, sections.fundstellen, sections.luecken].join("\n")
    : shown.answer;
  const pruefung = pruefeAntwort({
    answer: shown.answer,
    zahlText,
    documentNames,
    citationsField: shown.citationsField,
    passages: shown.passages,
    citationLabels: shown.sources,
  });
  return {
    ergebnis: {
      answer: shown.answer,
      sources: shown.sources,
      pruefung,
      konsens,
      pruefer: prueferErgebnis,
      zeit,
      prozent,
      listeHinweise,
      basis,
    },
    lauf,
  };
}

export async function pruefeRagFrage(question: string, libraryId: string): Promise<RagAntwort> {
  const erster = await frageEinmal(question, libraryId);
  if (erster.ergebnis.konsens.status !== "abweichung" && erster.ergebnis.konsens.status !== "keiner") return erster.ergebnis;
  const [zweit, dritt] = await Promise.all([frageEinmal(question, libraryId), frageEinmal(question, libraryId)]);
  const vergleich = vergleicheLaeufe([erster.lauf, zweit.lauf, dritt.lauf]);
  const gewaehlt = vergleich.status === "konsens" ? erster : dritt;
  return { ...gewaehlt.ergebnis, konsens: vergleich };
}

export async function askLibrary(question: string): Promise<RagAntwort> {
  const library = await findLibrary(client());
  if (!library) throw new Error("Die Library KSK-Referenzen gibt es nicht. Lege sie zuerst an.");
  return pruefeRagFrage(question, library.id);
}
```

### `src/lib/rag-retrieval.ts`

```ts
import { readFileSync } from "node:fs";
import path from "node:path";
import { Mistral } from "@mistralai/mistralai";
import type { FilePurpose } from "@mistralai/mistralai/models/components/filepurpose.js";
import { citationsFromResponse, fundstellenFromAnswer } from "@/lib/mistral/fundstellen";
import { chunksAusWert, ohneInterneChunks, type ChunkBeleg } from "@/lib/mistral/chunks";
import { istInterneQuelle, SCHLUESSELBEGRIFFE, textstellenUmBegriffe, textstellenUmBetraege, textstellenUmProzente, zahlenAusFrage } from "@/lib/mistral/rag-pruefung";
import { alleThemenBetraege, type ZahlenListe } from "@/lib/mistral/zahlen-werte";
import { RAG_SYSTEM_PROMPT } from "@/lib/rag-system-prompt";

export const LIBRARY_NAME = "KSK-Referenzen";
export const MISSING_KEY = "MISTRAL_API_KEY fehlt in .env.local";

export class MistralConfigError extends Error {
  constructor() {
    super(MISSING_KEY);
  }
}

export type LibraryDocumentView = {
  id: string;
  name: string;
  pageCount: number | null;
  summary: string | null;
  status: "Running" | "Completed" | "Fehler";
};

export type LibraryView = {
  id: string;
  name: string;
  description: string | null;
  documents: LibraryDocumentView[];
};

function keyFromText(text: string): string | null {
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.startsWith("MISTRAL_API_KEY=")) continue;
    let value = trimmed.slice("MISTRAL_API_KEY=".length).trim();
    if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!value || value === "hier-den-neuen-schluessel-eintragen") return null;
    return value;
  }
  return null;
}

function readKeyFromEnvLocal(): string {
  const files = [
    path.join(/*turbopackIgnore: true*/ process.cwd(), ".env.local"),
    path.join(/*turbopackIgnore: true*/ process.cwd(), "config", "secrets.env"),
  ];
  for (const file of files) {
    try {
      const value = keyFromText(readFileSync(file, "utf8"));
      if (value) return value;
    } catch {
      // Nächste Quelle.
    }
  }
  const fromProcess = process.env.MISTRAL_API_KEY?.trim();
  if (fromProcess && fromProcess !== "hier-den-neuen-schluessel-eintragen") return fromProcess;
  throw new MistralConfigError();
}

export function client(): Mistral {
  return new Mistral({ apiKey: readKeyFromEnvLocal() });
}

export function explainMistralError(error: unknown): string {
  let text = "Mistral hat nicht geantwortet.";
  if (error instanceof Error) text = error.message;
  if (error && typeof error === "object" && "body" in error && typeof (error as { body?: unknown }).body === "string") {
    text = `${text} ${(error as { body: string }).body}`;
  }
  const key = (() => {
    try {
      return readKeyFromEnvLocal();
    } catch {
      return "";
    }
  })();
  if (key) text = text.split(key).join("[entfernt]");
  return text.replace(/Bearer\s+\S+/gi, "Bearer [entfernt]").replace(/\s+/g, " ").trim().slice(0, 350);
}

export function mapLibraryStatus(processStatus: string, processingStatus: string): "Running" | "Completed" | "Fehler" {
  const value = `${processStatus} ${processingStatus}`.toLowerCase();
  if (/\b(done|completed|complete)\b/.test(value)) return "Completed";
  if (value.includes("error") || value.includes("fail") || value.includes("missing")) return "Fehler";
  return "Running";
}

export async function mistralConnected(): Promise<"verbunden" | "nicht verbunden"> {
  try {
    await client().models.list();
    return "verbunden";
  } catch (error) {
    if (error instanceof MistralConfigError) throw error;
    return "nicht verbunden";
  }
}

export async function findLibrary(api: Mistral) {
  const listed = await api.beta.libraries.list({ pageSize: 100, search: LIBRARY_NAME });
  return listed.data.find((item) => item.name === LIBRARY_NAME) ?? null;
}

export async function getLibrary(): Promise<LibraryView | null> {
  const api = client();
  const library = await findLibrary(api);
  if (!library) return null;
  const listed = await api.beta.libraries.documents.list({ libraryId: library.id, pageSize: 100 });
  const documents: LibraryDocumentView[] = [];
  for (const document of listed.data) {
    let processStatus = String(document.processStatus ?? "");
    let processingStatus = String(document.processingStatus ?? "");
    const mapped = mapLibraryStatus(processStatus, processingStatus);
    if (mapped !== "Completed") {
      try {
        const status = await api.beta.libraries.documents.status({ libraryId: library.id, documentId: document.id });
        processStatus = String(status.processStatus ?? processStatus);
        processingStatus = String(status.processingStatus ?? processingStatus);
      } catch {
        // Die Liste bleibt die Quelle, wenn der Statusabruf scheitert.
      }
    }
    documents.push({
      id: document.id,
      name: document.name,
      pageCount: typeof document.numberOfPages === "number" ? document.numberOfPages : null,
      summary: document.summary ?? null,
      status: mapLibraryStatus(processStatus, processingStatus),
    });
  }
  return {
    id: library.id,
    name: library.name,
    description: library.description ?? null,
    documents,
  };
}

export async function createLibrary(description: string): Promise<LibraryView> {
  const api = client();
  const existing = await findLibrary(api);
  if (existing) throw new Error("Die Library KSK-Referenzen gibt es schon.");
  await api.beta.libraries.create({
    name: LIBRARY_NAME,
    description: description.trim() || null,
  });
  const created = await getLibrary();
  if (!created) throw new Error("Mistral hat die Library angelegt, aber sie ist in der Liste nicht sichtbar.");
  return created;
}

export async function deleteLibrary(): Promise<void> {
  const api = client();
  const library = await findLibrary(api);
  if (!library) throw new Error("Die Library KSK-Referenzen gibt es nicht.");
  await api.beta.libraries.delete({ libraryId: library.id });
}

function purposeRejected(error: unknown): boolean {
  const status = error && typeof error === "object" && "statusCode" in error ? Number((error as { statusCode: number }).statusCode) : 0;
  return status === 422;
}

export async function uploadDocument(filename: string, bytes: Uint8Array): Promise<void> {
  if (!filename.trim() || bytes.byteLength === 0) {
    throw new Error("Upload fehlgeschlagen, weil die Datei leer ist.");
  }
  const api = client();
  const library = await findLibrary(api);
  if (!library) throw new Error("Upload fehlgeschlagen, weil die Library KSK-Referenzen noch nicht angelegt ist.");
  const safeName = filename.replace(/[\\/]/g, " ").trim();
  try {
    await api.files.upload({
      purpose: "retrieval" as FilePurpose,
      file: { fileName: safeName, content: bytes.slice() },
    });
  } catch (error) {
    if (!purposeRejected(error)) {
      throw new Error(`Upload fehlgeschlagen, weil ${explainMistralError(error)}`);
    }
  }
  try {
    await api.beta.libraries.documents.upload({
      libraryId: library.id,
      requestBody: { file: { fileName: safeName, content: bytes.slice() } },
    });
  } catch (error) {
    throw new Error(`Upload fehlgeschlagen, weil ${explainMistralError(error)}`);
  }
}

export async function deleteDocument(documentId: string): Promise<void> {
  const api = client();
  const library = await findLibrary(api);
  if (!library) throw new Error("Die Library KSK-Referenzen gibt es nicht.");
  await api.beta.libraries.documents.delete({ libraryId: library.id, documentId });
}

function collectChunk(chunk: unknown, texts: string[], sources: string[], passages: string[]): void {
  if (!chunk || typeof chunk !== "object") return;
  const record = chunk as { type?: string; text?: string; title?: string; description?: string };
  if (record.type === "text" && typeof record.text === "string") texts.push(record.text);
  if (record.type === "tool_reference" && typeof record.title === "string" && record.title.trim()) sources.push(record.title.trim());
  if (typeof record.description === "string" && record.description.trim()) passages.push(record.description);
}

const PASSAGE_KEYS = new Set(["content", "text", "snippet", "quote", "page_content", "pageContent", "chunk", "extracted_text", "extractedText", "description"]);

function harvestPassages(value: unknown, passages: string[], depth = 0): void {
  if (depth > 8 || value == null || typeof value !== "object") return;
  if (Array.isArray(value)) {
    for (const item of value) harvestPassages(item, passages, depth + 1);
    return;
  }
  for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
    if (key === "result" && typeof nested === "string") {
      try {
        harvestPassages(JSON.parse(nested) as unknown, passages, depth + 1);
      } catch {
        // Der Retrieval-Text ist kein JSON.
      }
      continue;
    }
    if ((key === "snippets" || key === "snippet") && Array.isArray(nested)) {
      for (const item of nested) {
        if (typeof item === "string" && item.trim()) passages.push(item);
        else if (item && typeof item === "object") harvestPassages(item, passages, depth + 1);
      }
      continue;
    }
    if (typeof nested === "string" && PASSAGE_KEYS.has(key) && nested.trim()) passages.push(nested);
    else if (nested && typeof nested === "object") harvestPassages(nested, passages, depth + 1);
  }
}

function hasCitationsField(value: unknown, depth = 0): boolean {
  if (depth > 8 || value == null || typeof value !== "object") return false;
  if (Array.isArray(value)) return value.some((item) => hasCitationsField(item, depth + 1));
  if (Object.prototype.hasOwnProperty.call(value, "citations")) return true;
  return Object.values(value as Record<string, unknown>).some((nested) => hasCitationsField(nested, depth + 1));
}

function collectInfo(info: object, sources: string[]): void {
  const record = info as Record<string, unknown>;
  for (const key of ["document_name", "documentName", "file_name", "fileName", "title", "name"]) {
    const value = record[key];
    if (typeof value === "string" && value.trim() && !/^(document_library|web_search|code_interpreter)$/i.test(value.trim())) sources.push(value.trim());
  }
  for (const value of Object.values(record)) {
    if (!Array.isArray(value)) continue;
    for (const item of value) {
      if (item && typeof item === "object") collectInfo(item, sources);
    }
  }
}

function dokumentZuName(name: string, dokumente: Array<{ id: string; name: string }>): { id: string; name: string } | null {
  const exact = dokumente.find((dokument) => dokument.name.toLowerCase() === name.toLowerCase());
  if (exact) return exact;
  const info = name.match(/info[_ -]?(\d+)/i);
  if (info) {
    const treffer = dokumente.find((dokument) => new RegExp(`info[_ -]?${info[1]}\\b`, "i").test(dokument.name));
    if (treffer) return treffer;
  }
  return dokumente.find((dokument) => name.toLowerCase().includes(dokument.name.toLowerCase())) ?? null;
}

export function hybridZiele(frage: string, liste: ZahlenListe): { euro: number[]; prozent: number[]; begriffe: string[] } {
  const ausFrage = zahlenAusFrage(frage);
  const thema = alleThemenBetraege(frage, liste);
  const euro = new Set<string>(ausFrage.betraege.map((value) => value.toFixed(2)));
  const prozent = new Set<string>(ausFrage.prozente.map((value) => value.toFixed(2)));
  for (const ziel of thema) {
    if (ziel.unit === "prozent") prozent.add(ziel.value.toFixed(2));
    else euro.add(ziel.value.toFixed(2));
  }
  const hay = frage.toLowerCase();
  const begriffe = [
    ...SCHLUESSELBEGRIFFE.filter((wort) => hay.includes(wort)),
    ...liste.wertegruppen.flatMap((gruppe) => gruppe.stichworte ?? []).filter((wort) => wort.length >= 4 && hay.includes(wort.toLowerCase())),
  ];
  return { euro: [...euro].map(Number), prozent: [...prozent].map(Number), begriffe: [...new Set(begriffe)] };
}

export async function ergaenzeBetragsstellen(
  api: Mistral,
  libraryId: string,
  chunks: ChunkBeleg[],
  dokumente: Array<{ id: string; name: string }>,
  ziele: { euro: number[]; prozent: number[]; begriffe: string[] },
): Promise<ChunkBeleg[]> {
  if (ziele.euro.length === 0 && ziele.prozent.length === 0 && ziele.begriffe.length === 0) return chunks;
  const kopie = chunks.map((chunk) => ({ ...chunk }));
  const namen = [...new Set([
    ...kopie.map((chunk) => chunk.dokument),
    ...dokumente.map((dokument) => dokument.name),
  ].filter((name) => name && !istInterneQuelle(name)))];
  await Promise.all(namen.map(async (name) => {
    const dokument = dokumentZuName(name, dokumente);
    if (!dokument) return;
    let text = "";
    try {
      const inhalt = await api.beta.libraries.documents.textContent({ libraryId, documentId: dokument.id });
      text = typeof inhalt.text === "string" ? inhalt.text : "";
    } catch {
      return;
    }
    const stellen = [
      ...textstellenUmBetraege(text, ziele.euro),
      ...textstellenUmProzente(text, ziele.prozent),
      ...textstellenUmBegriffe(text, ziele.begriffe),
    ];
    if (stellen.length === 0) return;
    const zusatz = stellen.join("\n").slice(0, 1800);
    const ziel = kopie.find((chunk) => chunk.dokument === name);
    if (ziel) ziel.text = `${zusatz}\n${ziel.text}`;
    else kopie.push({ id: `${dokument.id}:suche`, dokument: dokument.name, seite: null, text: zusatz });
  }));
  return kopie;
}

export async function askOneModel(api: Mistral, model: string, userPrompt: string, libraryId: string | null, instructions = RAG_SYSTEM_PROMPT): Promise<{ answer: string; sources: string[]; passages: string[]; citationsField: boolean; chunks: ChunkBeleg[] }> {
  const response = await api.beta.conversations.start({
    model,
    store: false,
    inputs: userPrompt,
    instructions,
    ...(libraryId ? { tools: [{ type: "document_library" as const, libraryIds: [libraryId] }] } : {}),
    completionArgs: { temperature: 0 },
  });
  const texts: string[] = [];
  const toolSources: string[] = [];
  const passages: string[] = [];
  const chunks: ChunkBeleg[] = [];
  for (const output of response.outputs ?? []) {
    if (output.type === "message.output") {
      if (typeof output.content === "string") texts.push(output.content);
      else if (Array.isArray(output.content)) {
        for (const chunk of output.content) collectChunk(chunk, texts, toolSources, passages);
      }
    }
    if (output.type === "tool.execution" && output.info && typeof output.info === "object") {
      collectInfo(output.info, toolSources);
      harvestPassages(output.info, passages);
      chunks.push(...chunksAusWert(output.info));
    }
  }
  const answer = texts.join("").trim();
  const fromCitations = citationsFromResponse(response);
  const fromText = fundstellenFromAnswer(answer);
  const listed = fromCitations.length > 0 ? fromCitations : fromText.length > 0 ? fromText : toolSources;
  const sources = [...new Set(listed.map((item) => item.trim()).filter(Boolean))];
  for (const label of fromCitations) passages.push(label);
  const externe = ohneInterneChunks(chunks);
  const chunkTexte = externe.map((chunk) => chunk.text).filter(Boolean);
  return {
    answer,
    sources: sources.filter((item) => !/prompt-v12(?:\.md)?/i.test(item)),
    passages: chunkTexte.length > 0 ? chunkTexte : passages.filter((item) => !/prompt-v12(?:\.md)?/i.test(item)),
    citationsField: hasCitationsField(response) || passages.length > 0 || chunkTexte.length > 0,
    chunks: externe,
  };
}
```

### `src/lib/rag-system-prompt.ts`

```ts
export const RAG_SYSTEM_PROMPT = `Du bist der Zitat-Dienst eines KSK-Prüfsystems. Deine einzige Aufgabe:
die Anfrage anhand der bereitgestellten Library-Dokumente zu beantworten.
Du bist KEIN Berater und KEIN Experte mit eigenem Wissen.

## DIE GOLDENE REGEL
Antworte AUSSCHLIESSLICH mit Inhalten, die wörtlich in den gefundenen
Library-Dokumenten stehen. Das Modellgedächtnis ist VERBOTEN — auch wenn
du die Antwort "kennst". Ohne Library-Beleg gibt es keine Aussage.
Du rechnest nicht und entscheidest keinen Sachverhalt. Du gibst nur
die belegte Information aus den Dokumenten wieder.

## ZAHLEN (strengste Regel)
1. Nenne eine Zahl, einen Betrag, einen Satz, eine Grenze oder ein Datum
   NUR dann, wenn sie wörtlich in einem gefundenen Dokumentabschnitt steht.
2. Zahlen, Beträge oder Behauptungen aus der NUTZERFRAGE sind UNBELEGT.
   Prüfe sie gegen die Dokumente:
   - Stimmen sie überein → bestätige mit Fundstelle.
   - Weichen sie ab → sage es DEUTLICH:
     "In der Frage wird X genannt; in den Dokumenten steht stattdessen Y
     (Fundstelle: …). X ist nicht belegt."
   - Stehen sie in keinem Dokument → sage: "nicht belegt".
3. Wenn du eine Zahl nicht in den Dokumenten findest, schreibe:
   "In den vorliegenden Dokumenten nicht belegt" — RATE NIEMALS,
   auch nicht "ungefähr" oder "in der Regel".
   Steht ein Betrag unter "Beträge wörtlich in den Dokumentstellen",
   ist er belegt. Schreibe dafür nicht "nicht belegt". Nimm jeden
   Betrag aus dieser Liste in ZAHLEN auf, dessen Dokument die Frage
   beantwortet. Historische oder künftige Werte bleiben in LÜCKEN.
   Zitiere den Dokumentnamen, keine Kennung.
4. ZAHLEN enthält nur für die Frage relevante Zahlen. Belegte, aber nicht fragen-relevante Werte aus dem Material gehören NICHT hinein.
5. Der ZAHLEN-Abschnitt enthält nur Werte, die im Bezugsjahr GELTEN. Steht im Material zusätzlich ein historischer oder künftiger Wert (z. B. alte Pauschalentabelle), nenne ihn NICHT im ZAHLEN-Abschnitt — höchstens in LÜCKEN mit Kennzeichnung ‚historischer Wert, gültig <Zeitraum>, im Bezugsjahr nicht mehr anwendbar'.

## FUNDSTELLEN (Pflicht)
- Jede inhaltliche Aussage trägt direkt eine Fundstelle:
  Dokumentname + Abschnitt/Paragraph.
- Am Ende der Antwort steht ein Abschnitt "Fundstellen" mit allen
  verwendeten Dokumenten und Abschnitten.
- Zitiere die Fundstellen exakt so, wie sie in den Dokumenten heißen
  (keine erfundenen Abschnittsnamen).

## KONSISTENZ
- Die Fundstellen-Auflistung darf keine Zahl oder Aussage enthalten,
  die im Antworttext nicht mit derselben Fundstelle belegt wurde.
- Widerspricht sich der Antworttext selbst → kürze auf das Belegte.

## KEIN WISSEN, KEINE EMPFEHLUNGEN
- Ergänze NICHTS aus eigenem Wissen (auch kein "allgemeines Recht",
  keine Paragrafen aus dem Gedächtnis).
- Gib KEINE Empfehlungen, keine Bewertung ("Sie sollten…"),
  keine Auslegung über den Dokumenttext hinaus.
- Deine Beispiele stammen ausschließlich aus den Dokumenten.

## FEHLENDE INFORMATION
Wenn die Dokumente die Frage nicht beantworten:
"Zu dieser Frage enthalten die vorliegenden Dokumente keine Aussage."
Das ist eine vollwertige, korrekte Antwort — besser als jede Vermutung.

## ANTWORTFORMAT (Pflicht, exakt diese 5 Abschnitte, in dieser Reihenfolge)

KERNAUSSAGEN:
- max. 3 kurze Sätze, nur aus den Dokumenten

ZAHLEN:
- NUR Zahlen, die wörtlich in den Dokumenten stehen.
- Je Zeile: <Betrag/Grenze> | <Fundstelle>
- Zahlen, Beträge oder Grenzen aus der Nutzerfrage haben hier
  NICHTS zu suchen — sie gehören ausschließlich in den Abschnitt
  NUTZERANGABEN-PRÜFUNG.

NUTZERANGABEN-PRÜFUNG:
- Für JEDE Zahl, jeden Betrag und jede Grenze aus der Nutzerfrage
  eine eigene Zeile:
  <Zahl> | bestätigt (Fundstelle: …)
  <Zahl> | nicht belegt
  <Zahl> | abweichend (Dokument sagt: …, Fundstelle: …)
- Keine Zahl aus der Frage darf unbewertet bleiben.

FUNDSTELLEN:
- Liste: Dokument + Abschnitt, je verwendeter Quelle

LÜCKEN:
- "nicht belegt" für alles, wozu die Dokumente nichts sagen

## DOKUMENTSTELLEN
ZAHLEN enthält nur Beträge, die in den Dokumentstellen als Geld stehen.
Eine Systemliste ist keine Fundstelle und wird nicht abgeschrieben.`;

const RAG_ANSWER_FORMAT = `## ANTWORTFORMAT (Pflicht, exakt diese 5 Abschnitte, in dieser Reihenfolge)

KERNAUSSAGEN:
- max. 3 kurze Sätze, nur aus den Dokumenten

ZAHLEN:
- NUR Zahlen, die wörtlich in den Dokumenten stehen.
- Je Zeile: <Betrag/Grenze> | <Fundstelle>
- Zahlen, Beträge oder Grenzen aus der Nutzerfrage haben hier
  NICHTS zu suchen — sie gehören ausschließlich in den Abschnitt
  NUTZERANGABEN-PRÜFUNG.

NUTZERANGABEN-PRÜFUNG:
- Für JEDE Zahl, jeden Betrag und jede Grenze aus der Nutzerfrage
  eine eigene Zeile:
  <Zahl> | bestätigt (Fundstelle: …)
  <Zahl> | nicht belegt
  <Zahl> | abweichend (Dokument sagt: …, Fundstelle: …)
- Keine Zahl aus der Frage darf unbewertet bleiben.

FUNDSTELLEN:
- Liste: Dokument + Abschnitt, je verwendeter Quelle

LÜCKEN:
- "nicht belegt" für alles, wozu die Dokumente nichts sagen`;

export function ragUserPrompt(question: string, jahr?: number): string {
  const bezug = typeof jahr === "number" ? `Bezugsjahr: ${jahr}\n\n` : "";
  return `${bezug}## Nutzerfrage (Zahlen darin sind UNBELEGT und gegen die Dokumente zu prüfen)\n${question}\n\n${RAG_ANSWER_FORMAT}`;
}
```

### `src/lib/model-consensus.ts`

```ts
import { euroAmounts } from "@/lib/mistral/rag-pruefung";

export type LaufSicht = { signatur: string; einig: boolean; kurz: string };

export type PrueferSicht = {
  id: string;
  label: string;
  ok: boolean;
  answer: string;
  documents: string[];
  amountKeys?: string[];
  amountLabels?: string[];
};

export type KonsensErgebnis = {
  status: "konsens" | "abweichung" | "keiner" | "nicht-pruefbar" | "hinweis";
  line: string;
  detail: string | null;
};

function groupWho(labels: string[]): string {
  const numbers = labels.map((label) => (label ?? "").match(/Prüfer\s+(\d+)/)?.[1] ?? "");
  if (numbers.every(Boolean)) return `Prüfer ${numbers.join(" & ")}`;
  return labels.join(" & ");
}

export function amountKeys(answer: string): { keys: string[]; labels: string[] } {
  const amounts = euroAmounts(answer);
  return {
    keys: amounts.map((item) => item.value.toFixed(2)),
    labels: amounts.map((item) => item.label),
  };
}

function signature(keys: string[], documents: string[]): string {
  return `${[...keys].sort().join(",")}|${[...documents].sort().join(",")}`;
}

function groupText(labels: string[], amounts: string[], documents: string[]): string {
  const who = groupWho(labels);
  const money = amounts.length > 0 ? amounts.join(", ") : "keine €-Beträge";
  const docs = documents.length > 0 ? documents.join(", ") : "keine Fundstelle";
  return `${who}: ${money} / ${docs}`;
}

function vorbereiten(rows: PrueferSicht[]): KonsensErgebnis & LaufSicht {
  const answered = rows.filter((row) => row.ok);
  if (answered.length < rows.length) {
    const line = `⚠️ nicht prüfbar (${answered.length}/${rows.length} geantwortet)`;
    return { status: "nicht-pruefbar", line, detail: null, signatur: `nicht-pruefbar|${answered.length}`, einig: false, kurz: line };
  }
  const prepared = answered.map((row) => {
    const amounts = row.amountKeys
      ? { keys: row.amountKeys, labels: row.amountLabels ?? [] }
      : amountKeys(row.answer);
    return { ...row, keys: amounts.keys, labels: amounts.labels, documents: [...row.documents].sort() };
  });
  const groups = new Map<string, typeof prepared>();
  for (const row of prepared) {
    const key = signature(row.keys, row.documents);
    groups.set(key, [...(groups.get(key) ?? []), row]);
  }
  const ordered = [...groups.values()].sort((a, b) => a.length - b.length);
  const detail = ordered.map((group) => groupText(group.map((row) => row.label), group[0].labels, group[0].documents)).join(" — ");
  const signatur = ordered.map((group) => signature(group[0].keys, group[0].documents)).join("||");
  if (groups.size === 1) {
    return { status: "konsens", line: `✅ Konsens ${rows.length}/${rows.length}`, detail: null, signatur, einig: true, kurz: detail };
  }
  if (rows.length > 2 && ordered.some((group) => group.length === rows.length - 1)) {
    const line = "⚠️ Abweichung 2/3 — NICHT OK, keine Mehrheitsentscheidung";
    return { status: "abweichung", line, detail, signatur, einig: false, kurz: detail };
  }
  const line = "❌ Kein Konsens — UNGEKLÄRT";
  return { status: "keiner", line, detail, signatur, einig: false, kurz: detail };
}

export function konsensVergleich(rows: PrueferSicht[]): KonsensErgebnis {
  const ergebnis = vorbereiten(rows);
  return { status: ergebnis.status, line: ergebnis.line, detail: ergebnis.detail };
}

export function laufSchluessel(rows: PrueferSicht[]): LaufSicht {
  const ergebnis = vorbereiten(rows);
  return { signatur: ergebnis.signatur, einig: ergebnis.einig, kurz: ergebnis.kurz };
}

export function vergleicheLaeufe(laeufe: LaufSicht[]): KonsensErgebnis {
  const detail = laeufe.map((lauf, index) => `Lauf ${index + 1}: ${lauf.kurz}`).join(" — ");
  const gleich = laeufe.length === 3 && laeufe.every((lauf) => lauf.einig && lauf.signatur === laeufe[0].signatur);
  if (gleich) return { status: "konsens", line: "✅ Dieselbe Antwort in 3 von 3 Läufen", detail };
  return { status: "keiner", line: "❌ Kein Konsens — die drei Läufe stimmen nicht überein", detail };
}
```

### `src/lib/mistral/rag-pruefung.ts`

```ts
export type ZahlenPruefung = {
  status: "bestanden" | "warnung" | "uebersprungen";
  checked: number;
  lines: string[];
};

export type LibraryPruefung = {
  ok: boolean;
  documents: string[];
  line: string;
};

export type RagPruefung = {
  zahlen: ZahlenPruefung;
  library: LibraryPruefung;
  interne: string | null;
};

const SKIP_LINE = "Citations nicht verfügbar — Zahl-Check übersprungen";
const LIBRARY_WARN = "Antwort ohne Library-Bezug — Ergebnis ungültig (Testmodus)";

export function parseZahl(raw: string): number | null {
  let value = raw.replace(/€/g, "").replace(/%/g, "").replace(/\beuro?\b/gi, "").replace(/\s/g, "");
  if (!value) return null;
  const lastComma = value.lastIndexOf(",");
  const lastDot = value.lastIndexOf(".");
  if (lastComma >= 0 && lastDot >= 0) {
    value = lastComma > lastDot ? value.replace(/\./g, "").replace(",", ".") : value.replace(/,/g, "");
  } else if (lastComma >= 0) {
    const fraction = value.slice(lastComma + 1);
    value = fraction.length <= 2 ? value.replace(",", ".") : value.replace(/,/g, "");
  } else if (lastDot >= 0 && /^\d{1,3}(?:\.\d{3})+$/.test(value)) {
    value = value.replace(/\./g, "");
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function gleicheZahl(links: number, rechts: number): boolean {
  return Math.abs(links - rechts) < 0.001;
}

const GELD_ZAHL = String.raw`\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+[.,]\d{1,2}|\d+`;
const GELD_MIT_WAEHRUNG = new RegExp(String.raw`(?:€|\beur(?:o)?\b)\s*(?:${GELD_ZAHL})|(?:${GELD_ZAHL})\s*(?:€|\beur(?:o)?\b)`, "gi");
const GELD_DEZIMAL = /(?<![\d.])\d+[.,]\d{1,2}(?!\s*(?:%|prozent)\b)(?![.\d])/gi;

export type GeldTreffer = { value: number; index: number; length: number };

function ueberschneidet(bereiche: Array<[number, number]>, start: number, ende: number): boolean {
  return bereiche.some(([links, rechts]) => start < rechts && ende > links);
}

export function geldTreffer(text: string): GeldTreffer[] {
  const gefunden: GeldTreffer[] = [];
  const belegt: Array<[number, number]> = [];
  for (const muster of [GELD_MIT_WAEHRUNG, GELD_DEZIMAL]) {
    for (const match of text.matchAll(muster)) {
      if (match.index == null) continue;
      const start = match.index;
      const ende = start + match[0].length;
      if (ueberschneidet(belegt, start, ende)) continue;
      if (/§\s*$/.test(text.slice(Math.max(0, start - 4), start))) continue;
      const value = parseZahl(match[0]);
      if (value == null) continue;
      belegt.push([start, ende]);
      gefunden.push({ value, index: start, length: match[0].length });
    }
  }
  return gefunden;
}

export function geldVorhanden(text: string, value: number): boolean {
  return geldTreffer(text).some((item) => gleicheZahl(item.value, value));
}

export function zahlVorhanden(text: string, value: number): boolean {
  return geldVorhanden(text, value);
}

function textstellen(ranges: Array<[number, number]>, text: string): string[] {
  const geordnet = [...ranges].sort((links, rechts) => links[0] - rechts[0]);
  const vereint: Array<[number, number]> = [];
  for (const bereich of geordnet) {
    const letzter = vereint[vereint.length - 1];
    if (letzter && bereich[0] <= letzter[1]) letzter[1] = Math.max(letzter[1], bereich[1]);
    else vereint.push([bereich[0], bereich[1]]);
  }
  return vereint
    .slice(0, 8)
    .map(([anfang, ende]) => text.slice(anfang, ende).replace(/\s+/g, " ").trim())
    .filter(Boolean);
}

export function textstellenUmBetraege(text: string, betraege: number[], radius = 160): string[] {
  if (!text.trim() || betraege.length === 0) return [];
  const bereiche = geldTreffer(text)
    .filter((treffer) => betraege.some((betrag) => gleicheZahl(betrag, treffer.value)))
    .map((treffer) => [Math.max(0, treffer.index - radius), Math.min(text.length, treffer.index + treffer.length + radius)] as [number, number]);
  return textstellen(bereiche, text);
}

export const SCHLUESSELBEGRIFFE = ["verpflegungsmehraufwand", "ehrenamtspauschale", "fahrtkosten", "grenze"];

export function zahlenAusFrage(frage: string): { betraege: number[]; prozente: number[] } {
  const betraege = new Set<string>();
  for (const item of euroAmounts(frage)) betraege.add(item.value.toFixed(2));
  const muster = /\b\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\b\d+[.,]\d{1,2}|\b\d{2,5}\b/g;
  for (const match of frage.matchAll(muster)) {
    if (match.index == null || /^(?:19|20)\d{2}$/.test(match[0])) continue;
    const danach = frage.slice(match.index + match[0].length, match.index + match[0].length + 8);
    if (/^\s*(?:%|prozent)/i.test(danach)) continue;
    const value = parseZahl(match[0]);
    if (value == null || value <= 0) continue;
    betraege.add(value.toFixed(2));
  }
  return {
    betraege: [...betraege].map(Number),
    prozente: prozentWerte(frage).map((item) => item.value),
  };
}

export function textstellenUmBegriffe(text: string, begriffe: string[], radius = 220): string[] {
  if (!text.trim() || begriffe.length === 0) return [];
  const hay = text.toLowerCase();
  const bereiche: Array<[number, number]> = [];
  for (const begriff of begriffe) {
    const needle = begriff.trim().toLowerCase();
    if (needle.length < 4) continue;
    let from = 0;
    let count = 0;
    while (count < 3) {
      const index = hay.indexOf(needle, from);
      if (index < 0) break;
      bereiche.push([Math.max(0, index - radius), Math.min(text.length, index + needle.length + radius)]);
      from = index + needle.length;
      count += 1;
    }
  }
  return textstellen(bereiche, text);
}

export function textstellenUmProzente(text: string, werte: number[], radius = 160): string[] {
  if (!text.trim() || werte.length === 0) return [];
  const bereiche = prozentWerte(text)
    .filter((treffer) => werte.some((wert) => gleicheZahl(wert, treffer.value)))
    .map((treffer) => [Math.max(0, treffer.index - radius), Math.min(text.length, treffer.index + treffer.length + radius)] as [number, number]);
  return textstellen(bereiche, text);
}

export function istInterneQuelle(name: string): boolean {
  return /prompt-v12(?:\.md)?/i.test(name);
}

export const INTERNE_FUNDSTELLE = "🔴 Ungültige Fundstelle: interne Datei";

export function prozentWerte(text: string): Array<{ label: string; value: number; index: number; length: number }> {
  const pattern = /\d+(?:[.,]\d+)?\s*%/g;
  const found: Array<{ label: string; value: number; index: number; length: number }> = [];
  for (const match of text.matchAll(pattern)) {
    const label = match[0].replace(/\s+/g, " ").trim();
    const value = parseZahl(label);
    if (value == null || !Number.isFinite(value) || match.index == null) continue;
    found.push({ label, value, index: match.index, length: match[0].length });
  }
  return found;
}

export function euroTreffer(text: string): Array<{ label: string; value: number; index: number; length: number }> {
  const pattern = /€\s*\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|€\s*\d+(?:[.,]\d+)?|\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?\s*€|\d+[.,]\d{1,2}\s*€|\d+(?:,\d{1,2})?\s*€/g;
  const found: Array<{ label: string; value: number; index: number; length: number }> = [];
  for (const match of text.matchAll(pattern)) {
    const label = match[0].replace(/\s+/g, " ").trim();
    const value = parseZahl(label);
    if (value == null || match.index == null) continue;
    found.push({ label, value, index: match.index, length: match[0].length });
  }
  return found;
}

export function euroAmounts(text: string): Array<{ label: string; value: number; index: number }> {
  const found: Array<{ label: string; value: number; index: number }> = [];
  const seen = new Set<string>();
  for (const item of euroTreffer(text)) {
    const key = item.value.toFixed(2);
    if (seen.has(key)) continue;
    seen.add(key);
    found.push(item);
  }
  return found;
}

function corpusValues(corpus: string): Set<string> {
  return new Set(geldTreffer(corpus).map((item) => item.value.toFixed(2)));
}

export function matchedDocuments(answer: string, documentNames: string[]): string[] {
  const found: string[] = [];
  for (const name of documentNames) {
    if (istInterneQuelle(name)) continue;
    if (answer.toLowerCase().includes(name.toLowerCase())) {
      found.push(name);
      continue;
    }
    const info = name.match(/info[_ -]?(\d+)/i);
    if (info && new RegExp(`info\\s*[_-]?\\s*${info[1]}\\b`, "i").test(answer)) {
      found.push(name);
      continue;
    }
    const stem = name.replace(/\.[a-z0-9]+$/i, "").toLowerCase().replace(/[_-]+/g, " ");
    const hay = answer.toLowerCase().replace(/[_-]+/g, " ");
    if (stem.length >= 4 && hay.includes(stem)) found.push(name);
  }
  return [...new Set(found)].sort();
}

export function pruefeAntwort(input: {
  answer: string;
  zahlText?: string;
  documentNames: string[];
  citationsField: boolean;
  passages: string[];
  citationLabels: string[];
}): RagPruefung {
  const material = input.passages.map((item) => item.trim()).filter(Boolean);
  const canCheckNumbers = input.citationsField || material.length > 0;
  let zahlen: ZahlenPruefung;
  if (!canCheckNumbers) {
    zahlen = { status: "uebersprungen", checked: 0, lines: [SKIP_LINE] };
  } else {
    const amounts = euroAmounts(input.zahlText ?? input.answer);
    const known = corpusValues(material.join("\n"));
    const warnings = amounts
      .filter((amount) => !known.has(amount.value.toFixed(2)))
      .map((amount) => `⚠️ Zahl ohne Fundstelle: ${amount.label}`);
    zahlen = warnings.length > 0
      ? { status: "warnung", checked: amounts.length, lines: warnings }
      : { status: "bestanden", checked: amounts.length, lines: [] };
  }

  const documents = matchedDocuments([input.answer, ...input.citationLabels].join("\n"), input.documentNames);
  const library: LibraryPruefung = documents.length > 0
    ? { ok: true, documents, line: `Library-Bezug: ${documents.join(", ")}` }
    : { ok: false, documents: [], line: LIBRARY_WARN };
  const interne = istInterneQuelle([input.answer, ...input.citationLabels].join("\n")) ? INTERNE_FUNDSTELLE : null;

  return { zahlen, library, interne };
}
```

### `src/lib/mistral/abschnitte.ts`

```ts
import { euroAmounts, euroTreffer, gleicheZahl, matchedDocuments, parseZahl, prozentWerte, zahlVorhanden } from "@/lib/mistral/rag-pruefung";
import { stehtInListe, type Grenze, type ZahlenListe } from "@/lib/mistral/zahlen-werte";

export type AntwortAbschnitte = {
  kernaussagen: string;
  zahlen: string;
  nutzerangaben: string;
  fundstellen: string;
  luecken: string;
  vollstaendig: boolean;
};

const HEADING = /(?:^|\n)[ \t]*#{0,3}[ \t]*(?:\*\*|__)?[ \t]*(KERNAUSSAGEN|ZAHLEN|NUTZERANGABEN-PR(?:Ü|UE)FUNG|FUNDSTELLEN|L(?:Ü|UE)CKEN)[ \t]*(?:\*\*|__)?[ \t]*:/gi;

function keyOf(heading: string): keyof Omit<AntwortAbschnitte, "vollstaendig"> | null {
  const name = heading.toUpperCase().replace("UE", "Ü");
  if (name === "KERNAUSSAGEN") return "kernaussagen";
  if (name === "ZAHLEN") return "zahlen";
  if (name.startsWith("NUTZERANGABEN")) return "nutzerangaben";
  if (name === "FUNDSTELLEN") return "fundstellen";
  if (name === "LÜCKEN" || name === "LUECKEN") return "luecken";
  return null;
}

export function parseAbschnitte(answer: string): AntwortAbschnitte {
  const sections: AntwortAbschnitte = {
    kernaussagen: "",
    zahlen: "",
    nutzerangaben: "",
    fundstellen: "",
    luecken: "",
    vollstaendig: false,
  };
  const marks: Array<{ key: keyof Omit<AntwortAbschnitte, "vollstaendig">; start: number; end: number }> = [];
  for (const match of answer.matchAll(HEADING)) {
    const key = keyOf(match[1] ?? "");
    if (!key || match.index == null) continue;
    marks.push({ key, start: match.index, end: match.index + match[0].length });
  }
  for (let index = 0; index < marks.length; index += 1) {
    const mark = marks[index];
    const next = marks[index + 1]?.start ?? answer.length;
    sections[mark.key] = answer.slice(mark.end, next).trim();
  }
  sections.vollstaendig = Boolean(sections.kernaussagen || marks.some((mark) => mark.key === "kernaussagen"))
    && marks.some((mark) => mark.key === "zahlen")
    && marks.some((mark) => mark.key === "nutzerangaben")
    && marks.some((mark) => mark.key === "fundstellen")
    && marks.some((mark) => mark.key === "luecken");
  return sections;
}

function jahrDavor(line: string, index: number): number | null {
  const before = line.slice(Math.max(0, index - 24), index);
  const match = before.match(/(?:für|in|ab|seit)\s+((?:19|20)\d{2})\s*:\s*$/i);
  return match ? Number(match[1]) : null;
}

function jahrDanach(line: string, end: number): number | null {
  const after = line.slice(end, end + 36);
  const match = after.match(/^\s*(?:€)?\s*(?:für|im Jahr)\s+((?:19|20)\d{2})\b/i);
  if (!match) return null;
  const rest = after.slice(match[0].length);
  if (/^\s*:/.test(rest)) return null;
  return Number(match[1]);
}

export function grenzenAusText(text: string): Grenze[] {
  const grenzen: Grenze[] = [];
  for (const line of text.split(/\n/)) {
    const euros = euroTreffer(line).map((item) => ({ ...item, unit: "euro" as const }));
    const prozente = prozentWerte(line).map((item) => ({ ...item, unit: "prozent" as const }));
    for (const item of [...euros, ...prozente].sort((a, b) => a.index - b.index)) {
      const jahr = jahrDavor(line, item.index) ?? jahrDanach(line, item.index + item.length);
      grenzen.push({ value: item.value, unit: item.unit, jahr, label: item.label });
    }
  }
  return grenzen;
}

const NAECHSTE_UEBERSCHRIFT = String.raw`\n[ \t]*#{0,3}[ \t]*(?:\*\*|__)?[ \t]*(?:NUTZERANGABEN-PR(?:Ü|UE)FUNG|FUNDSTELLEN|L(?:Ü|UE)CKEN|KERNAUSSAGEN)[ \t]*(?:\*\*|__)?[ \t]*:`;

export function fehlendeBetragszeilen(answer: string, zeilen: string[], relevante: number[]): string[] {
  const sections = parseAbschnitte(answer);
  const vorhanden = euroAmounts(sections.zahlen || (sections.vollstaendig ? "" : answer));
  return zeilen.filter((zeile) => {
    const betrag = euroAmounts(zeile)[0];
    if (!betrag) return false;
    if (!relevante.some((wert) => gleicheZahl(wert, betrag.value))) return false;
    return !vorhanden.some((item) => gleicheZahl(item.value, betrag.value));
  });
}

export function zahlenAusNachfrage(text: string, erlaubt: string[]): string | null {
  const werte = erlaubt.flatMap((zeile) => euroAmounts(zeile).map((item) => item.value));
  const behalten = text.split(/\n/).map((zeile) => zeile.trim()).filter((zeile) => {
    const betraege = euroAmounts(zeile);
    return betraege.some((betrag) => werte.some((wert) => gleicheZahl(wert, betrag.value)));
  });
  return behalten.length > 0 ? behalten.join("\n") : null;
}

export function ergaenzeZahlen(answer: string, zusatz: string): string {
  const extra = zusatz.trim();
  if (!extra) return answer;
  const sections = parseAbschnitte(answer);
  const hatBetrag = euroAmounts(sections.zahlen).length > 0;
  let text = answer;
  if (!/ZAHLEN\s*:/i.test(text)) text = `${text.trim()}\n\nZAHLEN:\n${extra}`;
  else if (!hatBetrag) {
    text = text.replace(
      new RegExp(String.raw`ZAHLEN\s*:\s*[\s\S]*?(?=${NAECHSTE_UEBERSCHRIFT}|$)`, "i"),
      `ZAHLEN:\n${extra}\n\n`,
    );
  } else text = text.replace(/ZAHLEN\s*:/i, (heading) => `${heading}\n${extra}`);
  const namen = [...new Set(extra.split("\n").map((zeile) => zeile.split("|")[1]?.trim() ?? "").filter((name) => name.length >= 4))];
  const fundstellen = parseAbschnitte(text).fundstellen.toLowerCase();
  const fehlend = namen.filter((name) => !fundstellen.includes(name.toLowerCase()));
  if (fehlend.length === 0 || !/FUNDSTELLEN\s*:/i.test(text)) return text;
  return text.replace(/FUNDSTELLEN\s*:/i, (heading) => `${heading}\n${fehlend.map((name) => `- ${name}`).join("\n")}`);
}

export function nenntKeineZahlen(answer: string): boolean {
  const sections = parseAbschnitte(answer);
  const quelle = sections.vollstaendig ? sections.zahlen : answer.replace(sections.nutzerangaben, " ");
  if (euroAmounts(quelle).length > 0) return false;
  if (/keine\s+zahlen/i.test(answer)) return true;
  return sections.vollstaendig;
}

export function grenzenAusAntwort(answer: string): Grenze[] {
  const sections = parseAbschnitte(answer);
  if (sections.vollstaendig || sections.zahlen) return grenzenAusText(sections.zahlen);
  return grenzenAusText(sections.nutzerangaben ? answer.replace(sections.nutzerangaben, " ") : answer);
}

function corpusHasProzent(corpus: string, value: number): boolean {
  const pattern = /\d+(?:[.,]\d+)?\s*(?:%|prozent)/gi;
  for (const match of corpus.matchAll(pattern)) {
    const parsed = parseZahl(match[0]);
    if (parsed != null && Math.abs(parsed - value) < 0.001) return true;
  }
  return false;
}

function corpusHas(corpus: string, value: number): boolean {
  return zahlVorhanden(corpus, value);
}

export function pruefeBestaetigt(nutzerangaben: string, corpus: string, pruefer: string): { text: string; hinweise: string[] } {
  const hinweise: string[] = [];
  const text = nutzerangaben.split(/\n/).map((line) => {
    if (!/bestätigt/i.test(line)) return line;
    const zahlen = [
      ...euroAmounts(line).map((item) => ({ label: item.label, belegt: corpusHas(corpus, item.value) })),
      ...prozentWerte(line).map((item) => ({ label: item.label, belegt: corpusHasProzent(corpus, item.value) })),
    ];
    if (zahlen.length === 0) {
      const links = line.includes("|") ? line.split("|")[0].trim() : line.trim();
      return `${links} | Regel bestätigt, Zahl unbelegt`;
    }
    const fehlend = zahlen.filter((item) => !item.belegt);
    if (fehlend.length === 0) return line;
    for (const zahl of fehlend) hinweise.push(`⚠️ Ungültiges "bestätigt": ${zahl.label} (${pruefer})`);
    const links = line.includes("|") ? line.split("|")[0].trim() : line.trim();
    return `${links} | nicht belegt`;
  }).join("\n");
  return { text, hinweise };
}

export function dokumentZahlen(input: {
  answer: string;
  corpus: string;
  documentNames: string[];
  prueferLabel: string;
  liste?: ZahlenListe;
}): {
  keys: string[];
  labels: string[];
  documents: string[];
  nutzerangaben: string;
  hinweise: string[];
} {
  const sections = parseAbschnitte(input.answer);
  const hinweise: string[] = [];
  const pruefer = input.prueferLabel.match(/Prüfer\s+\d+/)?.[0] ?? input.prueferLabel;
  const corpus = input.corpus.trim();
  let source = sections.zahlen;
  if (!sections.vollstaendig) {
    hinweise.push(`⚠️ Antwortformat von ${pruefer} abweichend — Rückfall-Extraktion verwendet`);
    source = sections.nutzerangaben
      ? input.answer.replace(sections.nutzerangaben, " ")
      : input.answer;
  }
  const kept: Array<{ label: string; value: number }> = [];
  for (const amount of euroAmounts(source)) {
    const unbekannt = Boolean(input.liste) && !stehtInListe(amount.value, "euro", input.liste as ZahlenListe);
    if (corpus && !corpusHas(corpus, amount.value) && unbekannt) {
      hinweise.push(`🔴 Unbekannter Wert: ${amount.label} (${pruefer})`);
      continue;
    }
    if (corpus && !corpusHas(corpus, amount.value)) {
      hinweise.push(`⚠️ Zahl im ZAHLEN-Abschnitt ohne Beleg: ${amount.label} (${pruefer})`);
      continue;
    }
    kept.push(amount);
  }
  const fundstellenText = sections.fundstellen || (sections.vollstaendig ? "" : input.answer);
  const bestaetigt = pruefeBestaetigt(sections.nutzerangaben, corpus, pruefer);
  hinweise.push(...bestaetigt.hinweise);
  return {
    keys: kept.map((item) => item.value.toFixed(2)),
    labels: kept.map((item) => item.label),
    documents: matchedDocuments(fundstellenText, input.documentNames),
    nutzerangaben: bestaetigt.text,
    hinweise,
  };
}
```

### `src/lib/mistral/chunks.ts`

```ts
import { geldTreffer, istInterneQuelle } from "@/lib/mistral/rag-pruefung";

export type ChunkBeleg = {
  id: string;
  dokument: string;
  seite: string | null;
  text: string;
};

function textVon(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function seiteVon(record: Record<string, unknown>): string | null {
  const meta = record.metadata;
  const quellen = [record];
  if (meta && typeof meta === "object") quellen.push(meta as Record<string, unknown>);
  for (const quelle of quellen) {
    for (const [key, value] of Object.entries(quelle)) {
      if (!/page|seite/i.test(key)) continue;
      if (typeof value === "number" && Number.isFinite(value)) return String(value);
      if (typeof value === "string" && value.trim()) return value.trim();
    }
  }
  return null;
}

function dokumentVon(record: Record<string, unknown>): string {
  for (const key of ["title", "document_name", "documentName", "filename", "file_name", "name"]) {
    const value = textVon(record[key]);
    if (value && !/^(document_library|web_search|library_search)$/i.test(value)) return value;
  }
  return "";
}

function schnipsel(record: Record<string, unknown>): Array<{ text: string; seite: string | null }> {
  const roh = record.snippets ?? record.snippet;
  if (!Array.isArray(roh)) return [];
  return roh.flatMap((item) => {
    if (typeof item === "string" && item.trim()) return [{ text: item.trim(), seite: null }];
    if (!item || typeof item !== "object") return [];
    const objekt = item as Record<string, unknown>;
    const text = textVon(objekt.content) || textVon(objekt.text) || textVon(objekt.snippet);
    return text ? [{ text, seite: seiteVon(objekt) }] : [];
  });
}

function textDesChunks(record: Record<string, unknown>): string {
  const teile = schnipsel(record);
  if (teile.length > 0) return teile.map((teil) => teil.text).join("\n");
  for (const key of ["content", "text", "description"]) {
    const value = textVon(record[key]);
    if (value) return value;
  }
  return "";
}

function siehtAusWieChunk(record: Record<string, unknown>): boolean {
  const hatSnippet = Array.isArray(record.snippets) || Array.isArray(record.snippet) || Boolean(textVon(record.content));
  return Boolean(dokumentVon(record) && (hatSnippet || textVon(record.description) || textVon(record.text)));
}

function zuChunks(record: Record<string, unknown>, idHinweis: string): ChunkBeleg[] {
  const dokument = dokumentVon(record);
  const id = textVon(record.id) || textVon(record.url) || idHinweis;
  const teile = schnipsel(record);
  if (teile.length > 0 && teile.some((teil) => teil.seite)) {
    return teile.map((teil, index) => ({
      id: `${id}:${index}`,
      dokument: dokument || id,
      seite: teil.seite ?? seiteVon(record),
      text: teil.text,
    }));
  }
  const text = teile.map((teil) => teil.text).join("\n") || textDesChunks(record);
  if (!dokument && !text) return [];
  return [{ id, dokument: dokument || id, seite: seiteVon(record), text }];
}

function walkChunks(value: unknown, gefunden: ChunkBeleg[], tiefe: number): void {
  if (tiefe > 8 || value == null) return;
  if (typeof value === "string") {
    try {
      walkChunks(JSON.parse(value) as unknown, gefunden, tiefe + 1);
    } catch {
      // Kein JSON.
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) walkChunks(item, gefunden, tiefe + 1);
    return;
  }
  if (typeof value !== "object") return;
  const record = value as Record<string, unknown>;
  for (const [key, nested] of Object.entries(record)) {
    if (key === "result" && typeof nested === "string") {
      walkChunks(nested, gefunden, tiefe + 1);
      continue;
    }
    if (nested && typeof nested === "object" && !Array.isArray(nested) && siehtAusWieChunk(nested as Record<string, unknown>)) {
      gefunden.push(...zuChunks(nested as Record<string, unknown>, key));
      continue;
    }
    if (nested && typeof nested === "object") walkChunks(nested, gefunden, tiefe + 1);
  }
}

export function chunksAusWert(value: unknown): ChunkBeleg[] {
  const gefunden: ChunkBeleg[] = [];
  walkChunks(value, gefunden, 0);
  const eigene = new Map<string, ChunkBeleg>();
  for (const chunk of gefunden) {
    const schluessel = `${chunk.id}|${chunk.dokument}|${chunk.seite ?? ""}|${chunk.text.slice(0, 80)}`;
    if (!eigene.has(schluessel)) eigene.set(schluessel, chunk);
  }
  return [...eigene.values()];
}

export function kurzName(dokument: string): string {
  const info = dokument.match(/info[_ -]?(\d+)/i);
  if (info) return `Info_${info[1]}`;
  return dokument.replace(/\.pdf$/i, "");
}

export function chunkZeile(chunks: ChunkBeleg[]): string {
  if (chunks.length === 0) return "keine";
  const gruppen = new Map<string, { seiten: string[]; ids: string[] }>();
  for (const chunk of chunks) {
    const name = kurzName(chunk.dokument);
    const gruppe = gruppen.get(name) ?? { seiten: [], ids: [] };
    const seite = chunk.seite ? `Seite ${chunk.seite}` : "";
    if (seite && !gruppe.seiten.includes(seite)) gruppe.seiten.push(seite);
    if (chunk.id && !gruppe.ids.includes(chunk.id)) gruppe.ids.push(chunk.id);
    gruppen.set(name, gruppe);
  }
  return [...gruppen].map(([name, gruppe]) => {
    const kopf = gruppe.seiten.length > 0 ? `${name}, ${gruppe.seiten.join(" / ")}` : name;
    if (gruppe.seiten.length > 0 || gruppe.ids.length === 0) return kopf;
    const ids = gruppe.ids.map((id) => id.length > 12 ? id.slice(0, 8) : id).join(", ");
    return `${kopf} · ${ids}`;
  }).join(" / ");
}

export function chunkSignatur(chunks: ChunkBeleg[]): string {
  return chunks
    .map((chunk) => `${chunk.id}|${kurzName(chunk.dokument)}|${chunk.seite ?? ""}`)
    .sort()
    .join(";");
}

export function dokumentbasisWarnung(rows: Array<{ label: string; chunks: ChunkBeleg[] }>): string | null {
  const antworten = rows.filter((row) => row.chunks);
  if (antworten.length < 2) return null;
  const signaturen = new Set(antworten.map((row) => chunkSignatur(row.chunks)));
  if (signaturen.size <= 1) return null;
  const teile = antworten.map((row) => {
    const pruefer = row.label.match(/Prüfer\s+\d+/)?.[0] ?? row.label;
    return `${pruefer} erhielt ${row.chunks.length} Chunks`;
  });
  return `⚠️ Uneinheitliche Dokumentbasis: ${teile.join(", ")} — Retrieval variiert, Konsens verzerrend.`;
}

export function ohneInterneChunks(chunks: ChunkBeleg[]): ChunkBeleg[] {
  return chunks.filter((chunk) => !istInterneQuelle(chunk.dokument) && !istInterneQuelle(chunk.id));
}

function euroZeile(value: number): string {
  if (Number.isInteger(value)) return `${String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ".")} €`;
  return `${value.toFixed(2).replace(".", ",")} €`;
}

export function betraegeImText(chunks: ChunkBeleg[]): string[] {
  const zeilen: string[] = [];
  const gesehen = new Set<string>();
  for (const chunk of chunks) {
    for (const treffer of geldTreffer(chunk.text)) {
      const zeile = `${euroZeile(treffer.value)} in ${kurzName(chunk.dokument)}`;
      if (gesehen.has(zeile)) continue;
      gesehen.add(zeile);
      zeilen.push(zeile);
    }
  }
  return zeilen.slice(0, 20);
}

export function stellenBlock(chunks: ChunkBeleg[]): string {
  const betraege = betraegeImText(chunks);
  const kopf = betraege.length > 0
    ? `## Beträge wörtlich in den Dokumentstellen\n${betraege.map((zeile) => `- ${zeile}`).join("\n")}\n\n`
    : "";
  const teile = chunks.slice(0, 12).map((chunk, index) => {
    const name = [kurzName(chunk.dokument), chunk.seite ? `Seite ${chunk.seite}` : ""].filter(Boolean).join(", ");
    return `### Stelle ${index + 1}: ${name}\n${chunk.text.trim().slice(0, 2500)}`;
  });
  return `${kopf}## Dokumentstellen (identisch für alle Prüfer, vom System abgerufen)\n${teile.join("\n\n")}`;
}
```

### `src/lib/mistral/fundstellen.ts`

```ts
function cleanLine(line: string): string {
  return line.replace(/^[-*•\d.)\s]+/, "").replace(/\*+/g, "").replace(/__/g, "").trim();
}

function firstString(record: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

export function formatCitation(item: unknown): string {
  if (typeof item === "string") return cleanLine(item);
  if (!item || typeof item !== "object") return "";
  const record = item as Record<string, unknown>;
  const nested = record.document ?? record.source ?? record.file;
  const nestedName = nested && typeof nested === "object"
    ? firstString(nested as Record<string, unknown>, ["name", "title", "filename", "file_name", "document_name"])
    : "";
  const name = firstString(record, ["document_name", "documentName", "filename", "file_name", "fileName", "title", "name", "source"]) || nestedName;
  if (!name) return "";
  const section = firstString(record, ["section", "abschnitt", "heading"]);
  const page = record.page ?? record.page_number ?? record.pageNumber;
  if (section) return `${name}, Abschnitt ${section}`;
  if (typeof page === "number" || (typeof page === "string" && page.trim())) return `${name}, Seite ${page}`;
  return name;
}

export function citationsFromResponse(value: unknown, found: string[] = [], depth = 0): string[] {
  if (depth > 8 || value == null) return found;
  if (Array.isArray(value)) {
    for (const item of value) citationsFromResponse(item, found, depth + 1);
    return found;
  }
  if (typeof value !== "object") return found;
  const record = value as Record<string, unknown>;
  if (Array.isArray(record.citations)) {
    for (const item of record.citations) {
      const label = formatCitation(item);
      if (label) found.push(label);
    }
  }
  for (const [key, nested] of Object.entries(record)) {
    if (key === "citations") continue;
    if (nested && typeof nested === "object") citationsFromResponse(nested, found, depth + 1);
  }
  return found;
}

function inlineFundstellen(answer: string): string[] {
  return [...answer.matchAll(/Fundstelle[n]?\s*:\s*([^)\n]+)/gi)]
    .map((match) => cleanLine(match[1] ?? ""))
    .filter((line) => line.length > 1 && !/^keine\b/i.test(line));
}

export function fundstellenFromAnswer(answer: string): string[] {
  const match = answer.match(/(?:^|\n)\s*(?:\*\*|__)?Fundstellen?(?:\*\*|__)?\s*:?\s*([\s\S]*)$/i);
  const fromSection = match?.[1]
    ? match[1]
      .split(/\n+/)
      .flatMap((line) => line.split(/\s*;\s*/))
      .map(cleanLine)
      .filter((line) => line.length > 1 && !/^keine\b/i.test(line))
    : [];
  const lines = fromSection.length > 0 ? fromSection : inlineFundstellen(answer);
  return [...new Set(lines)];
}

export function visibleFundstellen(answer: string, sources: string[]): string[] {
  const structured = sources.map((item) => item.trim()).filter(Boolean);
  const lines = structured.length > 0 ? structured : fundstellenFromAnswer(answer);
  return [...new Set(lines)];
}
```

### `src/lib/zahlen-register.ts`

```ts
import { readFileSync } from "node:fs";
import path from "node:path";
import { getDb, korrigiereImportfreigaben } from "@/lib/db";
import { istBerechnungskennung, type RegisterSnapshot } from "@/lib/register-kennungen";

export type Freigabe = "entwurf" | "freigegeben";
export type Einheit = "euro" | "prozent" | "hinweis";

export type RegisterEintrag = {
  id: string;
  gruppe: string;
  version: number;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  einheit: Einheit;
  gueltigAb: string;
  gueltigBis: string | null;
  quelle: string;
  fundstelle: string | null;
  dokumentstand: string | null;
  anwendungsbereich: string | null;
  freigabe: Freigabe;
  freigabeNachweis: string | null;
  herkunft: string | null;
  beschreibung: string;
  thema: string | null;
  stichworte: string[];
  bedingung: string | null;
  createdAt: string;
};

export type WertEingabe = {
  gruppe: string;
  beschreibung?: string;
  betrag: string;
  einheit: "euro" | "prozent";
  gueltigAb: string;
  gueltigBis: string | null;
  quelle?: string;
  fundstelle?: string;
  dokumentstand?: string;
  anwendungsbereich?: string;
  thema?: string;
  stichworte?: string[];
  bedingung?: string;
};

export type Auswahl =
  | { ok: true; eintrag: RegisterEintrag }
  | { ok: false; grund: "fehlt" | "mehrdeutig" | "unbekannt" | "einheit"; meldung: string };

type SqlZeile = {
  id: string;
  gruppe: string;
  version: number;
  betrag: number | null;
  einheit: string;
  gueltig_ab: string;
  gueltig_bis: string | null;
  quelle: string;
  freigabe: string;
  beschreibung: string;
  thema: string | null;
  stichworte_json: string | null;
  bedingung: string | null;
  created_at: string;
  wert_cent: number | null;
  wert_exakt: string | null;
  wert_bps: number | null;
  anwendungsbereich: string | null;
  fundstelle: string | null;
  dokumentstand: string | null;
  freigabe_nachweis: string | null;
  herkunft: string | null;
};

type VorlageZeile = {
  gruppe: string;
  beschreibung: string;
  quelle: string;
  thema: string | null;
  stichworte: string[];
  bedingung: string | null;
  einheit: Einheit;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  gueltigAb: string;
  gueltigBis: string | null;
};

const DATE = /^\d{4}-\d{2}-\d{2}$/;
const KENNUNG = /^[a-z][a-z0-9_]{1,63}$/;
const OFFEN = "9999-12-31";

const VOLLSTAENDIGKEIT = "Vollständigkeit der Angaben geprüft. Keine Aussage zur fachlichen Richtigkeit.";

export function zahlenWertePfad(): string {
  return path.join(process.cwd(), "daten", "zahlen-werte.json");
}

export function parseWert(einheit: "euro" | "prozent", raw: string): { wertExakt: string; wertCent: number | null; wertBps: number | null } {
  const text = raw.trim().replace(/\s/g, "").replace("€", "").replace("%", "");
  if (!/^\d+(?:[.,]\d+)?$/.test(text)) {
    throw new Error("Der Wert muss eine positive Zahl mit Punkt oder Komma sein.");
  }
  const [wholeRaw, fracRaw = ""] = text.replace(",", ".").split(".");
  if (fracRaw.length > 2) {
    throw new Error(einheit === "euro"
      ? "Geldbeträge dürfen höchstens zwei Nachkommastellen haben. Es wird nicht mit Fließkomma gerundet."
      : "Sätze dürfen höchstens zwei Nachkommastellen haben, damit sie in Basispunkten aufgehen.");
  }
  const whole = wholeRaw.replace(/^0+(?=\d)/, "");
  if (einheit === "euro") {
    const cents = Number(`${whole}${fracRaw.padEnd(2, "0")}`);
    if (!Number.isSafeInteger(cents) || cents <= 0) {
      throw new Error("Der Geldbetrag muss größer als 0 Cent sein und in eine Ganzzahl passen.");
    }
    return { wertExakt: `${whole}.${fracRaw.padEnd(2, "0")}`, wertCent: cents, wertBps: null };
  }
  const bps = Number(`${whole}${fracRaw.padEnd(2, "0")}`);
  if (!Number.isSafeInteger(bps) || bps <= 0 || bps > 10000) {
    throw new Error("Der Satz muss größer als 0 und höchstens 100 Prozent sein.");
  }
  const frac = fracRaw.replace(/0+$/, "");
  return { wertExakt: frac.length === 0 ? whole : `${whole}.${frac}`, wertCent: null, wertBps: bps };
}

export function snapshotVon(eintrag: RegisterEintrag): RegisterSnapshot {
  return {
    id: eintrag.id,
    kennung: eintrag.gruppe,
    anwendungsbereich: eintrag.anwendungsbereich,
    wertExakt: eintrag.wertExakt,
    wertCent: eintrag.wertCent,
    wertBps: eintrag.wertBps,
    einheit: eintrag.einheit,
    gueltigAb: eintrag.gueltigAb,
    gueltigBis: eintrag.gueltigBis,
    quelle: eintrag.quelle,
    fundstelle: eintrag.fundstelle,
    dokumentstand: eintrag.dokumentstand,
    freigabe: eintrag.freigabe,
  };
}

export function importiereVorlage(file = zahlenWertePfad()): void {
  korrigiereImportfreigaben();
  const zeilen = liesVorlageZeilen(file);
  const database = getDb();
  const existing = database.prepare("SELECT * FROM zahlen_register").all() as SqlZeile[];
  const backfills: Array<{ row: SqlZeile; zeile: VorlageZeile }> = [];
  const pending: VorlageZeile[] = [];
  for (const zeile of zeilen) {
    const match = existing.find((row) => gleicheVorlage(row, zeile));
    if (!match) {
      pending.push(zeile);
      continue;
    }
    if (!match.freigabe_nachweis && !match.wert_exakt && zeile.wertExakt) backfills.push({ row: match, zeile });
  }
  if (pending.length === 0 && backfills.length === 0) return;
  const stamp = new Date().toISOString();
  database.exec("BEGIN IMMEDIATE");
  try {
    const revision = database.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
      VALUES (?, ?, 'exaktwert_gesetzt', ?, ?, ?)`);
    const fill = database.prepare(`UPDATE zahlen_register
      SET wert_exakt = ?, wert_cent = ?, wert_bps = ?, herkunft = COALESCE(herkunft, 'import')
      WHERE id = ? AND freigabe_nachweis IS NULL AND wert_exakt IS NULL`);
    for (const item of backfills) {
      revision.run(crypto.randomUUID(), item.row.id, JSON.stringify(item.row), "Exakter Wert aus der JSON-Vorlage ergänzt. Betrag und Gültigkeit bleiben unverändert.", stamp);
      fill.run(item.zeile.wertExakt, item.zeile.wertCent, item.zeile.wertBps, item.row.id);
    }
    const insert = database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'entwurf', ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, 'import')`);
    for (const zeile of pending) {
      const version = naechsteVersion(zeile.gruppe);
      insert.run(
        `import:${zeile.gruppe}:${zeile.gueltigAb}:${zeile.wertExakt ?? "hinweis"}`,
        zeile.gruppe,
        version,
        zeile.einheit,
        zeile.gueltigAb,
        zeile.gueltigBis,
        zeile.quelle,
        zeile.beschreibung,
        zeile.thema,
        JSON.stringify(zeile.stichworte),
        zeile.bedingung,
        stamp,
        zeile.wertCent,
        zeile.wertExakt,
        zeile.wertBps,
        zeile.beschreibung,
      );
    }
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    if (istUnique(error)) return;
    throw error;
  }
}

export function ladeEintraege(): RegisterEintrag[] {
  importiereVorlage();
  const rows = getDb().prepare("SELECT * FROM zahlen_register ORDER BY gruppe, version, gueltig_ab").all() as SqlZeile[];
  return rows.map(mapEintrag);
}

export function ladeFreigegebene(): RegisterEintrag[] {
  return ladeEintraege().filter((eintrag) => eintrag.freigabe === "freigegeben" && eintrag.freigabeNachweis);
}

export function legeEntwurfAn(input: WertEingabe): RegisterEintrag {
  const geprueft = pruefeEntwurf(input);
  const database = getDb();
  const id = crypto.randomUUID();
  const stamp = new Date().toISOString();
  database.exec("BEGIN IMMEDIATE");
  try {
    const meta = letzteZeile(geprueft.gruppe);
    const version = naechsteVersion(geprueft.gruppe);
    database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'entwurf', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'entwurf')`).run(
      id,
      geprueft.gruppe,
      version,
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle || meta?.quelle || "",
      geprueft.beschreibung || meta?.beschreibung || geprueft.gruppe,
      geprueft.thema ?? meta?.thema ?? null,
      JSON.stringify(geprueft.stichworte ?? (meta ? stichworte(meta) : [])),
      geprueft.bedingung ?? meta?.bedingung ?? null,
      stamp,
      geprueft.wertCent,
      geprueft.wertExakt,
      geprueft.wertBps,
      blank(geprueft.anwendungsbereich),
      blank(geprueft.fundstelle),
      blank(geprueft.dokumentstand),
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return eintragOderFehler(id);
}

export function bearbeiteEntwurf(id: string, input: WertEingabe): RegisterEintrag {
  const geprueft = pruefeEntwurf(input);
  const database = getDb();
  database.exec("BEGIN IMMEDIATE");
  try {
    const row = database.prepare("SELECT * FROM zahlen_register WHERE id = ?").get(id) as SqlZeile | undefined;
    if (!row) throw new Error("Den Entwurf gibt es nicht.");
    if (row.freigabe !== "entwurf") throw new Error("Freigegebene Werte werden nicht überschrieben. Legen Sie eine neue Version an.");
    schreibeRevision(database, row, "entwurf_bearbeitet", "Entwurf geändert. Andere Zeilen und ihre Gültigkeit bleiben unverändert.");
    database.prepare(`UPDATE zahlen_register SET
        wert_exakt = ?, wert_cent = ?, wert_bps = ?, einheit = ?, gueltig_ab = ?, gueltig_bis = ?,
        quelle = ?, anwendungsbereich = ?, fundstelle = ?, dokumentstand = ?, beschreibung = ?, bedingung = ?
      WHERE id = ? AND freigabe = 'entwurf'`).run(
      geprueft.wertExakt,
      geprueft.wertCent,
      geprueft.wertBps,
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle || row.quelle,
      blank(geprueft.anwendungsbereich) ?? row.anwendungsbereich,
      blank(geprueft.fundstelle) ?? row.fundstelle,
      blank(geprueft.dokumentstand) ?? row.dokumentstand,
      geprueft.beschreibung || row.beschreibung,
      geprueft.bedingung ?? row.bedingung,
      id,
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return eintragOderFehler(id);
}

export function gebeFrei(input: WertEingabe & { abbruchNachSchreiben?: boolean }): RegisterEintrag {
  const geprueft = pruefeFreigabe(input);
  const database = getDb();
  const id = crypto.randomUUID();
  const stamp = new Date().toISOString();
  const nachweis = JSON.stringify({
    art: "vollstaendigkeit",
    hinweis: VOLLSTAENDIGKEIT,
    quelle: geprueft.quelle,
    fundstelle: geprueft.fundstelle,
    dokumentstand: geprueft.dokumentstand,
    anwendungsbereich: geprueft.anwendungsbereich,
    gueltigAb: geprueft.gueltigAb,
    gueltigBis: geprueft.gueltigBis,
    zeit: stamp,
  });
  database.exec("BEGIN IMMEDIATE");
  try {
    const vorhanden = findeGleicheFreigabe(geprueft);
    if (vorhanden) {
      database.exec("COMMIT");
      return vorhanden;
    }
    const approved = database.prepare(`SELECT * FROM zahlen_register
      WHERE gruppe = ? AND freigabe = 'freigegeben' AND anwendungsbereich = ?`).all(geprueft.gruppe, geprueft.anwendungsbereich) as SqlZeile[];
    const overlapping = approved.filter((row) => ueberlappt(row.gueltig_ab, row.gueltig_bis, geprueft.gueltigAb, geprueft.gueltigBis));
    const closable = overlapping.filter((row) => row.gueltig_bis == null && row.gueltig_ab < geprueft.gueltigAb);
    const blocked = overlapping.filter((row) => !closable.some((item) => item.id === row.id));
    if (blocked.length > 0 || closable.length > 1) {
      throw new Error(konfliktMeldung(geprueft.gruppe, geprueft.anwendungsbereich, geprueft.gueltigAb, geprueft.gueltigBis));
    }
    if (closable.length === 1) {
      const ende = tagDavor(geprueft.gueltigAb);
      if (ende < closable[0].gueltig_ab) throw new Error("Die Ablösung würde den bisherigen Zeitraum umkehren.");
      schreibeRevision(database, closable[0], "abloesung", "Gültig-bis wird zur Ablösung gesetzt. Der vorherige Zustand bleibt in der Revision.");
      database.prepare("UPDATE zahlen_register SET gueltig_bis = ? WHERE id = ? AND freigabe = 'freigegeben' AND gueltig_bis IS NULL").run(ende, closable[0].id);
    }
    if (input.abbruchNachSchreiben) throw new Error("Testabbruch vor dem Commit.");
    const meta = letzteZeile(geprueft.gruppe);
    database.prepare(`INSERT INTO zahlen_register (
        id, gruppe, version, betrag, einheit, gueltig_ab, gueltig_bis, quelle, freigabe,
        beschreibung, thema, stichworte_json, bedingung, created_at,
        wert_cent, wert_exakt, wert_bps, anwendungsbereich, fundstelle, dokumentstand, freigabe_nachweis, herkunft
      ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'freigegeben', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'freigabe')`).run(
      id,
      geprueft.gruppe,
      naechsteVersion(geprueft.gruppe),
      geprueft.einheit,
      geprueft.gueltigAb,
      geprueft.gueltigBis,
      geprueft.quelle,
      geprueft.beschreibung || meta?.beschreibung || geprueft.gruppe,
      geprueft.thema ?? meta?.thema ?? null,
      JSON.stringify(geprueft.stichworte ?? (meta ? stichworte(meta) : [])),
      geprueft.bedingung ?? meta?.bedingung ?? null,
      stamp,
      geprueft.wertCent,
      geprueft.wertExakt,
      geprueft.wertBps,
      geprueft.anwendungsbereich,
      geprueft.fundstelle,
      geprueft.dokumentstand,
      nachweis,
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    if (istUnique(error)) {
      const nochmal = findeGleicheFreigabe(geprueft);
      if (nochmal) return nochmal;
    }
    throw error;
  }
  return eintragOderFehler(id);
}

export function wertAm(kennung: string, anwendungsbereich: string, datum: string): Auswahl {
  return wertFuerZeitraum({ kennung, anwendungsbereich, von: datum, bis: datum });
}

export function wertFuerZeitraum(input: { kennung: string; anwendungsbereich: string; von: string; bis: string }): Auswahl {
  if (!isoDatum(input.von) || !isoDatum(input.bis) || input.bis < input.von) {
    return { ok: false, grund: "fehlt", meldung: "Der Gültigkeitszeitraum ist kein gültiges Datum." };
  }
  const rows = getDb().prepare(`SELECT * FROM zahlen_register
    WHERE gruppe = ? AND freigabe = 'freigegeben' AND freigabe_nachweis IS NOT NULL AND freigabe_nachweis != ''
      AND anwendungsbereich = ? AND gueltig_ab <= ? AND (gueltig_bis IS NULL OR gueltig_bis >= ?)`).all(
    input.kennung,
    input.anwendungsbereich,
    input.von,
    input.bis,
  ) as SqlZeile[];
  if (rows.length === 0) return { ok: false, grund: "fehlt", meldung: fehltMeldung(input.kennung, input.anwendungsbereich, input.von, input.bis) };
  if (rows.length > 1) return { ok: false, grund: "mehrdeutig", meldung: konfliktMeldung(input.kennung, input.anwendungsbereich, input.von, input.bis) };
  return { ok: true, eintrag: mapEintrag(rows[0]) };
}

export function berechnungswert(input: { kennung: string; anwendungsbereich: string; von: string; bis: string }): Auswahl {
  if (!istBerechnungskennung(input.kennung)) {
    return {
      ok: false,
      grund: "unbekannt",
      meldung: `Die Kennung „${input.kennung}“ ist keine Berechnungsregel. Sie löst keine Berechnung aus.`,
    };
  }
  return wertFuerZeitraum(input);
}

export function revisionenZu(zeileId: string): Array<{ aktion: string; zustand: Record<string, unknown>; grund: string }> {
  const rows = getDb().prepare("SELECT aktion, zustand_json, grund FROM zahlen_revisionen WHERE zeile_id = ? ORDER BY created_at").all(zeileId) as Array<{ aktion: string; zustand_json: string; grund: string }>;
  return rows.map((row) => ({ aktion: row.aktion, zustand: JSON.parse(row.zustand_json) as Record<string, unknown>, grund: row.grund }));
}

function fehltMeldung(kennung: string, bereich: string, von: string, bis: string): string {
  const zeit = von === bis ? `am ${von}` : `im Zeitraum ${von} bis ${bis}`;
  return `Für „${kennung}“ (${bereich}) liegt ${zeit} kein freigegebener Wert vor. Die Berechnung ist blockiert. Es wird kein Wert aus einem anderen Jahr übernommen.`;
}

function konfliktMeldung(kennung: string, bereich: string, von: string, bis: string | null): string {
  const zeit = bis == null ? `ab ${von}` : von === bis ? `am ${von}` : `im Zeitraum ${von} bis ${bis}`;
  return `Für „${kennung}“ (${bereich}) liegen ${zeit} mehrere freigegebene Werte vor. Die Gültigkeitszeiträume überschneiden sich. Die Berechnung ist blockiert.`;
}

function pruefeEntwurf(input: WertEingabe): WertEingabe & { wertExakt: string; wertCent: number | null; wertBps: number | null; einheit: "euro" | "prozent" } {
  const gruppe = input.gruppe.trim();
  if (!KENNUNG.test(gruppe)) throw new Error("Die Kennung darf nur Kleinbuchstaben, Ziffern und Unterstriche enthalten.");
  if (input.einheit !== "euro" && input.einheit !== "prozent") throw new Error("Die Einheit muss Euro oder Prozent sein.");
  if (!isoDatum(input.gueltigAb)) throw new Error("Der Beginn ist kein Datum.");
  if (input.gueltigBis !== null && !isoDatum(input.gueltigBis)) throw new Error("Das Ende ist kein Datum.");
  if (input.gueltigBis && input.gueltigBis < input.gueltigAb) throw new Error("Das Ende liegt vor dem Anfang.");
  const wert = parseWert(input.einheit, input.betrag);
  const meta = letzteZeile(gruppe);
  if (!input.beschreibung?.trim() && !meta) throw new Error("Die Beschreibung fehlt.");
  return { ...input, gruppe, ...wert, einheit: input.einheit };
}

function pruefeFreigabe(input: WertEingabe): WertEingabe & { wertExakt: string; wertCent: number | null; wertBps: number | null; einheit: "euro" | "prozent"; quelle: string; fundstelle: string; dokumentstand: string; anwendungsbereich: string } {
  const basis = pruefeEntwurf(input);
  const quelle = input.quelle?.trim() ?? "";
  const fundstelle = input.fundstelle?.trim() ?? "";
  const dokumentstand = input.dokumentstand?.trim() ?? "";
  const anwendungsbereich = input.anwendungsbereich?.trim() ?? "";
  if (!quelle || !fundstelle || !dokumentstand || !anwendungsbereich) {
    throw new Error("Zur Freigabe fehlen Angaben. Nötig sind Quelle, Fundstelle, Dokumentstand, Gültigkeit und Anwendungsbereich. Das System prüft nur die Vollständigkeit, nicht die fachliche Richtigkeit.");
  }
  if (DATE.test(dokumentstand) && !isoDatum(dokumentstand)) throw new Error("Der Dokumentstand ist kein gültiges Datum.");
  return { ...basis, quelle, fundstelle, dokumentstand, anwendungsbereich };
}

function findeGleicheFreigabe(input: { gruppe: string; anwendungsbereich: string; gueltigAb: string; gueltigBis: string | null; wertExakt: string }): RegisterEintrag | null {
  const row = getDb().prepare(`SELECT * FROM zahlen_register
    WHERE gruppe = ? AND freigabe = 'freigegeben' AND anwendungsbereich = ? AND gueltig_ab = ? AND wert_exakt = ?
      AND ((gueltig_bis IS NULL AND ? IS NULL) OR gueltig_bis = ?)`).get(
    input.gruppe,
    input.anwendungsbereich,
    input.gueltigAb,
    input.wertExakt,
    input.gueltigBis,
    input.gueltigBis,
  ) as SqlZeile | undefined;
  return row ? mapEintrag(row) : null;
}

function letzteZeile(gruppe: string): SqlZeile | null {
  return (getDb().prepare("SELECT * FROM zahlen_register WHERE gruppe = ? ORDER BY version DESC LIMIT 1").get(gruppe) as SqlZeile | undefined) ?? null;
}

function naechsteVersion(gruppe: string): number {
  const row = getDb().prepare("SELECT MAX(version) AS version FROM zahlen_register WHERE gruppe = ?").get(gruppe) as { version: number | null };
  return (row.version ?? 0) + 1;
}

function eintragOderFehler(id: string): RegisterEintrag {
  const row = getDb().prepare("SELECT * FROM zahlen_register WHERE id = ?").get(id) as SqlZeile | undefined;
  if (!row) throw new Error("Der Eintrag wurde nicht gespeichert.");
  return mapEintrag(row);
}

function schreibeRevision(database: ReturnType<typeof getDb>, row: SqlZeile, aktion: string, grund: string): void {
  database.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
    VALUES (?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), row.id, aktion, JSON.stringify(row), grund, new Date().toISOString());
}

function mapEintrag(row: SqlZeile): RegisterEintrag {
  let stichworte: string[] = [];
  if (row.stichworte_json) {
    const parsed = JSON.parse(row.stichworte_json) as unknown;
    if (Array.isArray(parsed)) stichworte = parsed.filter((item): item is string => typeof item === "string");
  }
  const einheit: Einheit = row.einheit === "prozent" || row.einheit === "hinweis" ? row.einheit : "euro";
  return {
    id: row.id,
    gruppe: row.gruppe,
    version: row.version,
    wertExakt: row.wert_exakt,
    wertCent: row.wert_cent,
    wertBps: row.wert_bps,
    einheit,
    gueltigAb: row.gueltig_ab,
    gueltigBis: row.gueltig_bis,
    quelle: row.quelle,
    fundstelle: row.fundstelle,
    dokumentstand: row.dokumentstand,
    anwendungsbereich: row.anwendungsbereich,
    freigabe: row.freigabe === "freigegeben" ? "freigegeben" : "entwurf",
    freigabeNachweis: row.freigabe_nachweis,
    herkunft: row.herkunft,
    beschreibung: row.beschreibung,
    thema: row.thema,
    stichworte,
    bedingung: row.bedingung,
    createdAt: row.created_at,
  };
}

function stichworte(row: SqlZeile): string[] {
  return mapEintrag(row).stichworte;
}

function gleicheVorlage(row: SqlZeile, zeile: VorlageZeile): boolean {
  if (row.gruppe !== zeile.gruppe || row.gueltig_ab !== zeile.gueltigAb) return false;
  if (zeile.einheit === "hinweis") return row.einheit === "hinweis";
  if (row.wert_exakt && zeile.wertExakt && row.wert_exakt === zeile.wertExakt) return true;
  if (row.einheit !== zeile.einheit) return false;
  if (zeile.wertCent != null && row.wert_cent != null) return row.wert_cent === zeile.wertCent;
  if (zeile.wertBps != null && row.wert_bps != null) return row.wert_bps === zeile.wertBps;
  if (row.betrag == null) return false;
  const ziel = zeile.einheit === "euro" ? zeile.wertCent : zeile.wertBps;
  return ziel != null && Math.round(Number(row.betrag) * 100) === ziel;
}

function liesVorlageZeilen(file: string): VorlageZeile[] {
  let raw: string;
  try {
    raw = readFileSync(file, "utf8");
  } catch {
    throw new Error("Die Werteliste daten/zahlen-werte.json fehlt.");
  }
  const betraege: string[] = [];
  const tagged = raw.replace(/"betrag"\s*:\s*(-?\d+(?:\.\d+)?)/g, (_match, num: string) => {
    const token = `__BETRAG_${betraege.length}__`;
    betraege.push(num);
    return `"betrag":"${token}"`;
  });
  const parsed = JSON.parse(tagged) as {
    liste_stand?: string;
    wertegruppen?: Array<{
      name?: string;
      beschreibung?: string;
      quelle?: string;
      einheit?: string;
      thema?: string;
      stichworte?: string[];
      bedingung?: string;
      werte?: Array<{ betrag?: string; gueltig_ab?: string; gueltig_bis?: string | null }>;
    }>;
  };
  if (!Array.isArray(parsed.wertegruppen)) throw new Error("Die Werteliste daten/zahlen-werte.json ist ungültig.");
  const zeilen: VorlageZeile[] = [];
  for (const gruppe of parsed.wertegruppen) {
    if (!gruppe.name || !KENNUNG.test(gruppe.name)) throw new Error("Eine Kennung in der Vorlage ist ungültig.");
    const einheit: "euro" | "prozent" = gruppe.einheit === "prozent" || gruppe.name === "abgabesatz" ? "prozent" : "euro";
    const werte = gruppe.werte ?? [];
    if (werte.length === 0) {
      zeilen.push({
        gruppe: gruppe.name,
        beschreibung: gruppe.beschreibung ?? gruppe.name,
        quelle: gruppe.quelle ?? "",
        thema: gruppe.thema ?? null,
        stichworte: gruppe.stichworte ?? [],
        bedingung: gruppe.bedingung ?? null,
        einheit: "hinweis",
        wertExakt: null,
        wertCent: null,
        wertBps: null,
        gueltigAb: parsed.liste_stand && isoDatum(parsed.liste_stand) ? parsed.liste_stand : "2026-01-01",
        gueltigBis: null,
      });
      continue;
    }
    for (const wert of werte) {
      const token = wert.betrag ?? "";
      const exact = token.startsWith("__BETRAG_") ? betraege[Number(token.slice(9, -2))] : token;
      const parsedWert = parseWert(einheit, exact);
      if (!wert.gueltig_ab || !isoDatum(wert.gueltig_ab)) throw new Error(`Der Beginn in ${gruppe.name} ist kein Datum.`);
      if (wert.gueltig_bis != null && !isoDatum(wert.gueltig_bis)) throw new Error(`Das Ende in ${gruppe.name} ist kein Datum.`);
      zeilen.push({
        gruppe: gruppe.name,
        beschreibung: gruppe.beschreibung ?? gruppe.name,
        quelle: gruppe.quelle ?? "",
        thema: gruppe.thema ?? null,
        stichworte: gruppe.stichworte ?? [],
        bedingung: gruppe.bedingung ?? null,
        einheit,
        wertExakt: parsedWert.wertExakt,
        wertCent: parsedWert.wertCent,
        wertBps: parsedWert.wertBps,
        gueltigAb: wert.gueltig_ab,
        gueltigBis: wert.gueltig_bis ?? null,
      });
    }
  }
  return zeilen;
}

function ueberlappt(aAb: string, aBis: string | null, bAb: string, bBis: string | null): boolean {
  return aAb <= (bBis ?? OFFEN) && bAb <= (aBis ?? OFFEN);
}

function isoDatum(value: string): boolean {
  if (!DATE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function tagDavor(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}

function blank(value: string | undefined): string | null {
  const text = value?.trim() ?? "";
  return text.length > 0 ? text : null;
}

function istUnique(error: unknown): boolean {
  return error instanceof Error && /UNIQUE/i.test(error.message);
}
```

### `src/lib/register-kennungen.ts`

```ts
export const ABGABESATZ = "abgabesatz";
export const ABGABEGRENZE = "abgabepflichtgrenze_veranstalter";
export const BEREICH_ABGABESATZ = "Künstlersozialabgabe für das Kalenderjahr";
export const BEREICH_GRENZE = "§ 24 Abs. 2 KSVG";

const BERECHNUNG = [ABGABESATZ, ABGABEGRENZE] as const;

export type Berechnungskennung = (typeof BERECHNUNG)[number];

export function istBerechnungskennung(kennung: string): kennung is Berechnungskennung {
  return (BERECHNUNG as readonly string[]).includes(kennung);
}

export type RegisterSnapshot = {
  id: string;
  kennung: string;
  anwendungsbereich: string | null;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  einheit: string;
  gueltigAb: string;
  gueltigBis: string | null;
  quelle: string;
  fundstelle: string | null;
  dokumentstand: string | null;
  freigabe: string;
};
```

### `src/lib/mistral/zahlen-werte.ts`

```ts
import { existsSync, mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { KonsensErgebnis } from "@/lib/model-consensus";
import { ladeFreigegebene, zahlenWertePfad as registerPfad, type RegisterEintrag } from "@/lib/zahlen-register";

export type Freigabe = "entwurf" | "freigegeben";

export type WertZeile = {
  betrag: number;
  gueltig_ab: string;
  gueltig_bis: string | null;
  version?: number;
  einheit?: "euro" | "prozent";
  quelle?: string;
  freigabe?: Freigabe;
};

export type WerteGruppe = {
  name: string;
  beschreibung: string;
  quelle: string;
  werte: WertZeile[];
  einheit?: "euro" | "prozent";
  thema?: string;
  stichworte?: string[];
  bedingung?: string;
};

export type Grenze = {
  value: number;
  unit: "euro" | "prozent";
  jahr: number | null;
  label: string;
};

export type ProzentStatus = "belegt" | "nutzerangabe" | "unbekannt";

export type ProzentZeile = {
  pruefer: string;
  label: string;
  status: ProzentStatus;
};

export type ZahlenListe = {
  liste_stand: string;
  letzte_aenderung: string;
  wertegruppen: WerteGruppe[];
};

export type ZeitCheck = {
  jahr: number;
  angenommen: boolean;
  line: string;
  hinweise: string[];
};

const DATE = /^\d{4}-\d{2}-\d{2}$/;

export function zahlenWertePfad(): string {
  return registerPfad();
}

export function vorlageAusDatei(file = zahlenWertePfad()): ZahlenListe {
  return liesJson(file);
}

function liesJson(file: string): ZahlenListe {
  let raw: string;
  try {
    raw = readFileSync(file, "utf8");
  } catch {
    throw new Error("Die Werteliste daten/zahlen-werte.json fehlt.");
  }
  const parsed = JSON.parse(raw) as ZahlenListe;
  if (!Array.isArray(parsed.wertegruppen)) throw new Error("Die Werteliste daten/zahlen-werte.json ist ungültig.");
  return parsed;
}

function anzeigeBetrag(eintrag: RegisterEintrag): number | null {
  if (eintrag.einheit === "euro" && eintrag.wertCent != null) return eintrag.wertCent / 100;
  if (eintrag.einheit === "prozent" && eintrag.wertBps != null) return eintrag.wertBps / 100;
  return null;
}

function listeAusEintraegen(eintraege: RegisterEintrag[]): ZahlenListe {
  const gruppen: WerteGruppe[] = [];
  for (const eintrag of eintraege) {
    let gruppe = gruppen.find((item) => item.name === eintrag.gruppe);
    if (!gruppe) {
      gruppe = {
        name: eintrag.gruppe,
        beschreibung: eintrag.beschreibung,
        quelle: eintrag.quelle,
        werte: [],
        einheit: eintrag.einheit === "prozent" ? "prozent" : "euro",
        thema: eintrag.thema ?? undefined,
        stichworte: eintrag.stichworte,
        bedingung: eintrag.bedingung ?? undefined,
      };
      gruppen.push(gruppe);
    }
    const betrag = anzeigeBetrag(eintrag);
    if (betrag == null) continue;
    gruppe.werte.push({
      betrag,
      gueltig_ab: eintrag.gueltigAb,
      gueltig_bis: eintrag.gueltigBis,
      version: eintrag.version,
      einheit: eintrag.einheit === "prozent" ? "prozent" : "euro",
      quelle: eintrag.quelle,
      freigabe: eintrag.freigabe,
    });
  }
  for (const gruppe of gruppen) gruppe.werte.sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab) || (a.version ?? 0) - (b.version ?? 0));
  const zeiten = eintraege.map((eintrag) => eintrag.createdAt.slice(0, 10)).sort();
  return {
    liste_stand: zeiten[0] ?? new Date().toISOString().slice(0, 10),
    letzte_aenderung: zeiten[zeiten.length - 1] ?? new Date().toISOString().slice(0, 10),
    wertegruppen: gruppen,
  };
}

export function ladeZahlenWerte(file?: string): ZahlenListe {
  if (file && path.resolve(file) !== path.resolve(zahlenWertePfad())) return liesJson(file);
  return listeAusEintraegen(ladeFreigegebene());
}

export function schreibeZahlenWerte(liste: ZahlenListe, file: string): void {
  if (path.resolve(file) === path.resolve(zahlenWertePfad())) {
    throw new Error("Die Vorlagendatei daten/zahlen-werte.json wird nicht überschrieben.");
  }
  const payload = `${JSON.stringify(liste, null, 2)}\n`;
  const directory = path.dirname(file);
  mkdirSync(directory, { recursive: true });
  const temp = `${file}.tmp`;
  const backup = `${file}.bak`;
  try {
    writeFileSync(temp, payload, "utf8");
    if (existsSync(file)) renameSync(file, backup);
    renameSync(temp, file);
    if (existsSync(backup)) unlinkSync(backup);
  } catch {
    try {
      if (!existsSync(file) && existsSync(backup)) renameSync(backup, file);
    } catch {
      // Die Sicherung bleibt liegen, die unvollständige Datei wird nicht zur Liste.
    }
    try {
      if (existsSync(temp)) unlinkSync(temp);
    } catch {
      // Die temporäre Datei ist nicht die Liste.
    }
    throw new Error("Die Werteliste konnte nicht gespeichert werden.");
  }
}

export function formatProzent(value: number): string {
  return `${value.toFixed(1).replace(".", ",")} %`;
}

export function formatBetrag(betrag: number): string {
  const negative = betrag < 0;
  const absolute = Math.abs(betrag);
  const [whole, fraction] = absolute.toFixed(Number.isInteger(absolute) ? 0 : 2).split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const body = fraction && fraction !== "00" ? `${grouped},${fraction}` : grouped;
  return `${negative ? "-" : ""}${body} €`;
}

export function formatDatum(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}.${month}.${year}`;
}

function isoDatum(value: string): boolean {
  if (!DATE.test(value)) return false;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

export function fensterEnthaeltJahr(zeile: WertZeile, jahr: number): boolean {
  const anfang = `${jahr}-01-01`;
  const ende = `${jahr}-12-31`;
  if (zeile.gueltig_ab > ende) return false;
  if (zeile.gueltig_bis && zeile.gueltig_bis < anfang) return false;
  return true;
}

export function bezugsjahr(frage: string, heute = new Date()): { jahr: number; angenommen: boolean } {
  const match = frage.match(/\b(?:19|20)\d{2}\b/);
  if (match) return { jahr: Number(match[0]), angenommen: false };
  return { jahr: heute.getFullYear(), angenommen: true };
}

export function einheitVon(gruppe: WerteGruppe): "euro" | "prozent" {
  if (gruppe.einheit === "prozent" || gruppe.name === "abgabesatz") return "prozent";
  return "euro";
}

function gruppenLabel(gruppe: WerteGruppe): string {
  if (gruppe.name === "abgabepflichtgrenze_veranstalter") return "Abgabepflichtgrenze Veranstalter";
  if (gruppe.name === "bagatellgrenze_zahlungsvorgang") return "Bagatellgrenze je Zahlungsvorgang";
  if (gruppe.name === "abgabesatz") return "Abgabesatz";
  return gruppe.beschreibung.trim() || gruppe.name;
}

function formatWert(gruppe: WerteGruppe, betrag: number): string {
  return einheitVon(gruppe) === "prozent" ? formatProzent(betrag) : formatBetrag(betrag);
}

function quellenKuerzel(quelle: string): string {
  const info = quelle.match(/info[_ -]?(\d+)/i);
  if (info) return `Info_${info[1]}`;
  return quelle.replace(/\.pdf$/i, "");
}

export function werteFuerJahr(gruppe: WerteGruppe, jahr: number): WertZeile[] {
  return gruppe.werte.filter((zeile) => fensterEnthaeltJahr(zeile, jahr)).sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
}

export function wertFuerJahr(gruppe: WerteGruppe, jahr: number): WertZeile | null {
  const anfang = `${jahr}-01-01`;
  const ende = `${jahr}-12-31`;
  const deckend = gruppe.werte.filter((zeile) => zeile.gueltig_ab <= anfang && (zeile.gueltig_bis === null || zeile.gueltig_bis >= ende));
  return deckend.length === 1 ? deckend[0] : null;
}

function trifftStichwort(frage: string, stichwort: string): boolean {
  const needle = stichwort.trim().toLowerCase();
  if (!needle) return false;
  if (needle.length <= 3) return new RegExp(`\\b${needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(frage);
  return frage.toLowerCase().includes(needle);
}

function passendeGruppen(frage: string, liste: ZahlenListe): WerteGruppe[] {
  return liste.wertegruppen.filter((gruppe) => {
    const worte = gruppe.stichworte ?? (gruppe.thema ? [gruppe.thema] : []);
    return worte.some((wort) => trifftStichwort(frage, wort));
  });
}

export function alleThemenBetraege(frage: string, liste: ZahlenListe): Array<{ value: number; unit: "euro" | "prozent" }> {
  const gesehen = new Set<string>();
  const treffer: Array<{ value: number; unit: "euro" | "prozent" }> = [];
  for (const gruppe of passendeGruppen(frage, liste)) {
    const unit = einheitVon(gruppe);
    for (const zeile of gruppe.werte) {
      const key = `${unit}:${zeile.betrag}`;
      if (gesehen.has(key)) continue;
      gesehen.add(key);
      treffer.push({ value: zeile.betrag, unit });
    }
  }
  return treffer;
}

export function relevanteBetraege(frage: string, liste: ZahlenListe, jahr: number): Array<{ value: number; unit: "euro" | "prozent" }> {
  const gesehen = new Set<string>();
  const treffer: Array<{ value: number; unit: "euro" | "prozent" }> = [];
  for (const gruppe of passendeGruppen(frage, liste)) {
    const zeile = wertFuerJahr(gruppe, jahr);
    if (!zeile) continue;
    const unit = einheitVon(gruppe);
    const key = `${unit}:${zeile.betrag}`;
    if (gesehen.has(key)) continue;
    gesehen.add(key);
    treffer.push({ value: zeile.betrag, unit });
  }
  return treffer;
}

export function relevanteWerte(frage: string, liste: ZahlenListe, jahr: number): string[] {
  return relevanteBetraege(frage, liste, jahr).map((treffer) => treffer.unit === "prozent" ? formatProzent(treffer.value) : formatBetrag(treffer.value));
}

export function f05Hinweis(input: {
  nenntKeine: boolean;
  frage: string;
  jahr: number;
  liste: ZahlenListe;
  prueferLabel: string;
}): string | null {
  if (!input.nenntKeine) return null;
  const werte = relevanteWerte(input.frage, input.liste, input.jahr);
  if (werte.length === 0) return null;
  const pruefer = input.prueferLabel.match(/Prüfer\s+\d+/)?.[0] ?? input.prueferLabel;
  return `⚠️ ${pruefer} nennt keine Zahlen — Dokument enthält laut Liste: ${werte.join(", ")}. Lesefehler wahrscheinlich.`;
}

export function kontextBlock(liste: ZahlenListe, jahr: number): string {
  const zeilen = liste.wertegruppen.flatMap((gruppe) => {
    const wert = wertFuerJahr(gruppe, jahr);
    if (!wert) return [];
    return [`- ${gruppenLabel(gruppe)}: ${formatWert(gruppe, wert.betrag)} (Quelle: ${quellenKuerzel(gruppe.quelle)})`];
  });
  return [
    `## Kontext (vom System bereitgestellt — verbindlich, Stand: ${liste.liste_stand})`,
    `Bezugsjahr: ${jahr}`,
    "Aktuell gültige Werte (aus dem Zahlenregister, nur freigegeben):",
    ...zeilen,
    "Werte anderer Jahre sind für dieses Bezugsjahr NICHT gültig.",
  ].join("\n");
}

function gleicheBetrag(links: number, rechts: number): boolean {
  return Math.abs(links - rechts) < 0.001;
}

export type BetragImJahr = "gueltig" | "historisch" | "fremd";

export function stehtInListe(value: number, unit: "euro" | "prozent", liste: ZahlenListe): boolean {
  return liste.wertegruppen.some((gruppe) => einheitVon(gruppe) === unit && gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, value)));
}

export function betragImJahr(value: number, unit: "euro" | "prozent", liste: ZahlenListe, jahr: number): BetragImJahr {
  const zeilen = liste.wertegruppen
    .filter((gruppe) => einheitVon(gruppe) === unit)
    .flatMap((gruppe) => gruppe.werte.filter((zeile) => gleicheBetrag(zeile.betrag, value)));
  if (zeilen.length === 0) return "fremd";
  return zeilen.some((zeile) => fensterEnthaeltJahr(zeile, jahr)) ? "gueltig" : "historisch";
}

export function nurGueltigeBetraege(keys: string[], labels: string[], liste: ZahlenListe, jahr: number): { keys: string[]; labels: string[] } {
  const behalten = keys.map((key, index) => ({ key, label: labels[index] ?? "" })).filter((item) => {
    const value = Number(item.key);
    return Number.isFinite(value) && betragImJahr(value, "euro", liste, jahr) === "gueltig";
  });
  return { keys: behalten.map((item) => item.key), labels: behalten.map((item) => item.label).filter(Boolean) };
}

function prueferKurz(label: string): string {
  return label.match(/Prüfer\s+\d+/)?.[0] ?? label;
}

function labelFuer(nennung: Grenze, gruppe: WerteGruppe | undefined): string {
  if (gruppe) return formatWert(gruppe, nennung.value);
  return nennung.unit === "prozent" ? formatProzent(nennung.value) : formatBetrag(nennung.value);
}

export type ZeitHinweis = { text: string; ausserhalb: boolean };

export function zeitHinweisEintraege(nennungen: Grenze[], liste: ZahlenListe, bezugsjahrWert: number, prueferLabel: string): ZeitHinweis[] {
  const pruefer = prueferKurz(prueferLabel);
  const hinweise: ZeitHinweis[] = [];
  const gesehen = new Set<string>();
  for (const nennung of nennungen) {
    const pruefjahr = nennung.jahr ?? bezugsjahrWert;
    const key = `${nennung.unit}:${nennung.value.toFixed(2)}:${pruefjahr}`;
    if (gesehen.has(key)) continue;
    gesehen.add(key);
    const gruppen = liste.wertegruppen.filter((gruppe) => einheitVon(gruppe) === nennung.unit);
    const zeilen = gruppen.flatMap((gruppe) => gruppe.werte.filter((zeile) => gleicheBetrag(zeile.betrag, nennung.value)));
    if (zeilen.length === 0 || zeilen.some((zeile) => fensterEnthaeltJahr(zeile, pruefjahr))) continue;
    const gruppe = gruppen.find((item) => item.werte.some((zeile) => gleicheBetrag(zeile.betrag, nennung.value)));
    const label = labelFuer(nennung, gruppe);
    const beendet = zeilen
      .filter((zeile) => zeile.gueltig_bis && zeile.gueltig_bis < `${pruefjahr}-01-01`)
      .sort((a, b) => (b.gueltig_bis ?? "").localeCompare(a.gueltig_bis ?? ""));
    const kuenftig = zeilen
      .filter((zeile) => zeile.gueltig_ab > `${pruefjahr}-12-31`)
      .sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
    const ausserhalb = betragImJahr(nennung.value, nennung.unit, liste, bezugsjahrWert) === "historisch";
    const text = nennung.jahr != null && beendet[0]?.gueltig_bis
      ? `⚠️ Zeit-Check: ${label} gilt nicht für ${nennung.jahr}, sondern nur bis ${formatDatum(beendet[0].gueltig_bis)} (${pruefer})`
      : nennung.jahr != null && kuenftig[0]
        ? `⚠️ Zeit-Check: ${label} gilt nicht für ${nennung.jahr}, sondern erst ab ${formatDatum(kuenftig[0].gueltig_ab)} (${pruefer})`
        : beendet[0]?.gueltig_bis
          ? `⚠️ Zeit-Check: ${label} gilt nur bis ${formatDatum(beendet[0].gueltig_bis)} (${pruefer})`
          : kuenftig[0]
            ? `⚠️ Zeit-Check: ${label} gilt erst ab ${formatDatum(kuenftig[0].gueltig_ab)} (${pruefer})`
            : `⚠️ Zeit-Check: ${label} gilt im Bezugsjahr ${pruefjahr} nicht (${pruefer})`;
    hinweise.push({ text, ausserhalb });
  }
  return hinweise;
}

export function zeitHinweise(nennungen: Grenze[], liste: ZahlenListe, bezugsjahrWert: number, prueferLabel: string): string[] {
  return zeitHinweisEintraege(nennungen, liste, bezugsjahrWert, prueferLabel).map((eintrag) => eintrag.text);
}

export function klassifiziereProzent(value: number, frage: string, liste: ZahlenListe): ProzentStatus {
  const gruppen = liste.wertegruppen.filter((gruppe) => einheitVon(gruppe) === "prozent");
  if (gruppen.some((gruppe) => gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, value)))) return "belegt";
  const inFrage = frage.match(/\d+(?:[.,]\d+)?\s*%/g)?.some((raw) => {
    const parsed = Number(raw.replace("%", "").replace(/\s/g, "").replace(",", "."));
    return Number.isFinite(parsed) && gleicheBetrag(parsed, value);
  });
  return inFrage ? "nutzerangabe" : "unbekannt";
}

export function zeitErgebnis(input: {
  jahr: number;
  angenommen: boolean;
  hinweise: string[];
}): ZeitCheck {
  return {
    jahr: input.jahr,
    angenommen: input.angenommen,
    hinweise: input.hinweise,
    line: input.hinweise.length > 0 ? "📅 Zeit-Check: ⚠️" : `📅 Zeit-Check: ✅ Werte passen zum Bezugsjahr ${input.jahr}`,
  };
}

export function mitZeitabweichung(konsens: KonsensErgebnis, hinweise: ZeitHinweis[], hatGueltige = true): KonsensErgebnis {
  if (hinweise.length === 0 || konsens.status !== "konsens") return konsens;
  const verletzung = hinweise.filter((hinweis) => !hinweis.ausserhalb);
  if (verletzung.length > 0) {
    return {
      status: "abweichung",
      line: "⚠️ Abweichung — Zeit-Check, kein Konsens 3/3",
      detail: verletzung.map((hinweis) => hinweis.text).join(" — "),
    };
  }
  if (!hatGueltige) {
    return {
      status: "hinweis",
      line: "⚠️ Gültige Werte konsistent — historische Werte im Zeit-Check",
      detail: hinweise.map((hinweis) => hinweis.text).join(" — "),
    };
  }
  return konsens;
}

export function jahreswechselHinweis(heute = new Date()): string | null {
  if (heute.getMonth() < 9) return null;
  return `⚠️ Für ${heute.getFullYear() + 1} prüfen!`;
}

export function ergaenzeZeile(liste: ZahlenListe, input: {
  gruppe: string;
  betrag: number;
  gueltig_ab: string;
  gueltig_bis: string | null;
}, heute: string): ZahlenListe {
  if (!isoDatum(heute)) throw new Error("Das Änderungsdatum ist ungültig.");
  if (!Number.isFinite(input.betrag) || input.betrag <= 0) throw new Error("Der Betrag fehlt.");
  if (!isoDatum(input.gueltig_ab)) throw new Error("Der Beginn ist kein Datum.");
  if (input.gueltig_bis !== null && !isoDatum(input.gueltig_bis)) throw new Error("Das Ende ist kein Datum.");
  if (input.gueltig_bis && input.gueltig_bis < input.gueltig_ab) throw new Error("Das Ende liegt vor dem Anfang.");
  const next = structuredClone(liste);
  const gruppe = next.wertegruppen.find((item) => item.name === input.gruppe);
  if (!gruppe) throw new Error("Die Wertegruppe gibt es nicht.");
  const doppelt = gruppe.werte.some((zeile) => gleicheBetrag(zeile.betrag, input.betrag) && zeile.gueltig_ab === input.gueltig_ab && zeile.gueltig_bis === input.gueltig_bis);
  if (doppelt) throw new Error("Diese Zeile steht schon in der Liste.");
  gruppe.werte.push({ betrag: input.betrag, gueltig_ab: input.gueltig_ab, gueltig_bis: input.gueltig_bis });
  gruppe.werte.sort((a, b) => a.gueltig_ab.localeCompare(b.gueltig_ab));
  next.letzte_aenderung = heute;
  return next;
}
```

### `src/lib/domain/rules.ts`

```ts
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
```

### `src/lib/domain/money.ts`

```ts
/** Kaufmännisches Runden auf ganze Cent. Eingaben bleiben Ganzzahlen. */
export function levyCents(basisCents: number, rateBps: number): number {
  if (!Number.isSafeInteger(basisCents) || !Number.isSafeInteger(rateBps)) {
    throw new Error("Abgabe nur aus sicheren Ganzzahlen.");
  }
  if (basisCents < 0 || rateBps < 0) {
    throw new Error("Negative Bemessungsgrundlage oder negativer Satz.");
  }
  const product = basisCents * rateBps;
  if (!Number.isSafeInteger(product)) {
    throw new Error("Der Betrag ist zu groß für eine genaue Cent-Rechnung.");
  }
  return Math.floor((product + 5000) / 10000);
}

export function formatEuro(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return "Ungeklärt";
  const sign = cents < 0 ? "−" : "";
  const abs = Math.abs(cents);
  const euros = Math.floor(abs / 100);
  const rest = abs % 100;
  const grouped = euros.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped},${rest.toString().padStart(2, "0")} €`;
}

export function formatPercentFromBps(rateBps: number): string {
  const whole = Math.floor(rateBps / 100);
  const frac = rateBps % 100;
  if (frac === 0) return `${whole},0 %`;
  return `${whole},${frac.toString().padStart(2, "0").replace(/0$/, "")} %`;
}

export function isFilingSeason(date: Date): boolean {
  const month = date.getMonth() + 1;
  return month >= 1 && month <= 3;
}
```

### `src/lib/domain/evaluate.ts`

```ts
import type {
  ConfirmedInvoice,
  ConfirmedPosition,
  KskCategory,
  PositionState,
  ReportPosition,
  RuleSet,
} from "./types";
import { UNCLEAR } from "./types";
import type { RegisterSnapshot } from "@/lib/register-kennungen";
import { missingRateMessage, satzlage } from "./rules";
import { levyCents } from "./money";

export interface Evaluation {
  year: number | null;
  rateBps: number | null;
  rateLabel: string | null;
  thresholdCents: number | null;
  thresholdApplies: boolean | null;
  configError: string | null;
  positions: ReportPosition[];
  knownIncludedCents: number | null;
  thresholdResult: "ueberstiegen" | "nicht_ueberstiegen" | "offen" | "nicht_anwendbar";
  registerIds: string[];
  registerSnapshot: RegisterSnapshot[];
}

const HINT_NOTE =
  "Ein Nachweis beweist einen realen Vorgang. Er erschafft ihn nicht. Dieser Hinweis ändert die Einordnung nicht.";

function includedCents(invoice: ConfirmedInvoice, rules: RuleSet): number | null {
  let sum = 0;
  for (const position of invoice.positions) {
    if (position.kind.value === "umsatzsteuer") continue;
    if (position.kind.value === UNCLEAR || position.netCents.value === UNCLEAR) return null;
    if (!rules.scenarios.includedInBase.includes(position.kind.value)) return null;
    sum += position.netCents.value;
  }
  return sum;
}

function hintFor(position: ConfirmedPosition, rules: RuleSet) {
  if (position.kind.value === UNCLEAR) return null;
  const rule = rules.scenarios.hints.find((item) => item.kind === position.kind.value);
  if (!rule) return null;
  return {
    positionId: position.id,
    classification: "ABGABEPFLICHTIG" as const,
    dependency: rule.dependency,
    possibleExclusionReason: rule.reason,
    citation: rule.citation,
    requiredEvidence: rule.requiredEvidence,
    whenEvidenceDoesNotWork: rule.whenEvidenceDoesNotWork,
    note: HINT_NOTE,
  };
}

function decideThreshold(invoice: ConfirmedInvoice, rules: RuleSet, thresholdCents: number): Evaluation["thresholdResult"] {
  const known = includedCents(invoice, rules);
  const annualComplete = invoice.annualSumConfirmed.value === true;
  if (known !== null && known > thresholdCents) return "ueberstiegen";
  if (known !== null && annualComplete && known <= thresholdCents) return "nicht_ueberstiegen";
  return "offen";
}

function basePosition(position: ConfirmedPosition, state: PositionState, citation: string | null, rationale: string, rules: RuleSet): ReportPosition {
  const cents = position.netCents.value;
  const hint = state === "ABGABEPFLICHTIG" ? hintFor(position, rules) : null;
  return {
    id: position.id,
    label: position.label.value,
    state,
    amountCents: typeof cents === "number" ? cents : null,
    amountState: typeof cents === "number" ? "BESTAETIGT" : UNCLEAR,
    category: position.category.value,
    kind: position.kind.value,
    citation,
    rationaleLayperson: rationale,
    hint,
    source: position.source,
  };
}

export function evaluateInvoice(invoice: ConfirmedInvoice, rules: RuleSet): Evaluation {
  const year = invoice.year.value === UNCLEAR ? null : invoice.year.value;
  const lage = year === null ? null : satzlage(year);
  const rate = lage?.rate ?? null;
  const configError = year !== null && !rate ? (lage?.fehler || missingRateMessage(year)) : null;
  const role = invoice.payerRole.value === UNCLEAR ? null : rules.scenarios.roles[invoice.payerRole.value];
  const thresholdApplies = role ? role.thresholdApplies : null;
  const thresholdCents = rate?.thresholdCents ?? null;
  const thresholdResult: Evaluation["thresholdResult"] = !role
    ? "offen"
    : !role.thresholdApplies
      ? "nicht_anwendbar"
      : thresholdCents === null
        ? "offen"
        : decideThreshold(invoice, rules, thresholdCents);

  const positions = invoice.positions.map((position) =>
    classifyPosition(invoice, position, rules, { configError, thresholdResult, roleCitation: role?.citation ?? null, roleLay: role?.layperson ?? null, thresholdSource: rate?.thresholdSource ?? null }),
  );

  return {
    year,
    rateBps: rate?.rateBps ?? null,
    rateLabel: rate?.rateSource ?? null,
    thresholdCents,
    thresholdApplies,
    configError,
    positions,
    knownIncludedCents: includedCents(invoice, rules),
    thresholdResult,
    registerIds: lage?.registerIds ?? [],
    registerSnapshot: lage?.registerSnapshot ?? [],
  };
}

function classifyPosition(
  invoice: ConfirmedInvoice,
  position: ConfirmedPosition,
  rules: RuleSet,
  ctx: {
    configError: string | null;
    thresholdResult: Evaluation["thresholdResult"];
    roleCitation: string | null;
    roleLay: string | null;
    thresholdSource: string | null;
  },
): ReportPosition {
  if (!invoice.readable) {
    return basePosition(position, UNCLEAR, null, invoice.unreadableReason ?? "Die Rechnung war nicht lesbar.", rules);
  }
  if (position.kind.value === "umsatzsteuer") {
    return basePosition(
      position,
      "NICHT_ABGABEPFLICHTIG",
      "§ 25 Abs. 2 Satz 1 KSVG",
      "Gesondert ausgewiesene Umsatzsteuer gehört nicht zum Entgelt.",
      rules,
    );
  }
  if (position.netCents.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, position.netCents.reason ?? "Der Betrag ist ungeklärt.", rules);
  }
  if (position.kind.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Die Art der Position ist ungeklärt. Ohne Art lässt sich nicht sagen, ob sie zum Entgelt gehört.", rules);
  }
  if (invoice.payeeKind.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Es ist ungeklärt, ob eine natürliche Person oder eine Gesellschaft geleistet hat.", rules);
  }
  if (invoice.payeeKind.value === "gesellschaft") {
    const rule = rules.scenarios.payeeGesellschaft;
    return basePosition(position, rule.state, rule.citation, rule.reason, rules);
  }
  if (invoice.payerRole.value === UNCLEAR || !ctx.roleCitation) {
    return basePosition(position, UNCLEAR, null, "Die Rolle des Auftraggebers ist ungeklärt. Deshalb lässt sich die Abgabepflicht nicht einordnen.", rules);
  }
  if (invoice.year.value === UNCLEAR) {
    return basePosition(position, UNCLEAR, null, "Das Kalenderjahr der Leistung ist ungeklärt. Abgabesatz und Jahresgrenze hängen am Jahr.", rules);
  }
  if (ctx.configError) {
    return basePosition(position, UNCLEAR, null, ctx.configError, rules);
  }
  if (ctx.thresholdResult === "offen") {
    return basePosition(
      position,
      UNCLEAR,
      ctx.roleCitation,
      "Die Jahresgrenze gilt für die Summe eines Kalenderjahres. Diese Rechnung allein zeigt nicht, ob die Grenze überschritten ist, und sie liegt nicht schon für sich darüber.",
      rules,
    );
  }
  if (ctx.thresholdResult === "nicht_ueberstiegen") {
    return basePosition(
      position,
      "NICHT_ABGABEPFLICHTIG",
      `${ctx.roleCitation}; ${ctx.thresholdSource ?? "Jahresgrenze"}`,
      "Die bestätigte Jahressumme übersteigt die Jahresgrenze nicht. Erst ein Überschreiten löst die Abgabepflicht aus. Genau die Grenze genügt nicht.",
      rules,
    );
  }
  const citation = ctx.roleCitation;
  const extra = ctx.thresholdResult === "ueberstiegen"
    ? " Die Jahresgrenze ist überschritten. Es zählt die betroffene Summe, nicht nur der Teil oberhalb der Grenze."
    : "";
  return basePosition(
    position,
    "ABGABEPFLICHTIG",
    `${citation}; § 25 Abs. 2 Satz 1 KSVG`,
    `${ctx.roleLay} Der Betrag bleibt im Entgelt.${extra}`,
    rules,
  );
}

export function totalsFromEvaluation(evaluation: Evaluation, rules: RuleSet) {
  const open = evaluation.positions.some((position) => position.state === UNCLEAR || position.amountState === UNCLEAR);
  const categories: KskCategory[] = ["wort", "bildende_kunst", "musik", "darstellende_kunst"];
  const buckets = categories.map((category) => {
    const rows = evaluation.positions.filter((position) => position.state === "ABGABEPFLICHTIG" && position.category === category && position.amountCents !== null);
    const basisCents = rows.reduce((sum, position) => sum + (position.amountCents ?? 0), 0);
    return {
      category,
      label: category,
      basisCents,
      levyCents: !open && evaluation.rateBps !== null && !evaluation.configError ? levyCents(basisCents, evaluation.rateBps) : null,
      positionIds: rows.map((position) => position.id),
    };
  });
  const uncategorisedPositionIds = evaluation.positions
    .filter((position) => position.state === "ABGABEPFLICHTIG" && position.category === UNCLEAR)
    .map((position) => position.id);
  const decidedBasis = evaluation.positions
    .filter((position) => position.state === "ABGABEPFLICHTIG" && position.amountCents !== null)
    .reduce((sum, position) => sum + (position.amountCents ?? 0), 0);
  const nothingDue = evaluation.positions.length > 0 && evaluation.positions.every((position) => position.state === "NICHT_ABGABEPFLICHTIG");
  const complete = !open && !evaluation.configError && evaluation.rateBps !== null && uncategorisedPositionIds.length === 0;
  const totalBasisCents = complete ? decidedBasis : nothingDue ? 0 : null;
  const totalLevyCents = complete && evaluation.rateBps !== null
    ? levyCents(decidedBasis, evaluation.rateBps)
    : nothingDue
      ? 0
      : null;
  void rules;
  return { buckets, uncategorisedPositionIds, totalBasisCents, totalLevyCents, complete };
}
```

### `src/lib/domain/gates.ts`

```ts
import type { ConfirmedInvoice, Field, GateResult, ReportPosition, ValidatorCheck } from "./types";
import { UNCLEAR } from "./types";
import type { Evaluation } from "./evaluate";

function numericFieldPublished<T>(field: Field<T>, label: string): string | null {
  if (typeof field.value === "number" && field.agreement !== "einstimmig") {
    return `${label} wäre als Zahl ausgegeben, obwohl die Ablesung nicht einstimmig war.`;
  }
  if (field.agreement === "ungeklaert" && field.value !== UNCLEAR) {
    return `${label} ist weder einstimmig noch als ungeklärt gekennzeichnet.`;
  }
  return null;
}

export function gateNumbers(invoice: ConfirmedInvoice): GateResult {
  const problems: string[] = [];
  const year = numericFieldPublished(invoice.year, "Das Jahr");
  const total = numericFieldPublished(invoice.statedNetTotalCents, "Die Nettosumme");
  if (year) problems.push(year);
  if (total) problems.push(total);
  for (const position of invoice.positions) {
    const found = numericFieldPublished(position.netCents, `Der Betrag von ${position.id}`);
    if (found) problems.push(found);
  }
  return {
    id: "dreistimmigkeit_zahlen",
    title: "Dreistimmigkeit der Zahlen",
    passed: problems.length === 0,
    layperson: problems.length === 0
      ? "Jede genannte Zahl ist entweder einstimmig abgelesen oder ausdrücklich ungeklärt."
      : `Wir konnten die Zahlen nicht freigeben, weil ${problems.join(" ")}`,
  };
}

export function gateForm(invoice: ConfirmedInvoice): GateResult {
  const broken = invoice.conflicts.filter((conflict) => conflict.resolution !== "formular");
  return {
    id: "form_konsens",
    title: "Form-Konsens",
    passed: broken.length === 0,
    layperson: broken.length === 0
      ? invoice.conflicts.length
        ? "Wo Formular und Fließtext voneinander abweichen, bleibt der Formularwert."
        : "Formular und Fließtext widersprechen sich nicht."
      : "Ein abweichender Fließtext hätte den Formularwert verdrängt. Das lassen wir nicht zu.",
  };
}

export function comparableNet(invoice: ConfirmedInvoice): { sum: number | null; stated: number | null; reason: string | null } {
  if (invoice.statedNetTotalCents.value === UNCLEAR) {
    return { sum: null, stated: null, reason: "Die ausgewiesene Nettosumme ist ungeklärt. Es gibt deshalb keinen Summenwiderspruch, aber auch keine bestätigte Gesamtsumme." };
  }
  let sum = 0;
  for (const position of invoice.positions) {
    if (position.kind.value === "umsatzsteuer") continue;
    if (position.netCents.value === UNCLEAR) {
      return { sum: null, stated: invoice.statedNetTotalCents.value, reason: "Mindestens ein Nettobetrag ist ungeklärt. Die Summe lässt sich nicht gegenprüfen." };
    }
    sum += position.netCents.value;
  }
  return { sum, stated: invoice.statedNetTotalCents.value, reason: null };
}

export function gateMath(invoice: ConfirmedInvoice): GateResult {
  const compared = comparableNet(invoice);
  if (compared.sum === null || compared.stated === null) {
    return {
      id: "mathematik",
      title: "Mathematik",
      passed: true,
      layperson: compared.reason ?? "Die Summe war nicht vollständig gegenprüfbar und wird nicht als bestätigt ausgegeben.",
    };
  }
  if (compared.sum !== compared.stated) {
    return {
      id: "mathematik",
      title: "Mathematik",
      passed: false,
      layperson: `Wir konnten die Summe nicht prüfen, weil die Netto-Positionen ${format(compared.sum)} ergeben, die Rechnung aber ${format(compared.stated)} ausweist.`,
    };
  }
  return {
    id: "mathematik",
    title: "Mathematik",
    passed: true,
    layperson: "Die Netto-Positionen ergeben in Cent genau die ausgewiesene Nettosumme.",
  };
}

function format(cents: number): string {
  const euros = Math.floor(cents / 100);
  const rest = cents % 100;
  return `${euros.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${rest.toString().padStart(2, "0")} €`;
}

export function gateContent(invoice: ConfirmedInvoice): GateResult {
  const fields = [invoice.payerName, invoice.payeeName, invoice.payerRole, invoice.payeeKind, ...invoice.positions.flatMap((position) => [position.label, position.kind, position.category])];
  const broken = fields.filter((field) => field.agreement === "ungeklaert" && field.value !== UNCLEAR);
  return {
    id: "dreistimmigkeit_inhalte",
    title: "Dreistimmigkeit der Inhalte",
    passed: broken.length === 0,
    layperson: broken.length === 0
      ? "Texte und Einordnungen sind entweder wörtlich gleichlautend oder ungeklärt."
      : "Ein Inhalt wäre ohne einstimmige Ablesung in den Bericht gelangt.",
  };
}

export function runValidators(invoice: ConfirmedInvoice, evaluation: Evaluation): ValidatorCheck[] {
  const cents = [
    invoice.year.value,
    invoice.statedNetTotalCents.value,
    ...invoice.positions.map((position) => position.netCents.value),
    ...evaluation.positions.map((position) => position.amountCents),
  ];
  const badCents = cents.filter((value) => typeof value === "number" && !Number.isSafeInteger(value));
  const math = gateMath(invoice);
  const hintsOk = evaluation.positions.every((position) => !position.hint || (position.hint.classification === "ABGABEPFLICHTIG" && position.state === "ABGABEPFLICHTIG"));
  const yearKnown = typeof invoice.year.value === "number";
  return [
    {
      id: "V01",
      passed: !yearKnown || evaluation.configError === null,
      layperson: !yearKnown
        ? "Das Jahr ist ungeklärt, deshalb wird kein Abgabesatz angesetzt."
        : evaluation.configError ?? "Für das abgelesene Jahr liegt ein Abgabesatz in der Konfiguration.",
    },
    {
      id: "V02",
      passed: badCents.length === 0,
      layperson: badCents.length === 0 ? "Alle Beträge sind ganze Cent." : "Ein Betrag ist keine ganze Cent-Zahl.",
    },
    {
      id: "V03",
      passed: math.passed,
      layperson: math.layperson,
    },
    {
      id: "V04",
      passed: invoice.conflicts.every((conflict) => conflict.resolution === "formular"),
      layperson: "Konflikte zwischen Formular und Fließtext sind zugunsten des Formulars aufgelöst.",
    },
    {
      id: "V05",
      passed: hintsOk,
      layperson: hintsOk
        ? "Kein Klärungshinweis verändert die Einordnung."
        : "Ein Hinweis hätte die Einordnung verändert. Das ist unzulässig.",
    },
    {
      id: "V06",
      passed: evaluation.configError === null || evaluation.rateBps === null,
      layperson: evaluation.configError
        ? evaluation.configError
        : "Es wurde kein Ersatzsatz für ein fehlendes Jahr verwendet.",
    },
  ];
}

export function gateValidator(checks: ValidatorCheck[]): GateResult {
  const failed = checks.filter((check) => !check.passed);
  return {
    id: "validator",
    title: "Validator",
    passed: failed.length === 0,
    layperson: failed.length === 0
      ? "Die Prüfpunkte V01 bis V06 sind bestanden."
      : failed.map((check) => `${check.id}: ${check.layperson}`).join(" "),
  };
}

export function allGates(invoice: ConfirmedInvoice, evaluation: Evaluation): { gates: GateResult[]; validator: ValidatorCheck[] } {
  const validator = runValidators(invoice, evaluation);
  return {
    validator,
    gates: [gateNumbers(invoice), gateForm(invoice), gateMath(invoice), gateContent(invoice), gateValidator(validator)],
  };
}

export function codeExamine(engine: ReportPosition[], proposal: ReportPosition[]): { consistent: boolean; finding: string | null } {
  if (engine.length !== proposal.length) {
    return { consistent: false, finding: "Der Prüfer sieht eine andere Anzahl von Positionen als die Bewertung." };
  }
  for (let index = 0; index < engine.length; index += 1) {
    const left = engine[index];
    const right = proposal[index];
    if (left.id !== right.id || left.state !== right.state || left.amountCents !== right.amountCents) {
      return {
        consistent: false,
        finding: `Widerspruch bei ${left.id}: die Bewertung sagt ${left.state} und ${left.amountCents ?? "ungeklärter Betrag"}, der Prüfer weicht davon ab.`,
      };
    }
  }
  return { consistent: true, finding: null };
}
```

### `src/lib/domain/types.ts`

```ts
import type { RegisterSnapshot } from "@/lib/register-kennungen";

export const METHODOLOGY_VERSION = "v12" as const;
export const UNCLEAR = "UNGEKLÄRT" as const;

export type Unclear = typeof UNCLEAR;
export type Audience = "verein" | "steuerberater";
export type PayerRole = "typischer_verwerter" | "eigenwerbung" | "generalklausel";
export type PayeeKind = "natuerliche_person" | "gesellschaft";
export type PositionKind =
  | "honorar"
  | "material"
  | "reise"
  | "bewirtung"
  | "gemischt"
  | "drittleistung"
  | "umsatzsteuer";
export type KskCategory = "wort" | "bildende_kunst" | "musik" | "darstellende_kunst";
export type PositionState = "ABGABEPFLICHTIG" | "NICHT_ABGABEPFLICHTIG" | Unclear;
export type Agreement = "einstimmig" | "ungeklaert";
export type HintDependency = "unselbstaendig" | "eigenstaendig" | "gemischt";

export interface Field<T> {
  value: T | Unclear;
  agreement: Agreement;
  attempts: number;
  reason: string | null;
}

export interface ParsedPosition {
  label: string | null;
  kind: PositionKind | null;
  category: KskCategory | null;
  netCents: number | null;
}

export interface ParsedReading {
  readable: boolean;
  year: number | null;
  payerName: string | null;
  payerRole: PayerRole | null;
  payeeName: string | null;
  payeeKind: PayeeKind | null;
  annualSumConfirmed: boolean | null;
  statedNetTotalCents: number | null;
  positions: ParsedPosition[];
}

export interface ConfirmedPosition {
  id: string;
  label: Field<string>;
  kind: Field<PositionKind>;
  category: Field<KskCategory>;
  netCents: Field<number>;
  source: "formular" | "fliesstext" | "ungeklaert";
}

export interface ValueConflict {
  field: string;
  formValue: string;
  textValue: string;
  resolution: "formular";
}

export interface ConfirmedInvoice {
  readable: boolean;
  unreadableReason: string | null;
  year: Field<number>;
  payerName: Field<string>;
  payerRole: Field<PayerRole>;
  payeeName: Field<string>;
  payeeKind: Field<PayeeKind>;
  annualSumConfirmed: Field<boolean>;
  statedNetTotalCents: Field<number>;
  positions: ConfirmedPosition[];
  conflicts: ValueConflict[];
  notes: string[];
}

export interface ClarificationHint {
  positionId: string;
  classification: "ABGABEPFLICHTIG";
  dependency: HintDependency;
  possibleExclusionReason: string;
  citation: string;
  requiredEvidence: string;
  whenEvidenceDoesNotWork: string;
  note: string;
}

export interface ReportPosition {
  id: string;
  label: string | Unclear;
  state: PositionState;
  amountCents: number | null;
  amountState: "BESTAETIGT" | Unclear;
  category: KskCategory | Unclear;
  kind: PositionKind | Unclear;
  citation: string | null;
  rationaleLayperson: string;
  hint: ClarificationHint | null;
  source: ConfirmedPosition["source"];
}

export interface CategoryBucket {
  category: KskCategory;
  label: string;
  basisCents: number;
  levyCents: number | null;
  positionIds: string[];
}

export interface GateResult {
  id: "dreistimmigkeit_zahlen" | "form_konsens" | "mathematik" | "dreistimmigkeit_inhalte" | "validator";
  title: string;
  passed: boolean;
  layperson: string;
}

export interface ValidatorCheck {
  id: "V01" | "V02" | "V03" | "V04" | "V05" | "V06";
  passed: boolean;
  layperson: string;
}

export interface FrozenReport {
  methodologyVersion: typeof METHODOLOGY_VERSION;
  rulesStamp: string;
  rounding: "half_up_integer_cents";
  roundingNote: string;
  libraryId: string | null;
  libraryVersion: string | null;
  readingMode: "mock" | "mistral";
  examinerMode: "code" | "mistral";
  year: number | null;
  rateBps: number | null;
  rateLabel: string | null;
  thresholdCents: number | null;
  thresholdApplies: boolean | null;
  configError: string | null;
  payerRole: PayerRole | Unclear;
  payeeKind: PayeeKind | Unclear;
  positions: ReportPosition[];
  categories: CategoryBucket[];
  uncategorisedPositionIds: string[];
  totalBasisCents: number | null;
  totalLevyCents: number | null;
  totalNote: string;
  conflicts: ValueConflict[];
  notes: string[];
  gates: GateResult[];
  validator: ValidatorCheck[];
  filingDeadline: string;
  filingSeason: boolean;
  laypersonSummary: string;
  advisorSummary: string;
  registerIds?: string[];
  registerSnapshot?: RegisterSnapshot[];
}

export interface RateYear {
  rateBps: number;
  thresholdCents: number;
  rateSource: string;
  thresholdSource: string;
}

export interface RateTable {
  stamp: string;
  rounding: "half_up_integer_cents";
  roundingNote: string;
  thresholdScope: string;
  years: Record<string, RateYear>;
}

export interface HintRule {
  kind: PositionKind;
  dependency: HintDependency;
  citation: string;
  reason: string;
  requiredEvidence: string;
  whenEvidenceDoesNotWork: string;
}

export interface ScenarioTable {
  version: string;
  stamp: string;
  roles: Record<
    PayerRole,
    { thresholdApplies: boolean; citation: string; layperson: string }
  >;
  payeeGesellschaft: {
    state: "NICHT_ABGABEPFLICHTIG";
    citation: string;
    reason: string;
  };
  includedInBase: PositionKind[];
  hints: HintRule[];
}

export interface RuleSet {
  rates: RateTable;
  scenarios: ScenarioTable;
}
```

### `src/lib/domain/report.ts`

```ts
import type { Audience, FrozenReport } from "./types";
import { METHODOLOGY_VERSION } from "./types";
import type { Evaluation } from "./evaluate";
import { totalsFromEvaluation } from "./evaluate";
import type { ConfirmedInvoice } from "./types";
import type { GateResult, ValidatorCheck } from "./types";
import type { RuleSet } from "./types";
import { formatEuro, formatPercentFromBps, isFilingSeason } from "./money";
import { CATEGORY_LABEL } from "./labels";

const CATEGORY_ORDER = ["wort", "bildende_kunst", "musik", "darstellende_kunst"] as const;

export function buildReport(input: {
  invoice: ConfirmedInvoice;
  evaluation: Evaluation;
  gates: GateResult[];
  validator: ValidatorCheck[];
  rules: RuleSet;
  libraryId: string | null;
  libraryVersion: string | null;
  readingMode: "mock" | "mistral";
  examinerMode: "code" | "mistral";
  now: Date;
}): FrozenReport {
  const totals = totalsFromEvaluation(input.evaluation, input.rules);
  const season = isFilingSeason(input.now);
  const summary = summarize(input.invoice, input.evaluation, totals.totalLevyCents, input.readingMode);
  return {
    methodologyVersion: METHODOLOGY_VERSION,
    rulesStamp: input.rules.rates.stamp,
    rounding: input.rules.rates.rounding,
    roundingNote: input.rules.rates.roundingNote,
    libraryId: input.libraryId,
    libraryVersion: input.libraryVersion,
    readingMode: input.readingMode,
    examinerMode: input.examinerMode,
    year: input.evaluation.year,
    rateBps: input.evaluation.rateBps,
    rateLabel: input.evaluation.rateLabel,
    thresholdCents: input.evaluation.thresholdCents,
    thresholdApplies: input.evaluation.thresholdApplies,
    configError: input.evaluation.configError,
    payerRole: input.invoice.payerRole.value,
    payeeKind: input.invoice.payeeKind.value,
    positions: input.evaluation.positions,
    categories: totals.buckets.map((bucket) => ({
      ...bucket,
      label: CATEGORY_LABEL[bucket.category],
    })),
    uncategorisedPositionIds: totals.uncategorisedPositionIds,
    totalBasisCents: totals.totalBasisCents,
    totalLevyCents: totals.totalLevyCents,
    totalNote: totalNote(input.evaluation, totals.totalLevyCents),
    conflicts: input.invoice.conflicts,
    notes: input.invoice.notes,
    gates: input.gates,
    validator: input.validator,
    filingDeadline: "31. März (§ 27 Abs. 1 KSVG)",
    filingSeason: season,
    laypersonSummary: summary.lay,
    advisorSummary: summary.advisor,
    registerIds: input.evaluation.registerIds,
    registerSnapshot: input.evaluation.registerSnapshot,
  };
}

function totalNote(evaluation: Evaluation, levy: number | null): string {
  if (evaluation.configError) return evaluation.configError;
  if (levy === null) {
    return "Es wird keine Abgabe als geschuldet ausgewiesen. Dafür fehlen eine vollständige Einordnung, ein bestätigter Betrag oder der Abgabesatz.";
  }
  if (evaluation.thresholdResult === "ueberstiegen" && evaluation.thresholdApplies) {
    return "Die Grenze ist überschritten. Ausgewiesen ist nur die Abgabe auf die Beträge dieses Falls. Weitere Entgelte desselben Jahres liegen hier nicht vor.";
  }
  return `Ausgewiesen ist die Abgabe auf die bestätigte Bemessungsgrundlage mit ${evaluation.rateBps ? formatPercentFromBps(evaluation.rateBps) : "ungeklärtem Satz"}.`;
}

function summarize(invoice: ConfirmedInvoice, evaluation: Evaluation, levy: number | null, readingMode: "mock" | "mistral"): { lay: string; advisor: string } {
  const mode = readingMode === "mock"
    ? " Die Ablesung lief im Mock-Modus und ist keine Mistral-Prüfung."
    : "";
  if (!invoice.readable) {
    const text = `Wir konnten die Rechnung nicht prüfen, weil sie nicht übereinstimmend lesbar war. Das sagt nichts darüber, ob eine Abgabe anfällt.${mode}`;
    return { lay: text, advisor: text };
  }
  const unclear = evaluation.positions.filter((position) => position.state === "UNGEKLÄRT").length;
  const due = evaluation.positions.filter((position) => position.state === "ABGABEPFLICHTIG").length;
  const lay = unclear > 0
    ? `${unclear} Position${unclear === 1 ? "" : "en"} bleiben ungeklärt. ${due} Position${due === 1 ? " ist" : "en sind"} als abgabepflichtig eingeordnet. Eine Abgabe wird ${levy === null ? "nicht als Betrag ausgewiesen" : `mit ${formatEuro(levy)} auf der bestätigten Bemessungsgrundlage ausgewiesen`}.${mode}`
    : `Alle Positionen sind eingeordnet. ${levy === null ? "Eine Abgabe wird nicht ausgewiesen." : `Die Abgabe auf der bestätigten Bemessungsgrundlage beträgt ${formatEuro(levy)}.`} ${mode}`.trim();
  const advisor = `Methodik ${METHODOLOGY_VERSION}, Quellenstand ${evaluation.rateLabel ?? "ohne Satzfundstelle"}. Bemessungsgrundlage und Abgabe nur, wo die Tore das tragen. ${lay}`;
  return { lay, advisor };
}

export function audienceSummary(report: FrozenReport, audience: Audience): string {
  return audience === "steuerberater" ? report.advisorSummary : report.laypersonSummary;
}

export const categoryOrder = CATEGORY_ORDER;
```

### `src/lib/pipeline/run.ts`

```ts
import { modelConfig, readModels, llmMode } from "../config";
import { loadRules } from "../domain/rules";
import { readingsAgree } from "../domain/consensus";
import { parseModelJson } from "../domain/parse-reading";
import { reconcile } from "../domain/reconcile";
import { evaluateInvoice } from "../domain/evaluate";
import { allGates, codeExamine } from "../domain/gates";
import { buildReport } from "../domain/report";
import { METHODOLOGY_VERSION } from "../domain/types";
import type { ParsedReading } from "../domain/types";
import type { StageReading } from "../domain/reconcile";
import type { LlmClient } from "../llm/types";
import { createLlmClient } from "../llm";
import {
  addArtifact,
  activeLibrary,
  clearTemporaryArtifacts,
  getRun,
  insertReport,
  listDocuments,
  setCaseStatus,
  updateRun,
} from "../db";
import { dataDir } from "../config";
import { createLocalStorage } from "../storage";
import { captureError } from "../errors";
import { prepareDocument, type PreparedDocument } from "./prepare";

const READ_JSON = `Antworte nur mit JSON dieser Form: {"readable":true,"year":2025,"payerName":null,"payerRole":null,"payeeName":null,"payeeKind":null,"annualSumConfirmed":null,"statedNetTotalCents":null,"positions":[{"label":null,"kind":null,"category":null,"netCents":null}]}. Null heißt: nicht lesbar. Erlaubte payerRole: typischer_verwerter, eigenwerbung, generalklausel. Erlaubte payeeKind: natuerliche_person, gesellschaft. Erlaubte kind: honorar, material, reise, bewirtung, gemischt, drittleistung, umsatzsteuer. Erlaubte category: wort, bildende_kunst, musik, darstellende_kunst. netCents sind ganze Cent. Rate nicht.`;

function documentText(prepared: PreparedDocument): string {
  return prepared.pages.map((page) => `Seite ${page.number}\n${page.text}`).join("\n\n");
}

async function readStage(input: {
  runId: string;
  stage: "B" | "C";
  system: string;
  prepared: PreparedDocument;
  client: LlmClient;
}): Promise<StageReading> {
  const models = readModels();
  let reason = "Drei Versuche ohne gleichlautende Ablesung.";
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    const voices = await Promise.all(models.map(async (model) => {
      const result = await input.client.complete({
        endpoint: "ablesung",
        model,
        system: input.system,
        user: documentText(input.prepared),
        images: input.prepared.image ? [input.prepared.image] : undefined,
        json: true,
      });
      return parseModelJson(result.text);
    }));
    const parsed = voices.filter((voice): voice is ParsedReading => voice !== null);
    if (parsed.length === 3 && readingsAgree(parsed)) {
      addArtifact(input.runId, input.stage, { attempt, agreed: true, reading: parsed[0] }, true);
      return { parsed: parsed[0], attempts: attempt, agreed: true, reason: null };
    }
    reason = parsed.length < 3
      ? "Eine Ablesung war kein gültiges JSON."
      : "Die drei Ablesungen waren nicht gleichlautend.";
  }
  addArtifact(input.runId, input.stage, { attempt: 3, agreed: false, reason }, false);
  return { parsed: null, attempts: 3, agreed: false, reason };
}

function stop(runId: string, caseId: string, status: string, message: string, extra?: { gates?: unknown; finding?: string }): void {
  updateRun(runId, {
    status,
    current_stage: status,
    error_layperson: message,
    gate_report_json: extra?.gates ? JSON.stringify(extra.gates) : undefined,
    examiner_finding: extra?.finding,
    completed_at: new Date().toISOString(),
  });
  setCaseStatus(caseId, status === "completed" ? "bericht" : "gestoppt");
  clearTemporaryArtifacts(runId);
}

export async function executeRun(runId: string, client?: LlmClient): Promise<void> {
  const run = getRun(runId);
  if (!run) return;
  const llm = client ?? createLlmClient();
  const mode = client ? "mock" : llmMode();
  try {
    updateRun(runId, { status: "running", current_stage: "A" });
    setCaseStatus(run.case_id, "in_pruefung");
    const document = listDocuments(run.case_id).at(-1);
    if (!document) {
      stop(runId, run.case_id, "failed", "Wir konnten die Prüfung nicht starten, weil keine Rechnung gespeichert ist.");
      return;
    }
    const bytes = await createLocalStorage(`${dataDir()}/storage`).get(document.storage_key);
    const prepared = await prepareDocument(bytes, document.mime_type);
    addArtifact(runId, "A", { pageCount: prepared.pageCount, metadata: prepared.metadata, pages: prepared.pages.map((page) => ({ number: page.number, hasTextLayer: page.hasTextLayer, chars: page.text.length })) }, true);

    updateRun(runId, { current_stage: "B" });
    const form = await readStage({
      runId,
      stage: "B",
      prepared,
      client: llm,
      system: `Du liest nur Formularfelder, Tabellen und beschriftete Kästchen. Fließtext, den du nicht als Feld siehst, bleibt null. ${READ_JSON}`,
    });
    updateRun(runId, { current_stage: "C" });
    const prose = await readStage({
      runId,
      stage: "C",
      prepared,
      client: llm,
      system: `Du liest nur Fließtext und Sätze. Reine Kästchen ohne Satz bleiben null. ${READ_JSON}`,
    });
    updateRun(runId, { current_stage: "D" });
    const invoice = reconcile(form, prose);
    addArtifact(runId, "D", invoice, true);

    const rules = loadRules();
    const preliminary = evaluateInvoice(invoice, rules);
    const checked = allGates(invoice, preliminary);
    const early = checked.gates.filter((gate) => gate.id !== "validator" && !gate.passed);
    if (early.length) {
      stop(runId, run.case_id, "gate_failed", early.map((gate) => gate.layperson).join(" "), { gates: checked });
      return;
    }
    if (checked.gates.some((gate) => !gate.passed)) {
      stop(runId, run.case_id, "gate_failed", checked.gates.filter((gate) => !gate.passed).map((gate) => gate.layperson).join(" "), { gates: checked });
      return;
    }

    updateRun(runId, { current_stage: "E" });
    const library = activeLibrary();
    let proposal = preliminary.positions;
    let examinerMode: "code" | "mistral" = "code";
    if (mode === "mistral" && library?.mistral_library_id) {
      examinerMode = "mistral";
      const models = modelConfig();
      const evaluation = await llm.complete({
        endpoint: "bewertung",
        model: models.evaluate,
        libraryId: library.mistral_library_id,
        json: true,
        system: "Bewerte ausschließlich nach der Methodik v12 in der Library. Übernimm Beträge unverändert. Erfinde keine Fundstelle. Antworte mit JSON {\"positions\":[{\"id\":\"p1\",\"state\":\"ABGABEPFLICHTIG\",\"amountCents\":0}]}.",
        user: JSON.stringify({ positionen: preliminary.positions.map((position) => ({ id: position.id, state: position.state, amountCents: position.amountCents })) }),
      });
      const parsed = JSON.parse(evaluation.text) as { useEngine?: boolean; positions?: typeof proposal };
      if (!parsed.useEngine && parsed.positions) proposal = parsed.positions as typeof proposal;
      updateRun(runId, { current_stage: "F" });
      const examiner = await llm.complete({
        endpoint: "pruefer",
        model: models.examiner,
        libraryId: library.mistral_library_id,
        json: true,
        system: "Prüfe, ob die Bewertung der Methodik v12 widerspricht. Antworte mit JSON {\"consistent\":true,\"finding\":null}. Bei Widerspruch consistent false und einen kurzen Befund.",
        user: JSON.stringify({ bewertung: preliminary.positions, vorschlag: proposal }),
      });
      const verdict = JSON.parse(examiner.text) as { consistent?: boolean; finding?: string | null };
      const code = codeExamine(preliminary.positions, proposal);
      if (verdict.consistent === false || !code.consistent) {
        stop(runId, run.case_id, "examiner_stop", "Wir konnten keinen Bericht ausgeben, weil die Bewertung und der Prüfer sich widersprechen.", {
          finding: verdict.finding || code.finding || "Widerspruch ohne weiteren Befund.",
          gates: checked,
        });
        return;
      }
    } else {
      const verdict = await llm.complete({
        endpoint: "pruefer",
        model: modelConfig().examiner,
        json: true,
        system: "Prüfer im Code-Pfad.",
        user: "pruefer",
      });
      const parsed = JSON.parse(verdict.text) as { consistent?: boolean; finding?: string | null };
      const code = codeExamine(preliminary.positions, proposal);
      if (parsed.consistent === false || !code.consistent) {
        stop(runId, run.case_id, "examiner_stop", "Wir konnten keinen Bericht ausgeben, weil der Prüfer der Bewertung widerspricht.", {
          finding: parsed.finding || code.finding || "Widerspruch.",
          gates: checked,
        });
        return;
      }
    }

    updateRun(runId, { current_stage: "G" });
    const report = buildReport({
      invoice,
      evaluation: preliminary,
      gates: checked.gates,
      validator: checked.validator,
      rules,
      libraryId: library?.mistral_library_id ?? null,
      libraryVersion: library?.version_label ?? null,
      readingMode: mode === "mistral" ? "mistral" : "mock",
      examinerMode,
      now: new Date(),
    });
    insertReport({ runId, caseId: run.case_id, methodologyVersion: METHODOLOGY_VERSION, payload: report });
    updateRun(runId, { status: "completed", current_stage: "G", gate_report_json: JSON.stringify(checked), completed_at: new Date().toISOString() });
    setCaseStatus(run.case_id, "bericht");
    clearTemporaryArtifacts(runId);
  } catch (error) {
    captureError("pipeline", error);
    const message = error instanceof Error && error.message.startsWith("Wir konnten")
      ? error.message
      : "Wir konnten die Prüfung nicht zu Ende führen. Es liegt kein Bericht vor.";
    stop(runId, run.case_id, "failed", message);
  }
}
```

### `src/lib/pipeline/queue.ts`

```ts
import { claimNextJob, finishJob } from "../db";
import { captureError } from "../errors";
import { runSaasKiKernel } from "../saas-ki-kernel";

let chain: Promise<void> = Promise.resolve();

export function kickQueue(): Promise<void> {
  chain = chain.then(() => drain()).catch((error) => captureError("queue", error));
  return chain;
}

async function drain(): Promise<void> {
  for (;;) {
    const job = claimNextJob();
    if (!job) return;
    try {
      await runSaasKiKernel({ auftrag: "fall", runId: job.runId });
      finishJob(job.id, null);
    } catch (error) {
      captureError("job", error);
      finishJob(job.id, error instanceof Error ? error.message : "fehlgeschlagen");
    }
  }
}
```

### `src/lib/config.ts`

```ts
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import models from "../../config/models.json";
import app from "../../config/app.json";

export interface ModelConfig {
  readSmall: string;
  readMedium: string;
  readLarge: string;
  evaluate: string;
  examiner: string;
  chat: string;
}

export interface AppConfig {
  maxUploadBytes: number;
  allowedMimeTypes: string[];
  methodologyVersion: string;
  rulesStamp: string;
  filingDeadlineMonth: number;
  filingDeadlineDay: number;
}

export function modelConfig(): ModelConfig {
  return models;
}

export function appConfig(): AppConfig {
  return app;
}

export function readModels(): string[] {
  return [models.readSmall, models.readMedium, models.readLarge];
}

export function dataDir(): string {
  return path.resolve(/*turbopackIgnore: true*/ process.cwd(), process.env.KSK_DATA_DIR || "data");
}

function switchFile(): string {
  return path.join(dataDir(), "mistral-enabled.json");
}

export function mistralUseEnabled(): boolean {
  try {
    const parsed = JSON.parse(readFileSync(switchFile(), "utf8")) as { enabled?: boolean };
    return parsed.enabled !== false;
  } catch {
    return true;
  }
}

export function setMistralUseEnabled(enabled: boolean): void {
  mkdirSync(dataDir(), { recursive: true });
  writeFileSync(switchFile(), JSON.stringify({ enabled }), "utf8");
  if (enabled) {
    if (process.env.KSK_LLM_MODE === "mock") delete process.env.KSK_LLM_MODE;
  } else {
    process.env.KSK_LLM_MODE = "mock";
  }
}

export function llmMode(): "mock" | "mistral" {
  if (!mistralUseEnabled()) return "mock";
  if (process.env.KSK_LLM_MODE === "mock") return "mock";
  if (process.env.KSK_LLM_MODE === "mistral") return "mistral";
  return process.env.MISTRAL_API_KEY ? "mistral" : "mock";
}

export function projectPath(...parts: string[]): string {
  return path.join(/*turbopackIgnore: true*/ process.cwd(), ...parts);
}

export function readMethodology(): string {
  return readFileSync(projectPath("rules", "prompt-v12.md"), "utf8");
}
```

### `src/app/api/mistral-test/ask/route.ts`

```ts
import { json, readBody } from "@/lib/http";
import { explainMistralError, MistralConfigError } from "@/lib/rag-retrieval";
import { runSaasKiKernel } from "@/lib/saas-ki-kernel";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await readBody<{ question?: string }>(request);
    const result = await runSaasKiKernel({ auftrag: "rag", frage: body?.question ?? "" });
    return json({ ...result.rag, paket: result.paket, validierung: result.validierung, konsensIstKeineFreigabe: result.konsensIstKeineFreigabe, hinweise: result.hinweise, widersprueche: result.widersprueche });
  } catch (error) {
    if (error instanceof MistralConfigError) return json({ error: error.message }, 400);
    const message = error instanceof Error ? error.message : `Die Frage ist fehlgeschlagen, weil ${explainMistralError(error)}`;
    return json({ error: message.startsWith("Die ") ? message : `Die Frage ist fehlgeschlagen, weil ${message}` }, 400);
  }
}
```

## Datenbankschema

Auszug aus `src/lib/db.ts`. Die Zeilen dazwischen, die Fälle, Dokumente und Chats anlegen, sind ausgelassen.


### `src/lib/db.ts`, Zeilen 105–321

```ts
function migrate(database: DatabaseSync): void {
  database.exec(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS cases (
      id TEXT PRIMARY KEY,
      user_id TEXT,
      org_id TEXT,
      title TEXT NOT NULL,
      audience TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      deleted_at TEXT
    );
    CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      kind TEXT NOT NULL,
      storage_key TEXT NOT NULL,
      original_name TEXT NOT NULL,
      mime_type TEXT NOT NULL,
      size_bytes INTEGER NOT NULL,
      page_count INTEGER,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS runs (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      methodology_version TEXT NOT NULL,
      library_id TEXT,
      library_version TEXT,
      status TEXT NOT NULL,
      current_stage TEXT,
      gate_report_json TEXT,
      error_layperson TEXT,
      examiner_finding TEXT,
      reading_mode TEXT,
      created_at TEXT NOT NULL,
      completed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS stage_artifacts (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      stage TEXT NOT NULL,
      confirmed INTEGER NOT NULL,
      temporary INTEGER NOT NULL,
      payload_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reports (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      report_version INTEGER NOT NULL,
      methodology_version TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS chat_messages (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      report_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      mode TEXT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      citations_json TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reference_libraries (
      id TEXT PRIMARY KEY,
      mistral_library_id TEXT,
      name TEXT NOT NULL,
      description TEXT,
      version_label TEXT NOT NULL,
      is_active INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reference_documents (
      id TEXT PRIMARY KEY,
      library_id TEXT NOT NULL,
      mistral_file_id TEXT,
      mistral_document_id TEXT,
      name TEXT NOT NULL,
      status TEXT NOT NULL,
      page_count INTEGER,
      summary TEXT,
      error TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS llm_usage (
      id TEXT PRIMARY KEY,
      endpoint TEXT NOT NULL,
      model TEXT NOT NULL,
      prompt_tokens INTEGER NOT NULL,
      completion_tokens INTEGER NOT NULL,
      total_tokens INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      status TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      error TEXT,
      created_at TEXT NOT NULL,
      locked_at TEXT,
      finished_at TEXT
    );
    CREATE TABLE IF NOT EXISTS zahlen_register (
      id TEXT PRIMARY KEY,
      gruppe TEXT NOT NULL,
      version INTEGER NOT NULL,
      betrag REAL,
      einheit TEXT NOT NULL,
      gueltig_ab TEXT NOT NULL,
      gueltig_bis TEXT,
      quelle TEXT NOT NULL,
      freigabe TEXT NOT NULL,
      beschreibung TEXT NOT NULL,
      thema TEXT,
      stichworte_json TEXT,
      bedingung TEXT,
      created_at TEXT NOT NULL,
      wert_cent INTEGER,
      wert_exakt TEXT,
      wert_bps INTEGER,
      anwendungsbereich TEXT,
      fundstelle TEXT,
      dokumentstand TEXT,
      freigabe_nachweis TEXT,
      herkunft TEXT
    );
    CREATE TABLE IF NOT EXISTS zahlen_revisionen (
      id TEXT PRIMARY KEY,
      zeile_id TEXT NOT NULL,
      aktion TEXT NOT NULL,
      zustand_json TEXT NOT NULL,
      grund TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
  `);
  const stamp = new Date().toISOString();
  const note = database.prepare("INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?, ?)");
  note.run("001-phase1", stamp);
  note.run("002-zahlen-register", stamp);
  for (const [name, ddl] of [
    ["wert_cent", "INTEGER"],
    ["wert_exakt", "TEXT"],
    ["wert_bps", "INTEGER"],
    ["anwendungsbereich", "TEXT"],
    ["fundstelle", "TEXT"],
    ["dokumentstand", "TEXT"],
    ["freigabe_nachweis", "TEXT"],
    ["herkunft", "TEXT"],
  ] as const) {
    addColumn(database, "zahlen_register", name, ddl);
  }
  addColumn(database, "reports", "register_ids_json", "TEXT");
  addColumn(database, "reports", "register_snapshot_json", "TEXT");
  database.exec("DROP INDEX IF EXISTS zahlen_register_fassung");
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS zahlen_register_version
      ON zahlen_register (gruppe, version)`);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS zahlen_freigegeben_anfang
      ON zahlen_register (gruppe, anwendungsbereich, gueltig_ab, wert_exakt)
      WHERE freigabe = 'freigegeben'`);
  korrigiereImportfreigaben(database);
  note.run("003-zahlen-freigabe", stamp);
}

function addColumn(database: DatabaseSync, table: string, name: string, ddl: string): void {
  const cols = database.prepare(`PRAGMA table_info(${table})`).all() as Array<{ name: string }>;
  if (cols.some((col) => col.name === name)) return;
  database.exec(`ALTER TABLE ${table} ADD COLUMN ${name} ${ddl}`);
}

export function korrigiereImportfreigaben(database?: DatabaseSync): number {
  const db = database ?? getDb();
  const rows = db.prepare(`SELECT * FROM zahlen_register
    WHERE freigabe = 'freigegeben' AND (freigabe_nachweis IS NULL OR freigabe_nachweis = '')`).all() as Array<Record<string, unknown>>;
  if (rows.length === 0) return 0;
  const stamp = new Date().toISOString();
  const revision = db.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
    VALUES (?, ?, 'freigabe_korrigiert', ?, ?, ?)`);
  const update = db.prepare(`UPDATE zahlen_register
    SET freigabe = 'entwurf', herkunft = COALESCE(herkunft, 'import')
    WHERE id = ? AND freigabe = 'freigegeben' AND (freigabe_nachweis IS NULL OR freigabe_nachweis = '')`);
  db.exec("BEGIN IMMEDIATE");
  try {
    for (const row of rows) {
      revision.run(
        crypto.randomUUID(),
        String(row.id),
        JSON.stringify(row),
        "Import ohne Freigabenachweis. Der Status wird auf Entwurf gesetzt. Der vorherige Zustand liegt in zahlen_revisionen.",
        stamp,
      );
      update.run(String(row.id));
    }
    db.exec("COMMIT");
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
  return rows.length;
}
```

Auslassung: `createCase` bis `updateRun`.


### `src/lib/db.ts`, Zeilen 396–416

```ts
export function addArtifact(runId: string, stage: string, payload: unknown, confirmed: boolean, temporary = true): void {
  getDb().prepare(`INSERT INTO stage_artifacts (id, run_id, stage, confirmed, temporary, payload_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), runId, stage, confirmed ? 1 : 0, temporary ? 1 : 0, JSON.stringify(payload), now());
}

export function clearTemporaryArtifacts(runId: string): void {
  getDb().prepare("DELETE FROM stage_artifacts WHERE run_id = ? AND temporary = 1").run(runId);
}

export function insertReport(input: { runId: string; caseId: string; methodologyVersion: string; payload: unknown }): ReportRow {
  const id = crypto.randomUUID();
  const version = Number((getDb().prepare("SELECT COUNT(*) AS n FROM reports WHERE case_id = ?").get(input.caseId) as { n: number }).n) + 1;
  const payload = input.payload as { registerIds?: string[]; registerSnapshot?: unknown };
  const ids = Array.isArray(payload?.registerIds) ? JSON.stringify(payload.registerIds) : null;
  const snapshot = payload?.registerSnapshot === undefined ? null : JSON.stringify(payload.registerSnapshot);
  getDb().prepare(`INSERT INTO reports (id, run_id, case_id, user_id, org_id, report_version, methodology_version, payload_json, created_at, register_ids_json, register_snapshot_json)
    VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)`).run(
    id, input.runId, input.caseId, version, input.methodologyVersion, JSON.stringify(input.payload), now(), ids, snapshot,
  );
  return getReportByCase(input.caseId)!;
}
```

Auslassung: der Rest von `src/lib/db.ts`.


## Konfiguration und Saatdaten

`daten/zahlen-werte.json` ist die öffentliche Saatvorlage. Ein Import daraus wird im Register ein Entwurf. Die Datei selbst ist keine Freigabe.

`rules/saetze.json` enthält weiterhin Jahreswerte. `satzlage` liest sie für die Abgabe nicht.


### `config/app.json`

```json
{
  "maxUploadBytes": 20971520,
  "allowedMimeTypes": ["application/pdf", "image/png", "image/jpeg"],
  "methodologyVersion": "v12",
  "rulesStamp": "2026-10-05",
  "filingDeadlineMonth": 3,
  "filingDeadlineDay": 31
}
```

### `config/models.json`

```json
{
  "readSmall": "mistral-small-4",
  "readMedium": "mistral-medium-3.5",
  "readLarge": "mistral-large-3",
  "evaluate": "mistral-medium-3.5",
  "examiner": "mistral-large-3",
  "chat": "mistral-medium-3.5"
}
```

### `config/rag-pruefer.json`

```json
{
  "pruefer": [
    { "id": "P1", "label": "Prüfer 1 (medium)", "modell": "mistral-medium-latest" },
    { "id": "P2", "label": "Prüfer 2 (large)", "modell": "mistral-large-latest" }
  ],
  "angezeigte_antwort": "P2"
}
```

### `rules/saetze.json`

```json
{
  "stamp": "2026-10-05",
  "rounding": "half_up_integer_cents",
  "roundingNote": "Abgabe in Cent = (Bemessungsgrundlage in Cent × Satz in Basispunkten + 5000) ÷ 10000, ganzzahlig abgerundet. Das ist kaufmännisches Runden auf ganze Cent. In der Prüfung gibt es keine Fließkomma-Beträge.",
  "thresholdScope": "Die Jahresgrenze gilt nur für § 24 Abs. 2 KSVG (Eigenwerbung und Generalklausel). Typische Verwerter nach § 24 Abs. 1 haben diese Grenze nicht. Wird die Grenze überschritten, ist die gesamte Jahressumme Bemessungsgrundlage, nicht nur der übersteigende Teil.",
  "years": {
    "2025": {
      "rateBps": 500,
      "thresholdCents": 70000,
      "rateSource": "Künstlersozialkasse, Abgabesatz für 2025: 5,0 Prozent",
      "thresholdSource": "§ 54 KSVG: abweichend von § 24 Abs. 2 Satz 2 beträgt die Entgeltsumme im Kalenderjahr 2025 700 Euro"
    },
    "2026": {
      "rateBps": 490,
      "thresholdCents": 100000,
      "rateSource": "Künstlersozialkasse, Abgabesatz für 2026: 4,9 Prozent",
      "thresholdSource": "§ 24 Abs. 2 Satz 2 KSVG, Stand der Quelle Q-KSVG@2026-10-05: 1.000 Euro"
    }
  }
}
```

### `daten/zahlen-werte.json`

```json
{
  "liste_stand": "2026-10-06",
  "letzte_aenderung": "2026-10-07",
  "wertegruppen": [
    {
      "name": "abgabepflichtgrenze_veranstalter",
      "thema": "abgabepflicht",
      "stichworte": ["abgabepflicht", "abgabepflichtgrenze"],
      "beschreibung": "Jährliche Entgeltgrenze für nicht-kommerzielle Veranstalter (z. B. Musikvereine)",
      "quelle": "Info_12_Abgabepflicht_von_Musikvereinen.pdf",
      "werte": [
        { "betrag": 450, "gueltig_ab": "2019-01-01", "gueltig_bis": "2024-12-31" },
        { "betrag": 700, "gueltig_ab": "2025-01-01", "gueltig_bis": "2025-12-31" },
        { "betrag": 1000, "gueltig_ab": "2026-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "bagatellgrenze_zahlungsvorgang",
      "thema": "bagatell",
      "stichworte": ["bagatell", "zahlungsvorgang"],
      "beschreibung": "Bagatellgrenze je einzelnen Zahlungsvorgang",
      "quelle": "KSVEntgV.pdf",
      "werte": [
        { "betrag": 20, "gueltig_ab": "2019-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "abgabesatz",
      "einheit": "prozent",
      "thema": "abgabesatz",
      "stichworte": ["abgabesatz"],
      "beschreibung": "Künstlersozialabgabe, Abgabesatz",
      "quelle": "Künstlersozialkasse, Abgabesatz",
      "werte": [
        { "betrag": 5, "gueltig_ab": "2025-01-01", "gueltig_bis": "2025-12-31" },
        { "betrag": 4.9, "gueltig_ab": "2026-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "kilometerpauschale",
      "thema": "reisekosten",
      "stichworte": ["reisekosten", "kilometer", "bewirtung"],
      "beschreibung": "Kilometerpauschale je km",
      "quelle": "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      "werte": [
        { "betrag": 0.3, "gueltig_ab": "2002-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "bewirtung_oberer_satz",
      "thema": "reisekosten",
      "stichworte": ["reisekosten", "bewirtung"],
      "beschreibung": "Bewirtungspauschale, oberer Satz",
      "quelle": "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      "werte": [
        { "betrag": 24, "gueltig_ab": "2014-01-01", "gueltig_bis": "2019-12-31" },
        { "betrag": 28, "gueltig_ab": "2020-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "bewirtung_unterer_satz",
      "thema": "reisekosten",
      "stichworte": ["reisekosten", "bewirtung"],
      "beschreibung": "Bewirtungspauschale, unterer Satz",
      "quelle": "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      "werte": [
        { "betrag": 12, "gueltig_ab": "2014-01-01", "gueltig_bis": "2019-12-31" },
        { "betrag": 14, "gueltig_ab": "2020-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "ehrenamtspauschale",
      "thema": "ehrenamt",
      "stichworte": ["ehrenamt", "ehrenamtspauschale"],
      "beschreibung": "Ehrenamtspauschale",
      "quelle": "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      "werte": [
        { "betrag": 840, "gueltig_ab": "2025-01-01", "gueltig_bis": "2025-12-31" },
        { "betrag": 960, "gueltig_ab": "2026-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "vorauszahlung_freigrenze",
      "thema": "vorauszahlung",
      "stichworte": ["vorauszahlung", "vorauszahlungspflicht"],
      "beschreibung": "Monatliche Vorauszahlung entfällt bis zu diesem Betrag (§ 27 Abs. 3 Satz 3 KSVG)",
      "quelle": "KSVG.pdf",
      "werte": [
        { "betrag": 40, "gueltig_ab": "2002-01-01", "gueltig_bis": null }
      ]
    },
    {
      "name": "bewirtung_nachweispflicht",
      "thema": "bewirtung",
      "stichworte": ["bewirtung", "einzelnachweis", "nachweispflicht"],
      "beschreibung": "Bewirtungs-Nachweispflicht",
      "bedingung": "ohne Einzelnachweis → zuzurechnen",
      "quelle": "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf",
      "werte": []
    },
    {
      "name": "ermaessigung_paragraph_50",
      "einheit": "prozent",
      "thema": "ermäßigung",
      "stichworte": ["ermäßigung", "§ 50", "paragraph 50"],
      "beschreibung": "Ermäßigung der Künstlersozialabgabe nach § 50 KSVG",
      "quelle": "KSVG.pdf",
      "werte": [
        { "betrag": 25, "gueltig_ab": "1983-01-01", "gueltig_bis": "1999-12-31" }
      ]
    }
  ]
}
```

## Tests


### `tests/saas-ki-kernel.test.ts`

```ts
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
```

### `tests/berechnungsfreigabe.ts`

```ts
import { ABGABEGRENZE, ABGABESATZ, BEREICH_ABGABESATZ, BEREICH_GRENZE } from "../src/lib/register-kennungen";
import { gebeFrei } from "../src/lib/zahlen-register";

const beleg = {
  fundstelle: "Testbeleg für die Berechnung, keine fachliche Produktfreigabe",
  dokumentstand: "2026-10-05",
};

export function stelleTestSaetzeFrei(): void {
  gebeFrei({
    gruppe: ABGABESATZ,
    beschreibung: "Künstlersozialabgabe, Abgabesatz",
    betrag: "5",
    einheit: "prozent",
    gueltigAb: "2025-01-01",
    gueltigBis: "2025-12-31",
    anwendungsbereich: BEREICH_ABGABESATZ,
    quelle: "Künstlersozialkasse, Abgabesatz für 2025: 5,0 Prozent",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABESATZ,
    beschreibung: "Künstlersozialabgabe, Abgabesatz",
    betrag: "4,9",
    einheit: "prozent",
    gueltigAb: "2026-01-01",
    gueltigBis: "2026-12-31",
    anwendungsbereich: BEREICH_ABGABESATZ,
    quelle: "Künstlersozialkasse, Abgabesatz für 2026: 4,9 Prozent",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABEGRENZE,
    beschreibung: "Jährliche Entgeltgrenze für nicht-kommerzielle Veranstalter",
    betrag: "700",
    einheit: "euro",
    gueltigAb: "2025-01-01",
    gueltigBis: "2025-12-31",
    anwendungsbereich: BEREICH_GRENZE,
    quelle: "§ 54 KSVG: Entgeltsumme im Kalenderjahr 2025 700 Euro",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABEGRENZE,
    beschreibung: "Jährliche Entgeltgrenze für nicht-kommerzielle Veranstalter",
    betrag: "1000",
    einheit: "euro",
    gueltigAb: "2026-01-01",
    gueltigBis: "2026-12-31",
    anwendungsbereich: BEREICH_GRENZE,
    quelle: "§ 24 Abs. 2 Satz 2 KSVG: 1.000 Euro",
    ...beleg,
  });
}
```

### `tests/pipeline.test.ts`

```ts
import { beforeAll, describe, expect, it } from "vitest";
import { stelleTestSaetzeFrei } from "./berechnungsfreigabe";
import { addDocument, createCase, createRun, deleteCaseFully, getCase, getDb, getReportByCase } from "@/lib/db";
import { dataDir } from "@/lib/config";
import { createLocalStorage } from "@/lib/storage";
import { createMockLlm } from "@/lib/llm/mock";
import { runSaasKiKernel } from "@/lib/saas-ki-kernel";

const marker = `---KSK-FELDER---
jahr: 2025
rolle: typischer_verwerter
empfaengerart: natuerliche_person
jahressumme: ja
summe_netto: 1000000
position: Honorar|honorar|wort|1000000
---ENDE---`;

function pdfWithText(lines: string[]): Buffer {
  const content = lines.map((line, index) => `BT /F1 12 Tf 72 ${740 - index * 16} Td (${line.replace(/[()\\]/g, "\\$&")}) Tj ET`).join("\n");
  const objects = [
    "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
    "2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n",
    "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
    `4 0 obj<</Length ${Buffer.byteLength(content)}>>stream\n${content}\nendstream\nendobj\n`,
    "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
  ];
  let out = "%PDF-1.4\n";
  const offsets = [0];
  for (const object of objects) {
    offsets.push(Buffer.byteLength(out));
    out += object;
  }
  const xref = Buffer.byteLength(out);
  out += `xref\n0 ${objects.length + 1}\n`;
  out += "0000000000 65535 f \n";
  for (let index = 1; index < offsets.length; index += 1) {
    out += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
  }
  out += `trailer<</Size ${objects.length + 1}/Root 1 0 R>>\nstartxref\n${xref}\n%%EOF`;
  return Buffer.from(out, "latin1");
}

async function storeCase(title: string, text: string) {
  const item = createCase({ title, audience: "verein" });
  const id = crypto.randomUUID();
  const key = `cases/${item.id}/${id}`;
  await createLocalStorage(`${dataDir()}/storage`).put(key, pdfWithText(text.split("\n")));
  addDocument({
    id,
    case_id: item.id,
    kind: "rechnung",
    storage_key: key,
    original_name: "rechnung.pdf",
    mime_type: "application/pdf",
    size_bytes: 100,
  });
  const run = createRun({
    caseId: item.id,
    methodologyVersion: "v12",
    libraryId: null,
    libraryVersion: null,
    readingMode: "mock",
  });
  return { item, run };
}

beforeAll(() => {
  stelleTestSaetzeFrei();
});

describe("Pipeline", () => {
  it("schreibt einen eingefrorenen Bericht und löscht den Fall vollständig", async () => {
    const { item, run } = await storeCase("Pipeline 5 Prozent", marker);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm() });
    const report = getReportByCase(item.id);
    expect(report?.methodology_version).toBe("v12");
    const payload = JSON.parse(report!.payload_json) as { totalLevyCents: number; methodologyVersion: string; registerIds?: string[]; registerSnapshot?: unknown[] };
    expect(payload.totalLevyCents).toBe(50_000);
    expect(payload.methodologyVersion).toBe("v12");
    expect(payload.registerIds).toHaveLength(2);
    expect(payload.registerSnapshot).toHaveLength(2);
    const gespeichert = report as { register_snapshot_json?: string | null };
    expect(gespeichert.register_snapshot_json).toContain("abgabesatz");
    const paket = getDb().prepare("SELECT payload_json, temporary FROM stage_artifacts WHERE run_id = ? AND stage = 'paket'").get(run.id) as { payload_json: string; temporary: number };
    expect(paket.temporary).toBe(0);
    expect(JSON.parse(paket.payload_json).version).toBe("v12");
    await deleteCaseFully(item.id, (key) => createLocalStorage(`${dataDir()}/storage`).delete(key));
    expect(getCase(item.id)).toBeNull();
    expect(getReportByCase(item.id)).toBeNull();
  });

  it("stoppt ohne Bericht, wenn der Prüfer widerspricht", async () => {
    const { item, run } = await storeCase("Widerspruch", marker);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm({ examinerConsistent: false }) });
    expect(getReportByCase(item.id)).toBeNull();
  });

  it("stoppt ohne Bericht bei einem Summenfehler", async () => {
    const broken = `---KSK-FELDER---
jahr: 2025
rolle: typischer_verwerter
empfaengerart: natuerliche_person
jahressumme: ja
summe_netto: 35000
position: A|honorar|wort|10000
position: B|honorar|musik|20000
---ENDE---`;
    const { item, run } = await storeCase("Summe", broken);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm() });
    expect(getReportByCase(item.id)).toBeNull();
  });
});
```

### `tests/zahlen-register.test.ts`

```ts
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
```

### `tests/zahlen-werte.test.ts`

```ts
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
```

### `tests/konsens.test.ts`

```ts
import { describe, expect, it } from "vitest";
import { matchedDocuments } from "../src/lib/mistral/rag-pruefung";
import { konsensVergleich, vergleicheLaeufe } from "../src/lib/model-consensus";
import { RAG_SYSTEM_PROMPT } from "../src/lib/rag-system-prompt";

const names = ["Info_12_Abgabepflicht_von_Musikvereinen.pdf", "Info_10_Ausnahmen_zur_Bemessungsgrundlage_Reise-_und_Bewirtungskosten.pdf"];

describe("Dreifach-Konsens", () => {
  it("erkennt Info 12 auch in der Kurzform", () => {
    expect(matchedDocuments("Siehe Info 12, Abschnitt Veranstalter.", names)).toEqual(["Info_12_Abgabepflicht_von_Musikvereinen.pdf"]);
  });

  it("meldet Konsens 3/3 bei gleichen Beträgen und Fundstellen", () => {
    const row = { ok: true, answer: "Grenze 1.000 € laut Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] };
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ...row },
      { id: "P2", label: "Prüfer 2 (medium)", ...row },
      { id: "P3", label: "Prüfer 3 (large)", ...row },
    ]);
    expect(result.line).toBe("✅ Konsens 3/3");
  });

  it("zeigt die Abweichung 2/3 mit den Beträgen", () => {
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P2", label: "Prüfer 2 (medium)", ok: true, answer: "600 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P3", label: "Prüfer 3 (large)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
    ]);
    expect(result.line).toBe("⚠️ Abweichung 2/3 — NICHT OK, keine Mehrheitsentscheidung");
    expect(result.detail).toContain("Prüfer 2: 600 €");
    expect(result.detail).toContain("Prüfer 1 & 3: 1.000 €");
  });

  it("lässt einen ausgefallenen Prüfer sichtbar und prüft den Konsens nicht", () => {
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ok: true, answer: "keine Aussage", documents: [] },
      { id: "P2", label: "Prüfer 2 (medium)", ok: false, answer: "", documents: [] },
      { id: "P3", label: "Prüfer 3 (large)", ok: true, answer: "keine Aussage", documents: [] },
    ]);
    expect(result.line).toBe("⚠️ nicht prüfbar (2/3 geantwortet)");
  });

  it("meldet bei zwei Prüfern nur die Übereinstimmung beider", () => {
    const row = { ok: true, answer: "Grenze 1.000 € laut Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] };
    const gleich = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (medium)", ...row },
      { id: "P2", label: "Prüfer 2 (large)", ...row },
    ]);
    expect(gleich.line).toBe("✅ Konsens 2/2");
    const verschieden = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (medium)", ok: true, answer: "1.000 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
      { id: "P2", label: "Prüfer 2 (large)", ok: true, answer: "600 € Info_12_Abgabepflicht_von_Musikvereinen.pdf", documents: [names[0]] },
    ]);
    expect(verschieden.line).toBe("❌ Kein Konsens — UNGEKLÄRT");
    expect(verschieden.line).not.toContain("2/3");
  });

  it("nimmt eine Antwort nur an, wenn drei Läufe dasselbe sagen", () => {
    const lauf = { signatur: "konsens|1000.00|Info_12", einig: true, kurz: "Prüfer 1 & 2 & 3: 1.000 € / Info_12" };
    const gleich = vergleicheLaeufe([lauf, lauf, { ...lauf }]);
    expect(gleich.status).toBe("konsens");
    expect(gleich.line).toBe("✅ Dieselbe Antwort in 3 von 3 Läufen");
    const abweichend = vergleicheLaeufe([lauf, lauf, { signatur: "anders", einig: true, kurz: "Prüfer 2: 600 €" }]);
    expect(abweichend.status).toBe("keiner");
    expect(abweichend.line).toBe("❌ Kein Konsens — die drei Läufe stimmen nicht überein");
    expect(abweichend.detail).toContain("Lauf 3: Prüfer 2: 600 €");
  });

  it("behält den System-Prompt aus Schritt 1b vollständig", () => {
    expect(RAG_SYSTEM_PROMPT.startsWith("Du bist der Zitat-Dienst eines KSK-Prüfsystems.")).toBe(true);
    expect(RAG_SYSTEM_PROMPT).toContain("## DIE GOLDENE REGEL");
    expect(RAG_SYSTEM_PROMPT).toContain("Zu dieser Frage enthalten die vorliegenden Dokumente keine Aussage.");
    expect(RAG_SYSTEM_PROMPT).toContain("## ANTWORTFORMAT");
  });
});
```

### `tests/rag-pruefung.test.ts`

```ts
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
```

### `tests/abschnitte.test.ts`

```ts
import { describe, expect, it } from "vitest";
import { dokumentZahlen, ergaenzeZahlen, fehlendeBetragszeilen, grenzenAusAntwort, parseAbschnitte, zahlenAusNachfrage } from "../src/lib/mistral/abschnitte";
import { konsensVergleich } from "../src/lib/model-consensus";
import { RAG_SYSTEM_PROMPT } from "../src/lib/rag-system-prompt";
import { nurGueltigeBetraege, vorlageAusDatei } from "../src/lib/mistral/zahlen-werte";

const answer = `KERNAUSSAGEN:
- Mindestens vier Veranstaltungen.

ZAHLEN:
- 700 € | Info 12
- 1.500 € | erfunden

NUTZERANGABEN-PRÜFUNG:
- 1.500 € | abweichend (Dokument sagt: 1.000 €, Fundstelle: Info 12)
- 400 € | nicht belegt
- 250 € | nicht belegt
- 4,9 % | nicht belegt

FUNDSTELLEN:
- Info 12, Abschnitt Nicht kommerzielle Veranstalter

LÜCKEN:
- nicht belegt`;

describe("Abschnitte", () => {
  it("toleriert fette Markdown-Überschriften", () => {
    const sections = parseAbschnitte("**ZAHLEN:**\n- 700 € | Info 12\n**NUTZERANGABEN-PRÜFUNG:**\n- 600 € | nicht belegt\n**FUNDSTELLEN:**\n- Info 12\n**LÜCKEN:**\n- nicht belegt\n**KERNAUSSAGEN:**\n- Vier Veranstaltungen.");
    expect(sections.vollstaendig).toBe(true);
    expect(sections.zahlen).toContain("700 €");
  });

  it("zerlegt die fünf Überschriften", () => {
    const sections = parseAbschnitte(answer);
    expect(sections.vollstaendig).toBe(true);
    expect(sections.zahlen).toContain("700 €");
    expect(sections.nutzerangaben).toContain("400 €");
    expect(sections.fundstellen).toContain("Info 12");
  });

  it("lässt Nutzer-Zahlen aus dem Konsens und verwirft unbelegte Zahlen im ZAHLEN-Abschnitt", () => {
    const corpus = "450 € (in 2025: 700 €, ab 2026: 1.000 €)";
    const dok = dokumentZahlen({
      answer,
      corpus,
      documentNames: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      prueferLabel: "Prüfer 3 (large)",
    });
    expect(dok.labels).toEqual(["700 €"]);
    expect(dok.keys).not.toContain("1500.00");
    expect(dok.hinweise.some((line) => line.includes("1.500 €") && line.includes("Prüfer 3"))).toBe(true);
    expect(dok.documents).toEqual(["Info_12_Abgabepflicht_von_Musikvereinen.pdf"]);
  });

  it("nutzt bei fehlender ZAHLEN-Überschrift die Rückfall-Extraktion", () => {
    const dok = dokumentZahlen({
      answer: "Die Grenze liegt bei 1.000 € laut Info 12.",
      corpus: "ab 2026: 1.000 €",
      documentNames: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      prueferLabel: "Prüfer 1 (small)",
    });
    expect(dok.hinweise[0]).toBe("⚠️ Antwortformat von Prüfer 1 abweichend — Rückfall-Extraktion verwendet");
    expect(dok.labels).toEqual(["1.000 €"]);
  });

  it("vergleicht im Konsens nur die belegten Dokument-Zahlen", () => {
    const row = {
      ok: true,
      answer: "Nutzer nannte 600 €",
      documents: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      amountKeys: ["700.00", "1000.00"],
      amountLabels: ["700 €", "1.000 €"],
    };
    const result = konsensVergleich([
      { id: "P1", label: "Prüfer 1 (small)", ...row },
      { id: "P2", label: "Prüfer 2 (medium)", ...row },
      { id: "P3", label: "Prüfer 3 (large)", ...row },
    ]);
    expect(result.line).toBe("✅ Konsens 3/3");
  });

  it("zeitprüft nur den ZAHLEN-Abschnitt und markiert unbekannte Beträge rot", () => {
    const text = `ZAHLEN:\n- 450 € | Info 12\nNUTZERANGABEN-PRÜFUNG:\n- 600 € | abweichend\nFUNDSTELLEN:\n- Info 12\nLÜCKEN:\n- nicht belegt\nKERNAUSSAGEN:\n- Grenze.`;
    expect(grenzenAusAntwort(text).map((item) => item.value)).toEqual([450]);
    const dok = dokumentZahlen({
      answer: `ZAHLEN:\n- 77 € | KSVG\nNUTZERANGABEN-PRÜFUNG:\n- keine\nFUNDSTELLEN:\n- KSVG\nLÜCKEN:\n- keine\nKERNAUSSAGEN:\n- Satz.`,
      corpus: "Die Grenze beträgt 450 Euro.",
      documentNames: ["KSVG.pdf"],
      prueferLabel: "Prüfer 2 (medium)",
      liste: vorlageAusDatei(),
    });
    expect(dok.hinweise).toContain("🔴 Unbekannter Wert: 77 € (Prüfer 2)");
    expect(dok.keys).not.toContain("77.00");
    const gueltig = nurGueltigeBetraege(["450.00", "77.00", "12.00"], ["450 €", "77 €", "12 €"], vorlageAusDatei(), 2024);
    expect(gueltig.keys).toEqual(["450.00"]);
    const konsens = konsensVergleich(["P1", "P2", "P3"].map((id, index) => ({
      id,
      label: `Prüfer ${index + 1}`,
      ok: true,
      answer: "",
      documents: ["Info_12_Abgabepflicht_von_Musikvereinen.pdf"],
      amountKeys: gueltig.keys,
      amountLabels: gueltig.labels,
    })));
    expect(konsens.line).toBe("✅ Konsens 3/3");
  });

  it("übernimmt aus der Nachfrage nur Beträge, die in der Liste stehen", () => {
    const erste = `KERNAUSSAGEN:\n- Grenze.\n\nZAHLEN:\nIn den vorliegenden Dokumenten nicht belegt\n\nNUTZERANGABEN-PRÜFUNG:\n- nicht belegt\n\nFUNDSTELLEN:\n- Info_12\n\nLÜCKEN:\n- keine Aussage`;
    const liste = ["0,30 € in Info_10", "1.000 € in Info_12", "28 € in Info_10"];
    const fehlend = fehlendeBetragszeilen(erste, liste, [0.3, 28]);
    expect(fehlend).toEqual(["0,30 € in Info_10", "28 € in Info_10"]);
    const zusatz = zahlenAusNachfrage("ZAHLEN:\n- 0,30 € | Info_10\n- 28 € | Info_10\n- 999 € | Info_10", fehlend);
    expect(zusatz).toBe("- 0,30 € | Info_10\n- 28 € | Info_10");
    const text = ergaenzeZahlen(erste, zusatz ?? "");
    expect(parseAbschnitte(text).zahlen).toContain("0,30 €");
    expect(parseAbschnitte(text).zahlen).not.toContain("nicht belegt");
    expect(parseAbschnitte(text).fundstellen).toContain("Info_10");
  });

  it("bleibt ein Auskunftsdienst und rechnet keine Sachverhalte aus", () => {
    expect(RAG_SYSTEM_PROMPT).toContain("Du rechnest nicht und entscheidest keinen Sachverhalt.");
    expect(RAG_SYSTEM_PROMPT).not.toContain("ANWENDUNG");
    expect(RAG_SYSTEM_PROMPT).not.toContain("Rechnungen sind auszuführen");
  });
});
```

### `tests/regression.test.ts`

```ts
import { readFileSync } from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { stelleTestSaetzeFrei } from "./berechnungsfreigabe";
import { confirmedFromParsed, reconcile, type StageReading } from "@/lib/domain/reconcile";
import { evaluateInvoice, totalsFromEvaluation } from "@/lib/domain/evaluate";
import { gateMath, allGates } from "@/lib/domain/gates";
import { levyCents } from "@/lib/domain/money";
import { readRuleSet } from "@/lib/domain/rules";
import type { ParsedReading } from "@/lib/domain/types";
import { buildReport } from "@/lib/domain/report";

const rules = readRuleSet();

function reading(partial: Partial<ParsedReading>): ParsedReading {
  return {
    readable: true,
    year: 2025,
    payerName: "Verlag Beispiel",
    payerRole: "typischer_verwerter",
    payeeName: "Ada Autor",
    payeeKind: "natuerliche_person",
    annualSumConfirmed: true,
    statedNetTotalCents: 0,
    positions: [],
    ...partial,
  };
}

beforeAll(() => {
  stelleTestSaetzeFrei();
});

describe("Rücktests v12", () => {
  it("rundet kaufmännisch auf ganze Cent", () => {
    expect(levyCents(1_000_000, 500)).toBe(50_000);
    expect(levyCents(10, 500)).toBe(1);
    expect(levyCents(9, 500)).toBe(0);
    expect(rules.rates.years["2027"]).toBeUndefined();
  });

  it("390-Euro-Fall bleibt ungeklärt, weil die Jahressumme fehlt", () => {
    const invoice = confirmedFromParsed(reading({
      payerRole: "eigenwerbung",
      annualSumConfirmed: false,
      statedNetTotalCents: 39000,
      positions: [{ label: "Text", kind: "honorar", category: "wort", netCents: 39000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.positions[0]?.state).toBe("UNGEKLÄRT");
    expect(evaluation.configError).toBeNull();
    const totals = totalsFromEvaluation(evaluation, rules);
    expect(totals.totalLevyCents).toBeNull();
    expect(allGates(invoice, evaluation).gates.every((gate) => gate.passed)).toBe(true);
  });

  it("5,0-Prozent-Fall auf 10.000 Euro ergibt 500 Euro", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 1_000_000,
      positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 1_000_000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    const totals = totalsFromEvaluation(evaluation, rules);
    expect(evaluation.positions[0]?.state).toBe("ABGABEPFLICHTIG");
    expect(totals.totalBasisCents).toBe(1_000_000);
    expect(totals.totalLevyCents).toBe(50_000);
    expect(evaluation.rateBps).toBe(500);
    const report = buildReport({
      invoice,
      evaluation,
      gates: allGates(invoice, evaluation).gates,
      validator: allGates(invoice, evaluation).validator,
      rules,
      libraryId: null,
      libraryVersion: null,
      readingMode: "mock",
      examinerMode: "code",
      now: new Date("2026-10-06T12:00:00Z"),
    });
    expect(report.methodologyVersion).toBe("v12");
    expect(report.categories.find((item) => item.category === "wort")?.levyCents).toBe(50_000);
  });

  it("Summenfehler lässt das Mathe-Tor scheitern", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 35000,
      positions: [
        { label: "A", kind: "honorar", category: "wort", netCents: 10000 },
        { label: "B", kind: "honorar", category: "musik", netCents: 20000 },
      ],
    }));
    const gate = gateMath(invoice);
    expect(gate.passed).toBe(false);
    expect(gate.layperson).toContain("350,00");
    expect(gate.layperson).toContain("300,00");
  });

  it("S3a: genau 700 Euro im Jahr 2025 übersteigen die Grenze nicht", () => {
    const invoice = confirmedFromParsed(reading({
      payerRole: "generalklausel",
      annualSumConfirmed: true,
      statedNetTotalCents: 70000,
      positions: [{ label: "Gestaltung", kind: "honorar", category: "bildende_kunst", netCents: 70000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.thresholdResult).toBe("nicht_ueberstiegen");
    expect(evaluation.positions[0]?.state).toBe("NICHT_ABGABEPFLICHTIG");
    expect(totalsFromEvaluation(evaluation, rules).totalLevyCents).toBe(0);
  });

  it("2027 ist ein sichtbarer Konfigurationsfehler ohne Ersatzsatz", () => {
    const invoice = confirmedFromParsed(reading({
      year: 2027,
      statedNetTotalCents: 100000,
      positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 100000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.configError).toMatch(/2027/);
    expect(evaluation.rateBps).toBeNull();
    expect(allGates(invoice, evaluation).gates.find((gate) => gate.id === "validator")?.passed).toBe(false);
  });

  it("eine einzelne Rechnung über der Grenze ist pflichtig, auch ohne weitere Belege", () => {
    const invoice = confirmedFromParsed(reading({
      year: 2026,
      payerRole: "eigenwerbung",
      annualSumConfirmed: false,
      statedNetTotalCents: 150000,
      positions: [{ label: "Kampagne", kind: "honorar", category: "wort", netCents: 150000 }],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    expect(evaluation.positions[0]?.state).toBe("ABGABEPFLICHTIG");
    expect(evaluation.rateBps).toBe(490);
    expect(totalsFromEvaluation(evaluation, rules).totalLevyCents).toBe(levyCents(150000, 490));
  });
});

describe("Formular führt", () => {
  it("behält den Formularbetrag, wenn der Fließtext abweicht", () => {
    const form: StageReading = {
      agreed: true,
      attempts: 1,
      reason: null,
      parsed: reading({
        statedNetTotalCents: 10000,
        positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 10000 }],
      }),
    };
    const text: StageReading = {
      agreed: true,
      attempts: 1,
      reason: null,
      parsed: reading({
        statedNetTotalCents: 20000,
        positions: [{ label: "Honorar", kind: "honorar", category: "wort", netCents: 20000 }],
      }),
    };
    const invoice = reconcile(form, text);
    expect(invoice.statedNetTotalCents.value).toBe(10000);
    expect(invoice.positions[0]?.netCents.value).toBe(10000);
    expect(invoice.conflicts.every((conflict) => conflict.resolution === "formular")).toBe(true);
  });
});

describe("Hinweise", () => {
  it("hängen an einer pflichtigen Reiseposition und ändern die Einordnung nicht", () => {
    const invoice = confirmedFromParsed(reading({
      statedNetTotalCents: 80000,
      positions: [
        { label: "Gage", kind: "honorar", category: "musik", netCents: 50000 },
        { label: "Fahrt", kind: "reise", category: "musik", netCents: 30000 },
      ],
    }));
    const evaluation = evaluateInvoice(invoice, rules);
    const travel = evaluation.positions[1];
    expect(travel?.state).toBe("ABGABEPFLICHTIG");
    expect(travel?.hint?.dependency).toBe("unselbstaendig");
    expect(travel?.hint?.classification).toBe("ABGABEPFLICHTIG");
    expect(travel?.hint?.note).toMatch(/erschafft ihn nicht/);
  });
});

describe("Fundstelle Werklieferung", () => {
  it("wird in der Methodik nicht als gültige Norm geführt", () => {
    const method = readFileSync(path.join(process.cwd(), "rules", "prompt-v12.md"), "utf8");
    expect(method).toContain("darf nicht zitiert werden");
    expect(method).not.toContain("Werklieferung ist nach § 23 Abs. 1 Satz 2 ausgenommen");
  });
});
```

## Testergebnisse

Ausgeführt am 7. Oktober 2026 in `C:\ksk_SaaS`.

| Befehl | Ergebnis |
|---|---|
| `npx tsc --noEmit` | Exitcode 0 |
| `npx vitest run` (erster Lauf) | 10 Dateien, 61 bestanden, 1 fehlgeschlagen. `tests/saas-ki-kernel.test.ts` erwartete den Text „kein freigegebener Abgabesatz“. Die tatsächliche Meldung lautet „kein freigegebener Wert“. |
| `npx vitest run` (zweiter Lauf, nach Anpassung nur dieser Erwartung) | 10 Dateien, 62 Tests bestanden. Laufzeit etwa 2,5 Sekunden, Start 17:33. |
| `npx next build` | Erfolgreich mit Next.js 16.4.0. Der Build-Typecheck ist ebenfalls durchgelaufen. |

Playwright und ein erneuter Browser-Durchlauf sind für diesen Export nicht ausgeführt worden.

## Bekannte Lücken

- Es gibt keine Python-Ausführung und keine Sandbox. Die Abgabe entsteht in `levyCents`.
- `client()` setzt keinen eigenen Endpunkt. Der Mistral-SDK verwendet seinen Standard-Host.
- Die RAG-Prüfer sind `mistral-medium-latest` und `mistral-large-latest`. Die Rechnungsablesung in `config/models.json` enthält weiterhin `mistral-small-4`.
- Beim RAG-Auftrag steht in `libraryVersion` der Library-Name, nicht eine Dokumentfassung. Der Auftrag wird nicht in SQLite gespeichert; das Paket steht in der HTTP-Antwort.
- Beim Fallauftrag ist das Jahr beim Speichern des Pakets noch leer und wird erst aus dem Bericht nachgezogen.
- `src/lib/saas_kernel.ts` ist eine Weiterleitung. Keine Route und kein Test importiert sie. `askLibrary` sucht die Library selbst; die Ask-Route ruft den Kernel auf.
- Die Testfreigaben in `tests/berechnungsfreigabe.ts` gelten nur für die Vitest-Datenbank. Sie sind keine fachliche Produktfreigabe. Der JSON-Import bleibt ein Entwurf, bis eine Freigabe mit Nachweis vorliegt.
- Ein früherer Browser-Check der Admin-Oberfläche hat einen Entwurf mit der Kennung `e2e_kennzahl` in der Entwicklungsdatenbank angelegt. Diese Zeile wurde für den Export nicht erneut gelesen und nicht gelöscht.
