export interface LlmUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface LlmRequest {
  endpoint: string;
  model: string;
  system: string;
  user: string;
  images?: Array<{ mime: string; base64: string }>;
  libraryId?: string | null;
  json?: boolean;
}

export interface LlmClient {
  complete(request: LlmRequest): Promise<{ text: string; usage: LlmUsage }>;
}

export function emptyUsage(): LlmUsage {
  return { promptTokens: 0, completionTokens: 0, totalTokens: 0 };
}
