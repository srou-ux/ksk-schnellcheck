import { json, readBody } from "@/lib/http";
import { createLibrary, deleteLibrary, explainMistralError, getLibrary, MistralConfigError } from "@/lib/rag-retrieval";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function fail(error: unknown): Response {
  if (error instanceof MistralConfigError) return json({ error: error.message }, 400);
  const message = error instanceof Error ? error.message : explainMistralError(error);
  return json({ error: message }, 400);
}

export async function GET(): Promise<Response> {
  try {
    return json({ library: await getLibrary() });
  } catch (error) {
    return fail(error);
  }
}

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await readBody<{ description?: string }>(request);
    return json({ library: await createLibrary(body?.description ?? "") });
  } catch (error) {
    return fail(error);
  }
}

export async function DELETE(): Promise<Response> {
  try {
    await deleteLibrary();
    return json({ ok: true });
  } catch (error) {
    return fail(error);
  }
}
