import { appConfig, dataDir } from "@/lib/config";
import { addDocument, getCase, listDocuments } from "@/lib/db";
import { json } from "@/lib/http";
import { createLocalStorage } from "@/lib/storage";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  const item = getCase(id);
  if (!item) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  if (listDocuments(id).length > 0) {
    return json({ error: "Für diesen Fall liegt schon eine Rechnung. Löschen Sie den Fall, wenn Sie eine andere Rechnung prüfen wollen." }, 409);
  }
  const form = await request.formData();
  const file = form.get("file");
  if (!(file instanceof File)) return json({ error: "Bitte wählen Sie eine Datei aus." }, 400);
  const config = appConfig();
  const mime = file.type === "image/jpg" ? "image/jpeg" : file.type;
  if (!config.allowedMimeTypes.includes(mime)) {
    return json({ error: "Wir können nur PDF, PNG und JPG prüfen." }, 400);
  }
  if (file.size <= 0) return json({ error: "Die Datei ist leer." }, 400);
  if (file.size > config.maxUploadBytes) {
    return json({ error: "Die Datei ist zu groß. Zulässig sind höchstens 20 MB." }, 400);
  }
  const bytes = Buffer.from(await file.arrayBuffer());
  const documentId = crypto.randomUUID();
  const storageKey = `cases/${id}/${documentId}`;
  await createLocalStorage(`${dataDir()}/storage`).put(storageKey, bytes);
  const document = addDocument({
    id: documentId,
    case_id: id,
    kind: "rechnung",
    storage_key: storageKey,
    original_name: file.name.slice(0, 180),
    mime_type: mime,
    size_bytes: bytes.length,
  });
  return json({ document }, 201);
}
