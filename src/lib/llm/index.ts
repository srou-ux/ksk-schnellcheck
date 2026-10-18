import { logLlmUsage } from "../db";
import { llmMode } from "../config";
import { createMistralLlm } from "./mistral";
import { createMockLlm } from "./mock";
import type { LlmClient } from "./types";

export function createLlmClient(options?: { examinerConsistent?: boolean }): LlmClient {
  let inner: LlmClient;
  if (llmMode() === "mistral") {
    const key = process.env.MISTRAL_API_KEY;
    if (!key) throw new Error("Wir konnten Mistral nicht aufrufen, weil kein Schlüssel konfiguriert ist.");
    inner = createMistralLlm(key);
  } else {
    inner = createMockLlm(options);
  }
  return {
    async complete(request) {
      const result = await inner.complete(request);
      logLlmUsage({
        endpoint: request.endpoint,
        model: request.model,
        promptTokens: result.usage.promptTokens,
        completionTokens: result.usage.completionTokens,
        totalTokens: result.usage.totalTokens,
      });
      return result;
    },
  };
}
