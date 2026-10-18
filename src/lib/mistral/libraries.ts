function authHeaders(): HeadersInit {
  const key = process.env.MISTRAL_API_KEY;
  if (!key) throw new Error("Wir konnten die Referenz-Library nicht ansprechen, weil kein Mistral-Zugang konfiguriert ist.");
  return { Authorization: `Bearer ${key}` };
}

async function readError(response: Response): Promise<string> {
  const text = await response.text();
  const key = process.env.MISTRAL_API_KEY ?? "";
  return text.split(key).join("[entfernter-schluessel]").slice(0, 400);
}

export async function createRemoteLibrary(name: string, description: string): Promise<string> {
  const response = await fetch("https://api.mistral.ai/v1/libraries", {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(`Wir konnten die Library nicht anlegen. ${await readError(response)}`);
  const body = await response.json() as { id?: string };
  if (!body.id) throw new Error("Mistral hat keine Library-ID zurückgegeben.");
  return body.id;
}

export async function uploadReferenceFile(input: { libraryId: string; filename: string; bytes: Buffer; mime: string }): Promise<{ fileId: string | null; documentId: string }> {
  const fileForm = new FormData();
  fileForm.set("purpose", "retrieval");
  fileForm.set("file", new Blob([new Uint8Array(input.bytes)], { type: input.mime }), input.filename);
  const fileResponse = await fetch("https://api.mistral.ai/v1/files", {
    method: "POST",
    headers: authHeaders(),
    body: fileForm,
  });
  let fileId: string | null = null;
  if (fileResponse.ok) {
    const fileBody = await fileResponse.json() as { id?: string };
    fileId = fileBody.id ?? null;
  } else if (fileResponse.status !== 422) {
    throw new Error(`Wir konnten die Datei nicht an Mistral geben. ${await readError(fileResponse)}`);
  }

  const docForm = new FormData();
  docForm.set("file", new Blob([new Uint8Array(input.bytes)], { type: input.mime }), input.filename);
  const docResponse = await fetch(`https://api.mistral.ai/v1/libraries/${input.libraryId}/documents`, {
    method: "POST",
    headers: authHeaders(),
    body: docForm,
  });
  if (!docResponse.ok) throw new Error(`Wir konnten die Datei der Library nicht zuordnen. ${await readError(docResponse)}`);
  const docBody = await docResponse.json() as { id?: string };
  if (!docBody.id) throw new Error("Mistral hat keine Dokument-ID zurückgegeben.");
  return { fileId, documentId: docBody.id };
}

export function mapProcessingStatus(status: string | null | undefined): "Running" | "Completed" | "Fehler" {
  const value = (status ?? "").toLowerCase();
  if (value === "completed" || value === "complete") return "Completed";
  if (value.includes("fail") || value.includes("error")) return "Fehler";
  return "Running";
}

export async function fetchDocumentMeta(libraryId: string, documentId: string): Promise<{ status: "Running" | "Completed" | "Fehler"; pageCount: number | null; summary: string | null }> {
  const response = await fetch(`https://api.mistral.ai/v1/libraries/${libraryId}/documents/${documentId}`, {
    headers: authHeaders(),
  });
  if (!response.ok) {
    return { status: "Fehler", pageCount: null, summary: null };
  }
  const body = await response.json() as Record<string, unknown>;
  const pageCount = typeof body.page_count === "number" ? body.page_count : typeof body.pages === "number" ? body.pages : null;
  const summary = typeof body.summary === "string" ? body.summary : null;
  return {
    status: mapProcessingStatus(String(body.processing_status ?? body.process_status ?? "")),
    pageCount,
    summary,
  };
}

export async function fetchDocumentText(libraryId: string, documentId: string): Promise<string> {
  const response = await fetch(`https://api.mistral.ai/v1/libraries/${libraryId}/documents/${documentId}/text_content`, {
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(`Wir konnten den Text nicht laden. ${await readError(response)}`);
  const body = await response.json() as { text?: string };
  return body.text ?? "";
}

export async function deleteRemoteDocument(libraryId: string, documentId: string): Promise<void> {
  const response = await fetch(`https://api.mistral.ai/v1/libraries/${libraryId}/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(`Wir konnten das Dokument nicht löschen. ${await readError(response)}`);
}

export async function deleteRemoteLibrary(libraryId: string): Promise<void> {
  const response = await fetch(`https://api.mistral.ai/v1/libraries/${libraryId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(`Wir konnten die Library nicht löschen. ${await readError(response)}`);
}
