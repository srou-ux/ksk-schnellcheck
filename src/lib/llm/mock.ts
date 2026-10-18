import type { LlmClient, LlmRequest } from "./types";
import { emptyUsage } from "./types";
import { emptyReading, parseMarker } from "../domain/parse-reading";

export function createMockLlm(options?: { examinerConsistent?: boolean }): LlmClient {
  const examinerConsistent = options?.examinerConsistent !== false;
  return {
    async complete(request: LlmRequest) {
      if (request.endpoint === "pruefer") {
        return {
          text: JSON.stringify({
            consistent: examinerConsistent,
            finding: examinerConsistent ? null : "Simulierter Widerspruch des Prüfers gegen Stufe E.",
          }),
          usage: emptyUsage(),
        };
      }
      if (request.endpoint === "bewertung") {
        return { text: JSON.stringify({ useEngine: true }), usage: emptyUsage() };
      }
      if (request.endpoint === "chat") {
        return {
          text: "Im gespeicherten Bericht steht der mitgeschickte Zustand der Position. Ich rechne nichts neu und löse keinen Hinweis.",
          usage: emptyUsage(),
        };
      }
      const marked = parseMarker(request.user);
      const reading = marked ?? { ...emptyReading(), readable: false };
      return { text: JSON.stringify(reading), usage: emptyUsage() };
    },
  };
}
