import { after } from "next/server";
import { json, readBody } from "@/lib/http";
import { holeVorbereitung, letzteVorbereitungen, starteJahrespaketVorbereitung } from "@/lib/jahrespaket-vorbereitung";
import { kickVorbereitungsQueue } from "@/lib/jahrespaket-vorbereitung-queue";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET(): Response {
  return json({ vorbereitungen: letzteVorbereitungen().map(serialize) });
}

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await readBody<{ jahr?: number }>(request);
    const preparation = starteJahrespaketVorbereitung(Number(body?.jahr));
    after(() => kickVorbereitungsQueue());
    return json({ vorbereitung: serialize(preparation) }, 202);
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : "Die Vorbereitung konnte nicht gestartet werden." }, 400);
  }
}

function serialize(item: NonNullable<ReturnType<typeof holeVorbereitung>>) {
  return { ...item, luecken: JSON.parse(item.luecken_json) as string[] };
}
