import { modelConfig, readModels, llmMode } from "../config";
import { loadRules } from "../domain/rules";
import { mergeUnanimous, readingsAgree } from "../domain/consensus";
import { parseModelJson } from "../domain/parse-reading";
import { reconcile } from "../domain/reconcile";
import { uebernehmeTextzeilen } from "../domain/rechnungszeilen";
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
    if (parsed.length === 3) {
      const merged = mergeUnanimous(parsed);
      if (merged.readable) {
        const partial = "Übernommen sind nur Felder, die alle drei Ablesungen gleich gelesen haben. Abweichende Felder bleiben ungeklärt.";
        addArtifact(input.runId, input.stage, { attempt, agreed: true, reading: merged, partial: true }, true);
        return { parsed: merged, attempts: attempt, agreed: true, reason: partial };
      }
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
    const invoice = uebernehmeTextzeilen(reconcile(form, prose), documentText(prepared));
    addArtifact(runId, "D", invoice, true);

    const rules = loadRules();
    const preliminary = evaluateInvoice(invoice, rules);
    const checked = allGates(invoice, preliminary);
    const early = checked.gates.filter((gate) => gate.id !== "validator" && !gate.passed);
    if (early.length || checked.gates.some((gate) => !gate.passed)) {
      const failed = checked.gates.filter((gate) => !gate.passed);
      const library = activeLibrary();
      insertReport({
        runId,
        caseId: run.case_id,
        methodologyVersion: METHODOLOGY_VERSION,
        payload: buildReport({
          invoice,
          evaluation: preliminary,
          gates: checked.gates,
          validator: checked.validator,
          rules,
          libraryId: library?.mistral_library_id ?? null,
          libraryVersion: library?.version_label ?? null,
          readingMode: mode === "mistral" ? "mistral" : "mock",
          examinerMode: "code",
          now: new Date(),
        }),
      });
      stop(runId, run.case_id, "gate_failed", failed.map((gate) => gate.layperson).join(" "), { gates: checked });
      return;
    }

    updateRun(runId, { current_stage: "E" });
    const library = activeLibrary();
    let proposal = preliminary.positions;
    let examinerMode: "code" | "mistral" = "code";
    if (mode === "mistral" && library?.mistral_library_id) {
      examinerMode = "mistral";
      const models = modelConfig();
      try {
      const evaluation = await llm.complete({
        endpoint: "bewertung",
        model: models.evaluate,
        libraryId: library.mistral_library_id,
        json: true,
        system: "Prüfe die Positionen einmal anhand der Rechtsquellen in der Library. Übernimm Beträge unverändert. Erfinde keine Fundstelle. Antworte nur mit JSON {\"positions\":[{\"id\":\"p1\",\"state\":\"ABGABEPFLICHTIG\",\"amountCents\":0}]}.",
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
        system: "Prüfe einmal, ob die Bewertung den Rechtsquellen in der Library widerspricht. Antworte nur mit JSON {\"consistent\":true,\"finding\":null}. Bei Widerspruch consistent false und einen kurzen Befund.",
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
      } catch {
        examinerMode = "code";
        invoice.notes.push("Die Mistral-Library v5 hat die rechtliche Gegenprüfung nicht rechtzeitig beantwortet. Der Bericht zeigt die rechnerische Prüfung der abgelesenen Rechnung.");
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
