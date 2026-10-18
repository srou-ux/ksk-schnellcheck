import { Mistral } from "@mistralai/mistralai";

const apiKey = process.env.MISTRAL_API_KEY;
if (!apiKey) throw new Error("MISTRAL_API_KEY ist für den isolierten Integrationstest nicht gesetzt.");

const model = process.env.MISTRAL_TEST_MODEL || "mistral-medium-latest";
const baseUrl = "https://api.mistral.ai/v1";
const runToken = crypto.randomUUID().replaceAll("-", "").slice(0, 16).toUpperCase();
const markerA = `KSK_ISOLATION_A_${runToken}`;
const markerB = `KSK_ISOLATION_B_${runToken}`;
const libraries = [];

function headers(json = false) {
  return { Authorization: `Bearer ${apiKey}`, ...(json ? { "Content-Type": "application/json" } : {}) };
}

async function api(path, init = {}) {
  const response = await fetch(`${baseUrl}${path}`, { ...init, headers: { ...headers(Boolean(init.body && typeof init.body === "string")), ...init.headers } });
  const text = await response.text();
  if (!response.ok) throw new Error(`Mistral ${response.status} bei ${path}: ${text.split(apiKey).join("[entfernt]").slice(0, 500)}`);
  return text ? JSON.parse(text) : null;
}

async function createLibrary(label) {
  const body = await api("/libraries", {
    method: "POST",
    body: JSON.stringify({ name: `KSK Isolation ${label} ${runToken}`, description: "Temporärer automatischer Trennungstest; nach dem Lauf löschen." }),
  });
  libraries.push(body.id);
  return body.id;
}

async function upload(libraryId, filename, marker) {
  const form = new FormData();
  const content = [
    "Fiktives Dokument ausschließlich für einen technischen Library-Trennungstest.",
    `Der eindeutige Prüfmarker lautet: ${marker}`,
    "Dieser Inhalt ist keine Rechtsquelle und enthält keine Kundendaten.",
  ].join("\n");
  form.set("file", new Blob([content], { type: "text/plain" }), filename);
  return api(`/libraries/${libraryId}/documents`, { method: "POST", body: form, headers: headers(false) });
}

async function waitForDocument(libraryId, documentId) {
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    const status = await api(`/libraries/${libraryId}/documents/${documentId}/status`);
    const normalized = String(status.processing_status || status.process_status || "").toLowerCase();
    if (["completed", "complete", "done", "noop", "self_managed"].includes(normalized)) return status;
    if (["failed", "error", "missing_content"].some((value) => normalized.includes(value))) {
      throw new Error(`Dokument ${documentId} endete mit Status ${normalized}.`);
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }
  throw new Error(`Zeitüberschreitung bei der Verarbeitung von Dokument ${documentId}.`);
}

async function textContent(libraryId, documentId) {
  return api(`/libraries/${libraryId}/documents/${documentId}/text_content`);
}

function allText(value) {
  return JSON.stringify(value);
}

async function query(libraryId, expectedMarker, forbiddenMarker, expectedDocumentId) {
  const client = new Mistral({ apiKey });
  const response = await client.beta.conversations.start({
    model,
    store: false,
    instructions: "Nutze ausschließlich die angegebene Dokument-Library. Antworte mit dem exakten Prüfmarker und liefere die verfügbare Quellenreferenz.",
    inputs: "Welcher eindeutige Prüfmarker steht im fiktiven Testdokument?",
    tools: [{ type: "document_library", libraryIds: [libraryId] }],
    completionArgs: { temperature: 0 },
  });
  const raw = allText(response);
  return {
    expectedMarkerFound: raw.includes(expectedMarker),
    forbiddenMarkerFound: raw.includes(forbiddenMarker),
    expectedDocumentIdReferenced: raw.includes(expectedDocumentId),
    outputTypes: (response.outputs || []).map((output) => output.type),
  };
}

let result;
try {
  const libraryA = await createLibrary("A");
  const libraryB = await createLibrary("B");
  const documentA = await upload(libraryA, `isolation-a-${runToken}.txt`, markerA);
  const documentB = await upload(libraryB, `isolation-b-${runToken}.txt`, markerB);

  if (documentA.library_id && documentA.library_id !== libraryA) throw new Error("Dokument A meldet eine falsche Library-ID.");
  if (documentB.library_id && documentB.library_id !== libraryB) throw new Error("Dokument B meldet eine falsche Library-ID.");

  const statusA = await waitForDocument(libraryA, documentA.id);
  const statusB = await waitForDocument(libraryB, documentB.id);
  const extractedA = await textContent(libraryA, documentA.id);
  const extractedB = await textContent(libraryB, documentB.id);
  const textAOk = allText(extractedA).includes(markerA) && !allText(extractedA).includes(markerB);
  const textBOk = allText(extractedB).includes(markerB) && !allText(extractedB).includes(markerA);
  const ragA = await query(libraryA, markerA, markerB, documentA.id);
  const ragB = await query(libraryB, markerB, markerA, documentB.id);

  result = {
    model,
    libraryA,
    libraryB,
    documentA: documentA.id,
    documentB: documentB.id,
    processingA: statusA.processing_status || statusA.process_status,
    processingB: statusB.processing_status || statusB.process_status,
    extractedTextAIsolated: textAOk,
    extractedTextBIsolated: textBOk,
    ragA,
    ragB,
  };

  const passed = textAOk && textBOk
    && ragA.expectedMarkerFound && !ragA.forbiddenMarkerFound
    && ragB.expectedMarkerFound && !ragB.forbiddenMarkerFound
    && ragA.expectedDocumentIdReferenced && ragB.expectedDocumentIdReferenced;
  result.passed = passed;
  if (!passed) process.exitCode = 2;
} finally {
  const cleanup = [];
  for (const libraryId of libraries.reverse()) {
    try {
      await api(`/libraries/${libraryId}`, { method: "DELETE", headers: headers(false) });
      cleanup.push({ libraryId, deleted: true });
    } catch (error) {
      cleanup.push({ libraryId, deleted: false, error: error instanceof Error ? error.message : String(error) });
      process.exitCode = 3;
    }
  }
  console.log(JSON.stringify({ ...result, cleanup }, null, 2));
}
