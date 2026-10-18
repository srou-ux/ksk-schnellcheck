import { readAdminToken } from "@/lib/admin/session";
import { activateLibrary, getLibrary } from "@/lib/db";
import { json } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const { id } = await context.params;
  const library = getLibrary(id);
  if (!library) return json({ error: "Diese Library ist hier nicht gespeichert." }, 404);
  activateLibrary(id);
  return json({ active: getLibrary(id) });
}
