import { readAdminToken } from "@/lib/admin/session";
import { json, readBody } from "@/lib/http";
import { loadSecrets, updateSecret } from "@/lib/secrets";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(request: Request): Response {
  loadSecrets();
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const stored = Boolean(process.env.MISTRAL_API_KEY && process.env.MISTRAL_API_KEY.length > 0);
  return json({ stored, place: "config/secrets.env" });
}

export async function POST(request: Request): Promise<Response> {
  loadSecrets();
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const body = await readBody<{ apiKey?: string }>(request);
  try {
    updateSecret("MISTRAL_API_KEY", body?.apiKey ?? "");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Wir konnten den Schlüssel nicht speichern.";
    return json({ error: message }, 400);
  }
  return json({ stored: true, place: "config/secrets.env" });
}
