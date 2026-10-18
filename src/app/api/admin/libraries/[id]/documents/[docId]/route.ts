import { readAdminToken } from "@/lib/admin/session";
import { deleteLibraryDocumentRow, getLibrary, getLibraryDocument } from "@/lib/db";
import { json } from "@/lib/http";
import { deleteRemoteDocument, fetchDocumentText } from "@/lib/mistral/libraries";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request, context: { params: Promise<{ id: string; docId: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id, docId } = await context.params;
  const library = getLibrary(id);
  const document = getLibraryDocument(docId);
  if (!library?.mistral_library_id || !document?.mistral_document_id) return json({ error: "Das Dokument ist nicht abrufbar." }, 404);
  const text = await fetchDocumentText(library.mistral_library_id, document.mistral_document_id);
  return json({ name: document.name, summary: document.summary, pageCount: document.page_count, text });
}

export async function DELETE(request: Request, context: { params: Promise<{ id: string; docId: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id, docId } = await context.params;
  const library = getLibrary(id);
  const document = getLibraryDocument(docId);
  if (!document || document.library_id !== id) return json({ error: "Das Dokument gehört nicht zu dieser Library." }, 404);
  if (library?.mistral_library_id && document.mistral_document_id) {
    await deleteRemoteDocument(library.mistral_library_id, document.mistral_document_id);
  }
  deleteLibraryDocumentRow(docId);
  return json({ deleted: true });
}
