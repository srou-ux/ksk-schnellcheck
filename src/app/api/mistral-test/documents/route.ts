import { json } from "@/lib/http";
import { explainMistralError, MistralConfigError, uploadDocument } from "@/lib/rag-retrieval";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  try {
    const form = await request.formData();
    const files = form.getAll("files").filter((item): item is File => item instanceof File);
    if (files.length === 0) return json({ error: "Upload fehlgeschlagen, weil keine Datei angekommen ist." }, 400);
    const uploaded: string[] = [];
    const errors: string[] = [];
    for (const file of files) {
      try {
        const bytes = new Uint8Array(await file.arrayBuffer());
        await uploadDocument(file.name, bytes);
        uploaded.push(file.name);
      } catch (error) {
        const message = error instanceof MistralConfigError
          ? error.message
          : error instanceof Error
            ? error.message
            : `Upload fehlgeschlagen, weil ${explainMistralError(error)}`;
        errors.push(`${file.name}: ${message}`);
        if (error instanceof MistralConfigError) break;
      }
    }
    if (uploaded.length === 0) return json({ error: errors[0] ?? "Upload fehlgeschlagen, weil Mistral die Datei nicht angenommen hat.", errors }, 400);
    return json({ uploaded, errors });
  } catch (error) {
    if (error instanceof MistralConfigError) return json({ error: error.message }, 400);
    return json({ error: `Upload fehlgeschlagen, weil ${explainMistralError(error)}` }, 400);
  }
}
