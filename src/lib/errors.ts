import { appendFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { dataDir } from "./config";

export function captureError(scope: string, error: unknown): void {
  const message = error instanceof Error ? error.message : "Unbekannter Fehler";
  const safe = message.replace(/sk-[A-Za-z0-9_-]+/g, "[entfernter-schluessel]");
  const entry = {
    at: new Date().toISOString(),
    scope,
    message: safe,
    stack: error instanceof Error ? error.stack?.replace(/sk-[A-Za-z0-9_-]+/g, "[entfernter-schluessel]") : undefined,
  };
  try {
    const dir = path.join(dataDir(), "logs");
    mkdirSync(dir, { recursive: true });
    appendFileSync(path.join(dir, "errors.jsonl"), `${JSON.stringify(entry)}\n`, "utf8");
  } catch {
    console.error(entry.at, scope, safe);
  }
  console.error(entry.at, scope, safe);
}

export function laypersonError(error: unknown): string {
  if (error instanceof Error && error.message.startsWith("Wir konnten")) return error.message;
  return "Wir konnten den Vorgang nicht abschließen. Der technische Grund ist im Fehlerprotokoll, ohne Schlüssel und ohne Rechnungsinhalt in der Kurzfassung.";
}
