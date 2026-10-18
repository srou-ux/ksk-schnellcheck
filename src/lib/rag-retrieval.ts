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
