import { readAdminToken } from "@/lib/admin/session";
import { deleteLibraryRow, getLibrary } from "@/lib/db";
import { json } from "@/lib/http";
import { deleteRemoteLibrary } from "@/lib/mistral/libraries";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function DELETE(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id } = await context.params;
  const library = getLibrary(id);
  if (!library) return json({ error: "Diese Library ist hier nicht gespeichert." }, 404);
  if (library.mistral_library_id) await deleteRemoteLibrary(library.mistral_library_id);
  deleteLibraryRow(id);
  return json({ deleted: true });
}
