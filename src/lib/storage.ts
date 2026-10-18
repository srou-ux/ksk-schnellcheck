import { mkdirSync, readFileSync, writeFileSync, unlinkSync, existsSync } from "node:fs";
import path from "node:path";

export interface ObjectStorage {
  put(key: string, body: Buffer): Promise<void>;
  get(key: string): Promise<Buffer>;
  delete(key: string): Promise<void>;
}

export function createLocalStorage(root: string): ObjectStorage {
  return {
    async put(key, body) {
      const target = safePath(root, key);
      mkdirSync(path.dirname(target), { recursive: true });
      writeFileSync(target, body);
    },
    async get(key) {
      return readFileSync(safePath(root, key));
    },
    async delete(key) {
      const target = safePath(root, key);
      if (existsSync(target)) unlinkSync(target);
    },
  };
}

function safePath(root: string, key: string): string {
  if (!/^[a-zA-Z0-9/_\-.]+$/.test(key) || key.includes("..")) {
    throw new Error("Wir konnten die Datei nicht speichern, weil der Speichername ungültig ist.");
  }
  const resolved = path.resolve(root, key);
  const relative = path.relative(path.resolve(root), resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Wir konnten die Datei nicht speichern, weil der Speicherpfad außerhalb des Ablageordners liegt.");
  }
  return resolved;
}
