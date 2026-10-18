import { test, expect } from "@playwright/test";
import { writeFileSync } from "node:fs";
import path from "node:path";
import os from "node:os";

test("eine unlesbare Bilddatei bleibt ungeklärt", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Rechnung prüfen" }).click();
  await page.getByPlaceholder("Verlag Beispiel, Rechnung März").fill("E2E Bild");
  await page.getByRole("button", { name: "Fall anlegen" }).click();
  await expect(page.getByRole("heading", { name: "E2E Bild" })).toBeVisible({ timeout: 30_000 });
  const file = path.join(os.tmpdir(), "ksk-e2e.png");
  writeFileSync(file, Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "base64"));
  await page.locator("input[type=file]").setInputFiles(file);
  await expect(page.getByText("ksk-e2e.png")).toBeVisible();
  await page.getByRole("button", { name: "Prüfung starten" }).click();
  await expect(page.getByText("nicht übereinstimmend lesbar")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Ablesung im Mock-Modus")).toBeVisible();
});

test("Admin ist im Testmodus ohne Anmeldung offen", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByText("Testmodus — nicht produktiv")).toBeVisible();
  await expect(page.getByRole("heading", { name: "KSK-Referenzen" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Schlüssel prüfen" })).toBeVisible();
});
