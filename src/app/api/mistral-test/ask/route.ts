import { json, readBody } from "@/lib/http";
import { explainMistralError, MistralConfigError } from "@/lib/rag-retrieval";
import { runSaasKiKernel } from "@/lib/saas-ki-kernel";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await readBody<{ question?: string }>(request);
    const result = await runSaasKiKernel({ auftrag: "rag", frage: body?.question ?? "" });
    return json({ ...result.rag, paket: result.paket, validierung: result.validierung, konsensIstKeineFreigabe: result.konsensIstKeineFreigabe, hinweise: result.hinweise, widersprueche: result.widersprueche });
  } catch (error) {
    if (error instanceof MistralConfigError) return json({ error: error.message }, 400);
    const message = error instanceof Error ? error.message : `Die Frage ist fehlgeschlagen, weil ${explainMistralError(error)}`;
    return json({ error: message.startsWith("Die ") ? message : `Die Frage ist fehlgeschlagen, weil ${message}` }, 400);
  }
}
