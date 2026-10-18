import { expect, test } from "@playwright/test";

test("Admin trennt Upload, Verarbeitung und RAG-Nachweis sichtbar", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Paketquellen und RAG-Nachweise" })).toBeVisible();
  await expect(page.getByText("Ein Upload allein ist nicht verwendbar.")).toBeVisible();
  await expect(page.getByText("Noch keine archivierte Quelle einer Paketversion zugeordnet.")).toBeVisible();
});
