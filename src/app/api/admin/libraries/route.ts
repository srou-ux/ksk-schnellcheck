import { readAdminToken } from "@/lib/admin/session";
import { insertLibrary, listLibraries } from "@/lib/db";
import { json, readBody } from "@/lib/http";
import { createRemoteLibrary } from "@/lib/mistral/libraries";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function denied(request: Request): Response | null {
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  return null;
}

export function GET(request: Request): Response {
  const block = denied(request);
  if (block) return block;
  return json({ libraries: listLibraries() });
}

export async function POST(request: Request): Promise<Response> {
  const block = denied(request);
  if (block) return block;
  const body = await readBody<{ name?: string; description?: string; versionLabel?: string }>(request);
  const name = body?.name?.trim() ?? "";
  const description = body?.description?.trim() ?? "";
  const versionLabel = body?.versionLabel?.trim() ?? "";
  if (name.length < 3 || versionLabel.length < 3) {
    return json({ error: "Name und Versionsbezeichnung werden beide gebraucht." }, 400);
  }
  try {
    const mistralLibraryId = await createRemoteLibrary(name, description);
    const library = insertLibrary({ name, description, versionLabel, mistralLibraryId });
    return json({ library }, 201);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Wir konnten die Library nicht anlegen.";
    return json({ error: message }, 502);
  }
}
