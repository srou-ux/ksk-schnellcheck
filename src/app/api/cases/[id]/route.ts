import { dataDir } from "@/lib/config";
import { deleteCaseFully, getCase, getReportByCase, latestRun, listDocuments } from "@/lib/db";
import { json } from "@/lib/http";
import { createLocalStorage } from "@/lib/storage";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  const item = getCase(id);
  if (!item) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  const reportRow = getReportByCase(id);
  return json({
    case: item,
    documents: listDocuments(id),
    run: latestRun(id),
    report: reportRow ? JSON.parse(reportRow.payload_json) : null,
    reportId: reportRow?.id ?? null,
  });
}

export async function DELETE(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  const item = getCase(id);
  if (!item) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  const storage = createLocalStorage(`${dataDir()}/storage`);
  await deleteCaseFully(id, (key) => storage.delete(key));
  return json({ deleted: true });
}
