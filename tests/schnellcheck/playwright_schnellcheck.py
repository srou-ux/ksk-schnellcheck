"""Echter Browser/HTTP-Server; ausschließlich erfundene Angaben, keine externen Dienste."""
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

W = Path(__file__).resolve().parents[2]


def main():
    from playwright.sync_api import sync_playwright, expect
    url = "http://127.0.0.1:8734"
    server = subprocess.Popen([sys.executable, "-m", "schnellcheck", "--port", "8734"], cwd=W)
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(url + "/gesundheit", timeout=1):
                    break
            except OSError:
                time.sleep(.2)
        else:
            raise RuntimeError("Schnellcheck nicht erreichbar")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            errors, externe, anfragen = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("request", lambda r: externe.append(r.url) if not r.url.startswith(url) else None)
            page.on("request", lambda r: anfragen.append(r) if r.url.endswith("/api/pruefen") else None)
            page.goto(url)
            expect(page.locator(".pos")).to_have_count(1)
            page.locator("#branche").fill("Fiktive Bäckerei")
            page.locator('[name="zweck"][value="eigene_werbung"]').check()
            page.locator('[name="katalog"][value="nein"]').check()
            page.locator('[data-feld="leistung"]').select_option("T-14")
            page.locator('[data-feld="rechtsform"]').select_option("natuerliche_person")
            page.locator('[data-feld="betrag"]').fill("1.500,00")
            page.locator('[name="vollstaendig"][value="ja"]').check()
            page.locator("#bestaetigt").check()
            page.locator("#pruefen").click()
            expect(page.locator("#ergebnis .bericht")).to_be_visible()
            assert anfragen[-1].post_data_json["positionen"][0]["betrag"] == "1500.00"
            # Eingabeänderung entfernt den Bericht, ungültige Zahl geht niemals an den Server.
            page.locator('[data-feld="betrag"]').fill("12,345")
            expect(page.locator("#ergebnis .bericht")).to_have_count(0)
            vorher = len(anfragen)
            page.locator("#pruefen").click()
            expect(page.locator("#meldung")).to_contain_text("gültigen Betrag")
            assert len(anfragen) == vorher
            page.locator('[data-feld="betrag"]').fill("1500,00")
            page.locator("#pruefen").click()
            expect(page.locator("#ergebnis .bericht")).to_be_visible()
            page.locator("#neu").click()
            expect(page.locator(".pos")).to_have_count(2)
            expect(page.locator("#ergebnis .bericht")).to_have_count(0)
            page.locator(".entfernen").last.click()
            expect(page.locator(".pos")).to_have_count(1)
            page.locator("#pruefen").click()
            expect(page.locator("#ergebnis .bericht")).to_be_visible()
            page.locator('[name="vollstaendig"][value="nein"]').check()
            expect(page.locator("#ergebnis .bericht")).to_have_count(0)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert not errors, errors
            assert not externe, externe
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
    print("Schnellcheck-Browser: Betrag, Prüfung, Korrektur, Positionen, Auswahl und Mobilansicht OK")


if __name__ == "__main__":
    main()
