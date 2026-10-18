"""Echter Browser + laufende App „Rechnungen prüfen“ (ohne KI); nur erfundene Belege
(kein Sprachmodell, kein Chat).
Aufruf: python tests/app/playwright_dokumente.py (Playwright/Chromium erforderlich).
"""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from tests.app.test_dokumente import pdf
from tests.app.test_dokument_layout import layout_pdf


def hauptlauf():
    from playwright.sync_api import sync_playwright, expect
    url = "http://127.0.0.1:8732"
    env = dict(os.environ)
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8732"], cwd=W, env=env)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(url + "/gesundheit", timeout=1); break
            except OSError:
                time.sleep(.2)
        else:
            raise RuntimeError("Dokumentenserver nicht erreichbar")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            fehler = []; fremde = []
            page.on("pageerror", lambda e: fehler.append(str(e)))
            page.on("request", lambda r: fremde.append(r.url) if not r.url.startswith(url) else None)
            # Ohne KI (17.10.2026): kein Chat mehr; Startseite und /rechnungen zeigen „Rechnungen prüfen“.
            for pfad in ("", "/rechnungen"):
                page.goto(url + pfad)
                expect(page.locator('#bereiche a[aria-current="page"]')).to_have_text("Rechnungen prüfen")
                expect(page.locator("#bereiche a", has_text="KSK-Chat")).to_have_count(0)
            # Beschrifteter Rechnungsempfänger + Betrag in separatem PDF-Textobjekt.
            page.goto(url + "/rechnungen")
            page.locator("#files").set_input_files({"name":"layout-test.pdf", "mimeType":"application/pdf", "buffer":layout_pdf()})
            expect(page.locator("#rows tr")).to_have_count(1)
            expect(page.locator('[data-field="bezeichnung"]')).to_have_value("Logo-Gestaltung")
            expect(page.locator('[data-field="betrag"]')).to_have_value("1500.00")
            expect(page.locator("#company")).to_have_value("Baeckerei Test GmbH")
            expect(page.locator("#autofill-note")).to_contain_text("RECHNUNGSEMPFAENGER")
            expect(page.locator("#year")).to_have_value("")
            expect(page.locator("#net-paid")).not_to_be_checked()
            page.locator("#company").fill("Manuell korrigiert")
            for n, (betrag, erwartung) in enumerate([(1500, "73,50"), (1600, "78,40"), (1700, "83,30"), (1800, "88,20")]):
                page.goto(url + "/rechnungen")
                # Keine eval-basierte Pollingfunktion: die Seite verbietet unsafe-eval ausdrücklich.
                expect(page.locator("#catalog-list li")).to_have_count(9)
                payload = {"name": f"fiktiv-{n}.pdf", "mimeType": "application/pdf", "buffer": pdf([f"Logo {betrag},00 EUR"])}
                page.locator("#files").set_input_files(payload)
                expect(page.locator("#rows tr")).to_have_count(1)
                page.locator("#company").fill("Bäckerei")
                page.locator("#year").fill("2026")
                page.locator("#purpose").select_option("eigene_werbung")
                page.locator("#catalog").select_option("false")
                page.locator('[data-field="auftragnehmer_nr"]').fill("1")
                page.locator('[data-field="auftragnehmer_typ"]').select_option("natuerliche_person")
                page.locator('[data-field="zahlungsweg"]').select_option("direkt")
                page.locator("#year-complete").check(); page.locator("#net-paid").check(); page.locator("#reviewed").check()
                page.locator('#facts button[type="submit"]').click()
                expect(page.locator("#confirmation")).to_be_visible()
                expect(page.locator("#summary")).to_contain_text("Eigenwerbung")
                page.locator("#confirm").click()
                expect(page.locator("#result")).to_be_visible()
                expect(page.locator("#result-title")).to_contain_text("Abgabepflichtig")
                expect(page.locator("#numbers")).to_contain_text(erwartung)
                # Jahresübersicht (17.10.2026): Kopfzeile, Spalte Rechnung/Belegstelle, CSV für den Steuerberater.
                expect(page.locator("#result-sub")).to_contain_text("Zahlungsjahr 2026")
                expect(page.locator("#result-rows")).to_contain_text(f"fiktiv-{n}.pdf")
                with page.expect_download() as laden:
                    page.locator("#csv-result").click()
                inhalt = Path(laden.value.path()).read_text(encoding="utf-8-sig")
                assert laden.value.suggested_filename == "KSK-Jahresuebersicht-2026.csv", laden.value.suggested_filename
                assert "Jahresübersicht" in inhalt and erwartung in inhalt and "Entwurf" in inhalt, inhalt[:300]
                page.locator("#result summary").click()
                expect(page.locator("#sources li").first).to_be_visible()
                # Nachträgliche Änderung verwirft das sichtbare Ergebnis und die Bestätigung.
                page.locator('[data-field="betrag"]').fill("1000")
                expect(page.locator("#result")).to_be_hidden()
                # Dieselbe Datei darf nicht doppelt eingefügt werden.
                page.locator("#files").set_input_files(payload)
                expect(page.locator("#message")).to_contain_text("bereits")
                expect(page.locator("#rows tr")).to_have_count(1)
            # Zwei Rechnungen, ein Jahresfall (17.10.2026): einzeln unter der Grenze, zusammen darüber.
            page.goto(url + "/rechnungen")
            page.locator("#files").set_input_files([
                {"name": "rechnung-a.pdf", "mimeType": "application/pdf", "buffer": pdf(["Logo 800,00 EUR"])},
                {"name": "rechnung-b.pdf", "mimeType": "application/pdf", "buffer": pdf(["Flyer-Gestaltung 900,00 EUR"])}])
            expect(page.locator("#rows tr")).to_have_count(2)
            page.locator("#company").fill("Bäckerei"); page.locator("#year").fill("2026")
            page.locator("#purpose").select_option("eigene_werbung"); page.locator("#catalog").select_option("false")
            for i in range(2):
                page.locator('[data-field="auftragnehmer_nr"]').nth(i).fill(str(i + 1))
                page.locator('[data-field="auftragnehmer_typ"]').nth(i).select_option("natuerliche_person")
                page.locator('[data-field="zahlungsweg"]').nth(i).select_option("direkt")
            page.locator("#year-complete").check(); page.locator("#net-paid").check(); page.locator("#reviewed").check()
            page.locator('#facts button[type="submit"]').click()
            page.locator("#confirm").click()
            expect(page.locator("#result-title")).to_contain_text("Abgabepflichtig")
            expect(page.locator("#numbers")).to_contain_text("83,30")
            expect(page.locator("#result-sub")).to_contain_text("2 Dokument(e)")
            expect(page.locator("#result-rows")).to_contain_text("rechnung-b.pdf")
            # XSS aus Dokumenttext wird nur als Text angezeigt.
            page.goto(url + "/rechnungen")
            page.locator("#files").set_input_files({"name":"fiktiv.csv", "mimeType":"text/csv",
                "buffer":b'Bezeichnung;Betrag\n<img src=x onerror=alert(1)>;1500,00'})
            expect(page.locator("#rows tr")).to_have_count(1)
            assert page.locator("#rows img").count() == 0
            page.set_viewport_size({"width":390,"height":844})
            for selector in ("#bereiche", "header", "main", ".layout", ".card"):
                for item in page.locator(selector).all():
                    box = item.bounding_box()
                    if box:
                        assert box["x"] >= 0 and box["x"] + box["width"] <= 390, (selector, box)
            assert not fehler, fehler
            assert not fremde, fremde
            browser.close()
    finally:
        server.terminate()
        try: server.wait(timeout=10)
        except subprocess.TimeoutExpired: server.kill()
    print("Dokumenten-Browsertest: Menü, Upload, Bestätigung, 4 Ergebnisse, Jahresübersicht mit CSV, zwei Rechnungen in einem Jahresfall, Korrektur, Duplikate, XSS und Mobilansicht OK")


if __name__ == "__main__":
    hauptlauf()
