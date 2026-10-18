import type { LlmClient, LlmRequest } from "./types";

function redact(text: string, key: string): string {
  return key ? text.split(key).join("[entfernter-schluessel]") : text;
}

function textFromConversation(parsed: { outputs?: Array<{ type?: string; content?: string | Array<{ text?: string }> }> }): string {
  const texts: string[] = [];
  for (const output of parsed.outputs ?? []) {
    if (output.type !== "message.output") continue;
    if (typeof output.content === "string") texts.push(output.content);
    else if (Array.isArray(output.content)) texts.push(output.content.map((part) => part.text ?? "").join("\n"));
  }
  return texts.join("\n").trim();
}

export function createMistralLlm(apiKey: string): LlmClient {
  return {
    async complete(request: LlmRequest) {
      const content: Array<Record<string, unknown>> = [{ type: "text", text: request.user }];
      for (const image of request.images ?? []) {
        content.push({ type: "image_url", image_url: { url: `data:${image.mime};base64,${image.base64}` } });
      }
      const libraryCall = Boolean(request.libraryId);
      const body: Record<string, unknown> = libraryCall
        ? {
          model: request.model,
          instructions: request.system,
          inputs: request.user,
          store: false,
          tools: [{ type: "document_library", library_ids: [request.libraryId] }],
          completion_args: {
            temperature: 0,
            ...(request.json ? { response_format: { type: "json_object" } } : {}),
          },
        }
        : {
          model: request.model,
          temperature: 0,
          messages: [
            { role: "system", content: request.system },
            { role: "user", content: request.images?.length ? content : request.user },
          ],
          ...(request.json ? { response_format: { type: "json_object" } } : {}),
        };
      const response = await fetch(libraryCall ? "https://api.mistral.ai/v1/conversations" : "https://api.mistral.ai/v1/chat/completions", {
        method: "POST",
        signal: AbortSignal.timeout(libraryCall ? 15_000 : 90_000),
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      const raw = await response.text();
      if (!response.ok) {
        throw new Error(`Wir konnten Mistral nicht erreichen (${request.endpoint}). ${redact(raw, apiKey).slice(0, 300)}`);
      }
      if (libraryCall) {
        const conversation = JSON.parse(raw) as {
          outputs?: Array<{ type?: string; content?: string | Array<{ text?: string }> }>;
          usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
        };
        return {
          text: textFromConversation(conversation),
          usage: {
            promptTokens: conversation.usage?.prompt_tokens ?? 0,
            completionTokens: conversation.usage?.completion_tokens ?? 0,
            totalTokens: conversation.usage?.total_tokens ?? 0,
          },
        };
      }
      const parsed = JSON.parse(raw) as {
        choices?: Array<{ message?: { content?: string | Array<{ text?: string }> } }>;
        usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number };
      };
      const message = parsed.choices?.[0]?.message?.content;
      const text = typeof message === "string" ? message : Array.isArray(message) ? message.map((part) => part.text ?? "").join("\n") : "";
      return {
        text,
        usage: {
          promptTokens: parsed.usage?.prompt_tokens ?? 0,
          completionTokens: parsed.usage?.completion_tokens ?? 0,
          totalTokens: parsed.usage?.total_tokens ?? 0,
        },
      };
    },
  };
}

export async function mistralKeyStatus(apiKey: string): Promise<"verbunden" | "nicht verbunden"> {
  const response = await fetch("https://api.mistral.ai/v1/models", {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  return response.ok ? "verbunden" : "nicht verbunden";
}
