import { PHASE2_MESSAGE } from "@/lib/phase2/nachweis";
import { json } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(): Promise<Response> {
  return json({ error: PHASE2_MESSAGE, phase: 2 }, 501);
}
