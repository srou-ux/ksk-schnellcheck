import { json } from "@/lib/http";
import { deleteDocument, explainMistralError, MistralConfigError } from "@/lib/rag-retrieval";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function DELETE(_request: Request, context: { params: Promise<{ documentId: string }> }): Promise<Response> {
  try {
    const { documentId } = await context.params;
    await deleteDocument(documentId);
    return json({ ok: true });
  } catch (error) {
    if (error instanceof MistralConfigError) return json({ error: error.message }, 400);
    const message = error instanceof Error ? error.message : explainMistralError(error);
    return json({ error: message }, 400);
  }
}
