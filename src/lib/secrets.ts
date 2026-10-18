import { chmodSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

/** Lädt config/secrets.env in process.env. Leere Variablen werden aus der Datei gefüllt. Der Schlüssel wird nicht geloggt. */
export function loadSecrets(): void {
  const file = path.join(process.cwd(), "config", "secrets.env");
  if (!existsSync(file)) return;
  const text = readFileSync(file, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!/^[A-Z0-9_]+$/.test(key) || value.length === 0) continue;
    if (!process.env[key]) process.env[key] = value;
  }
}

export function secretsFilePath(): string {
  return path.join(process.cwd(), "config", "secrets.env");
}

/** Schreibt einen Schlüssel nur in config/secrets.env. Der Wert wird nicht geloggt und nicht zurückgegeben. */
export function updateSecret(name: "MISTRAL_API_KEY" | "ADMIN_PASSWORD", value: string): void {
  const trimmed = value.trim();
  if (trimmed.length < 8 || /[\r\n]/.test(trimmed)) {
    throw new Error("Wir konnten den Schlüssel nicht speichern, weil der Eintrag leer oder mehrzeilig ist.");
  }
  const file = secretsFilePath();
  const current = existsSync(file) ? readFileSync(file, "utf8") : "";
  const kept = current.split(/\r?\n/).filter((line) => {
    const text = line.trim();
    if (!text) return false;
    if (text.startsWith("#")) return true;
    return !text.startsWith(`${name}=`);
  });
  kept.push(`${name}=${trimmed}`);
  writeFileSync(file, `${kept.join("\n")}\n`, { encoding: "utf8", mode: 0o600 });
  try {
    chmodSync(file, 0o600);
  } catch {
    // Unter Windows bleibt die Datei trotzdem außerhalb des Repositorys.
  }
  process.env[name] = trimmed;
  if (name === "MISTRAL_API_KEY") process.env.KSK_LLM_MODE = "mistral";
}

export function resetSecretsForTests(): void {
  delete process.env.MISTRAL_API_KEY;
}
