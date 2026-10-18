import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import models from "../../config/models.json";
import app from "../../config/app.json";

export interface ModelConfig {
  readSmall: string;
  readMedium: string;
  readLarge: string;
  evaluate: string;
  examiner: string;
  chat: string;
}

export interface AppConfig {
  maxUploadBytes: number;
  allowedMimeTypes: string[];
  methodologyVersion: string;
  rulesStamp: string;
  filingDeadlineMonth: number;
  filingDeadlineDay: number;
}

export function modelConfig(): ModelConfig {
  return models;
}

export function appConfig(): AppConfig {
  return app;
}

export function readModels(): string[] {
  return [models.readSmall, models.readMedium, models.readLarge];
}

export function dataDir(): string {
  return path.resolve(/*turbopackIgnore: true*/ process.cwd(), process.env.KSK_DATA_DIR || "data");
}

function switchFile(): string {
  return path.join(dataDir(), "mistral-enabled.json");
}

export function mistralUseEnabled(): boolean {
  try {
    const parsed = JSON.parse(readFileSync(switchFile(), "utf8")) as { enabled?: boolean };
    return parsed.enabled !== false;
  } catch {
    return true;
  }
}

export function setMistralUseEnabled(enabled: boolean): void {
  mkdirSync(dataDir(), { recursive: true });
  writeFileSync(switchFile(), JSON.stringify({ enabled }), "utf8");
  if (enabled) {
    if (process.env.KSK_LLM_MODE === "mock") delete process.env.KSK_LLM_MODE;
  } else {
    process.env.KSK_LLM_MODE = "mock";
  }
}

export function llmMode(): "mock" | "mistral" {
  if (!mistralUseEnabled()) return "mock";
  if (process.env.KSK_LLM_MODE === "mock") return "mock";
  if (process.env.KSK_LLM_MODE === "mistral") return "mistral";
  return process.env.MISTRAL_API_KEY ? "mistral" : "mock";
}

export function projectPath(...parts: string[]): string {
  return path.join(/*turbopackIgnore: true*/ process.cwd(), ...parts);
}

export function readMethodology(): string {
  return readFileSync(projectPath("rules", "prompt-v12.md"), "utf8");
}
