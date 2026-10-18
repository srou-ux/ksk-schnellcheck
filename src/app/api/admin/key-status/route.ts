import { readAdminToken } from "@/lib/admin/session";
import { llmMode, mistralUseEnabled } from "@/lib/config";
import { json } from "@/lib/http";
import { mistralKeyStatus } from "@/lib/llm/mistral";
import { loadSecrets } from "@/lib/secrets";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(request: Request): Promise<Response> {
  loadSecrets();
  if (!readAdminToken(request.headers.get("cookie"))) return json({ error: "Die Admin-Seite ist nicht angemeldet." }, 401);
  const enabled = mistralUseEnabled() && llmMode() === "mistral";
  const key = process.env.MISTRAL_API_KEY;
  if (!key) return json({ status: "nicht verbunden", enabled });
  try {
    return json({ status: await mistralKeyStatus(key), enabled });
  } catch {
    return json({ status: "nicht verbunden", enabled });
  }
}
