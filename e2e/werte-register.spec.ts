import { expect, test } from "@playwright/test";

test("zeigt Entwürfe und lehnt eine unvollständige Freigabe ab", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByText("Das System prüft nur, ob Quelle, Fundstelle, Dokumentstand, Gültigkeit und Anwendungsbereich ausgefüllt sind.")).toBeVisible();
  await expect(page.getByTestId("register-status").first()).toHaveText("Entwurf");
  await page.getByLabel("Kennung").fill("e2e_kennzahl");
  await page.getByLabel("Beschreibung").fill("E2E-Wert");
  await page.getByLabel("Betrag").fill("12,50");
  await page.getByLabel("gültig ab").fill("2028-01-01");
  await page.getByRole("button", { name: "Als Entwurf speichern" }).click();
  await expect(page.getByText("Der Entwurf ist gespeichert. Freigegebene Werte und ihre Gültigkeit sind unverändert.")).toBeVisible();
  await page.getByLabel("Betrag").fill("12,50");
  await page.getByRole("button", { name: "Freigeben" }).click();
  await expect(page.getByText("Zur Freigabe fehlen Angaben.")).toBeVisible();
  await expect(page.getByText("keine fachliche Prüfung")).toBeVisible();
});
