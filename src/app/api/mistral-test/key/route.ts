import { json } from "@/lib/http";
import { MistralConfigError, mistralConnected } from "@/lib/rag-retrieval";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(): Promise<Response> {
  try {
    return json({ status: await mistralConnected() });
  } catch (error) {
    if (error instanceof MistralConfigError) return json({ status: "nicht verbunden", error: error.message });
    return json({ status: "nicht verbunden" });
  }
}
