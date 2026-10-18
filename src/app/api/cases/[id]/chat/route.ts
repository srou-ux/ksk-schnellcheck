import { getCase, getReportByCase, listChat, addChat, activeLibrary } from "@/lib/db";
import { CHAT_SYSTEM, buildChatUserMessage, guardAnswer, questionViolatesGuard, refusal, type ChatMode } from "@/lib/domain/chat-guard";
import type { FrozenReport } from "@/lib/domain/types";
import { json, readBody } from "@/lib/http";
import { createLlmClient } from "@/lib/llm";
import { modelConfig } from "@/lib/config";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(_request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  if (!getCase(id)) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  return json({ messages: listChat(id) });
}

export async function POST(request: Request, context: { params: Promise<{ id: string }> }): Promise<Response> {
  const { id } = await context.params;
  if (!getCase(id)) return json({ error: "Diesen Fall gibt es nicht." }, 404);
  const reportRow = getReportByCase(id);
  if (!reportRow) return json({ error: "Zum Chat braucht es einen fertigen Bericht." }, 400);
  const body = await readBody<{ question?: string; mode?: string }>(request);
  const question = body?.question?.trim() ?? "";
  const mode: ChatMode = body?.mode === "steuerberater" ? "steuerberater" : "nutzer";
  if (question.length < 2) return json({ error: "Bitte stellen Sie eine Frage zum Bericht." }, 400);
  const report = JSON.parse(reportRow.payload_json) as FrozenReport;
  addChat({ caseId: id, reportId: reportRow.id, mode, role: "user", content: question });
  if (questionViolatesGuard(question)) {
    const answer = refusal(mode);
    addChat({ caseId: id, reportId: reportRow.id, mode, role: "assistant", content: answer });
    return json({ answer, refused: true });
  }
  const library = activeLibrary();
  const payload = buildChatUserMessage(question, report, mode);
  if (payload.includes("# Prüfmethodik v12")) {
    return json({ error: "Der Chat darf die Regeldateien nicht mitschicken." }, 500);
  }
  const result = await createLlmClient().complete({
    endpoint: "chat",
    model: modelConfig().chat,
    system: CHAT_SYSTEM,
    user: payload,
    libraryId: library?.mistral_library_id ?? null,
  });
  const answer = guardAnswer(result.text, report, mode);
  addChat({ caseId: id, reportId: reportRow.id, mode, role: "assistant", content: answer });
  return json({ answer, refused: false, libraryId: library?.mistral_library_id ?? null });
}
