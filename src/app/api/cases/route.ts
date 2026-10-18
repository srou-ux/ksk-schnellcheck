import { appConfig } from "@/lib/config";
import { createCase, listCases } from "@/lib/db";
import { json, readBody } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(): Response {
  return json({ cases: listCases() });
}

export async function POST(request: Request): Promise<Response> {
  const body = await readBody<{ title?: string; audience?: string }>(request);
  const title = body?.title?.trim() ?? "";
  const audience = body?.audience === "steuerberater" ? "steuerberater" : body?.audience === "verein" ? "verein" : null;
  if (title.length < 2 || title.length > 160) {
    return json({ error: "Bitte geben Sie dem Fall einen kurzen Namen, damit Sie ihn später wiederfinden." }, 400);
  }
  if (!audience) return json({ error: "Bitte wählen Sie Verein oder Fundstellen." }, 400);
  void appConfig();
  return json({ case: createCase({ title, audience }) }, 201);
}
