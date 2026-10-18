import { readAdminToken } from "@/lib/admin/session";
import { getLibrary, insertLibraryDocument, listLibraryDocuments, updateLibraryDocument } from "@/lib/db";
import { json } from "@/lib/http";
import { fetchDocumentMeta, uploadReferenceFile } from "@/lib/mistral/libraries";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function refresh(libraryMistralId: string, rows: ReturnType<typeof listLibraryDocuments>) {
  for (const row of rows) {
    if (!row.mistral_document_id || row.status === "Completed" || row.status === "Fehler") continue;
    const meta = await fetchDocumentMeta(libraryMistralId, row.mistral_document_id);
    updateLibraryDocument(row.id, { status: meta.status, page_count: meta.pageCount, summary: meta.summary });
  }
}

export async function GET(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id } = await context.params;
  const library = getLibrary(id);
  if (!library) return json({ error: "Diese Library ist hier nicht gespeichert." }, 404);
  if (library.mistral_library_id) await refresh(library.mistral_library_id, listLibraryDocuments(id));
  return json({ documents: listLibraryDocuments(id) });
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id } = await context.params;
  const library = getLibrary(id);
  if (!library?.mistral_library_id) return json({ error: "Die Library hat bei Mistral keine ID." }, 400);
  const form = await request.formData();
  const files = form.getAll("files").filter((item): item is File => item instanceof File);
  if (!files.length) return json({ error: "Bitte wählen Sie mindestens eine Datei." }, 400);
  const created = [];
  for (const file of files) {
    if (file.size > 512 * 1024 * 1024) return json({ error: `${file.name} ist größer als 512 MB.` }, 400);
    const bytes = Buffer.from(await file.arrayBuffer());
    try {
      const remote = await uploadReferenceFile({
        libraryId: library.mistral_library_id,
        filename: file.name,
        bytes,
        mime: file.type || "application/octet-stream",
      });
      created.push(insertLibraryDocument({
        libraryId: id,
        name: file.name,
        status: "Running",
        mistralFileId: remote.fileId,
        mistralDocumentId: remote.documentId,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload fehlgeschlagen.";
      created.push(insertLibraryDocument({
        libraryId: id,
        name: file.name,
        status: "Fehler",
        mistralFileId: null,
        mistralDocumentId: null,
      }));
      const last = created[created.length - 1];
      updateLibraryDocument(last.id, { status: "Fehler", error: message });
    }
  }
  return json({ documents: listLibraryDocuments(id) }, 201);
}
