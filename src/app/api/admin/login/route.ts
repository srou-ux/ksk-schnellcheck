import { adminCookieHeader, adminConfigured, createAdminCookie, passwordsMatch } from "@/lib/admin/session";
import { json, readBody } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  if (!adminConfigured()) {
    return json({ error: "Das Admin-Passwort ist nicht konfiguriert. Tragen Sie ADMIN_PASSWORD in config/secrets.env ein." }, 503);
  }
  const body = await readBody<{ password?: string }>(request);
  if (!body?.password || !passwordsMatch(body.password)) {
    return json({ error: "Das Passwort stimmt nicht." }, 401);
  }
  return json({ ok: true }, 200, { "Set-Cookie": adminCookieHeader(createAdminCookie()) });
}
