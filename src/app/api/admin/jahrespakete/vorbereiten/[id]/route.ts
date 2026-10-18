import { json } from "@/lib/http";
import { holeVorbereitung } from "@/lib/jahrespaket-vorbereitung";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  const item = holeVorbereitung(id);
  if (!item) return json({ error: "Diese Vorbereitung existiert nicht." }, 404);
  return json({ vorbereitung: { ...item, luecken: JSON.parse(item.luecken_json) as string[] } });
}
