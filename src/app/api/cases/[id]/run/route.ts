import { after } from "next/server";
import { appConfig, llmMode } from "@/lib/config";
import { activeLibrary, createRun, enqueueJob, getCase, latestRun, listDocuments } from "@/lib/db";
import { json } from "@/lib/http";
import { kickQueue } from "@/lib/pipeline/queue";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  const item = getCase(id);
  if (!item) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  if (listDocuments(id).length === 0) return json({ error: "Bitte laden Sie zuerst die Rechnung hoch." }, 400);
  const current = latestRun(id);
  if (current && (current.status === "queued" || current.status === "running")) {
    return json({ error: "Diese Rechnung wird schon geprüft." }, 409);
  }
  const library = activeLibrary();
  const run = createRun({
    caseId: id,
    methodologyVersion: appConfig().methodologyVersion,
    libraryId: library?.mistral_library_id ?? null,
    libraryVersion: library?.version_label ?? null,
    readingMode: llmMode(),
  });
  enqueueJob(run.id);
  after(() => kickQueue());
  return json({ run }, 202);
}
