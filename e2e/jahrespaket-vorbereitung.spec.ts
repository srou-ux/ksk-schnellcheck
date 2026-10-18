import { expect, test } from "@playwright/test";

test("zeigt den Einstieg zur KI-gestützten Jahrespaket-Vorbereitung", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByTestId("ki-vorbereitung-panel")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Jahrespaket mit KI vorbereiten" })).toBeVisible();
  await expect(page.getByLabel("Jahr")).toBeVisible();
  await expect(page.getByRole("button", { name: "Mit KI vorbereiten" })).toBeEnabled();
  await expect(page.getByText(/bleibt unvollständig, ungeprüft und inaktiv/)).toBeVisible();
});
