import { readAdminToken } from "@/lib/admin/session";
import { llmMode, mistralUseEnabled, setMistralUseEnabled } from "@/lib/config";
import { json, readBody } from "@/lib/http";
import { loadSecrets } from "@/lib/secrets";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(request: Request): Response {
  loadSecrets();
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  return json({ enabled: mistralUseEnabled() && llmMode() === "mistral" });
}

export async function POST(request: Request): Promise<Response> {
  loadSecrets();
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const body = await readBody<{ enabled?: boolean }>(request);
  if (typeof body?.enabled !== "boolean") return json({ error: "Bitte Ein oder Aus wählen." }, 400);
  if (body.enabled && !process.env.MISTRAL_API_KEY) {
    return json({ error: "Wir konnten Mistral nicht einschalten, weil kein Schlüssel gespeichert ist." }, 400);
  }
  setMistralUseEnabled(body.enabled);
  return json({ enabled: mistralUseEnabled() && llmMode() === "mistral" });
}
