import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { defineConfig } from "vitest/config";

const dataDir = mkdtempSync(path.join(tmpdir(), "ksk-test-"));

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    env: {
      KSK_LLM_MODE: "mock",
      KSK_DATA_DIR: dataDir,
      ADMIN_PASSWORD: "vitest-admin",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
