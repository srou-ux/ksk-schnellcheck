import { clearAdminCookieHeader, readAdminToken } from "@/lib/admin/session";
import { json } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(request: Request): Response {
  return json({ authenticated: readAdminToken(request.headers.get("cookie")) });
}

export function POST(): Response {
  return json({ ok: true }, 200, { "Set-Cookie": clearAdminCookieHeader() });
}
