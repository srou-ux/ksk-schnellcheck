"""Browser-Test (Playwright) fuer app/static/index.html -- Chatbot Teil 1f, Abschnitt J.5.

KEIN Teil der normalen Testsuite (Dateiname passt nicht zu `test*.py`, `python -m unittest
discover` findet ihn nicht): er braucht einen echten Chromium-Browser und `playwright`,
beides nicht in `app/requirements.txt`. Laeuft nur im GitHub-Workflow
`.github/workflows/pruefen.yml` (Job "oberflaeche").

Startet den Demo-Server (FakeLLM, kein Schluessel), oeffnet die Seite, sendet "hallo" und
prueft:
- die feste Begruessung (app/router.py::HINWEIS_TEXT) erscheint, OHNE Modellaufruf/Rueckfrage;
- kein sichtbares '**'/freistehendes '*' im Text (Markdown-Bug Teil 1f, Abschnitt J.2 --
  **fett**/*kursiv* muss als echtes <strong>/<em> dargestellt werden, nicht als Sternchen).
Aufruf: python tests/app/playwright_oberflaeche.py
"""
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
PORT = 8731
URL = f"http://127.0.0.1:{PORT}/"


def _warte_auf_server(timeout: float = 20.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            urllib.request.urlopen(f"{URL}gesundheit", timeout=1)
            return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.3)
    raise RuntimeError("Demo-Server ist innerhalb der Wartezeit nicht erreichbar geworden.")


def hauptlauf() -> None:
    from playwright.sync_api import sync_playwright

    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=str(WURZEL),
    )
    try:
        _warte_auf_server()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            seite = browser.new_page()
            seite.goto(URL)
            seite.fill("#eingabe", "hallo")
            seite.click("#senden")
            seite.wait_for_selector(".nachricht.bot")
            text = seite.inner_text(".nachricht.bot")
            assert "*" not in text, f"Sternchen im sichtbaren Text (Markdown nicht umgesetzt): {text!r}"
            assert "Rückfrage" not in text, f"Begruessung haette keine Rueckfrage sein duerfen: {text!r}"
            assert "Künstlersozialabgabe" in text, f"Feste Begruessung nicht gefunden: {text!r}"
            _dialog_schritt2(browser)
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


def _dialog_schritt2(browser) -> None:
    """Schritt 2 (17.10.2026): ganzer Dialog wie ein Mensch -- Frage -> Rückfrage nach dem Zweck (Knöpfe in
    Alltagssprache, keine Rechtskategorie) -> Knopf -> Faktenbestätigung (Sätze + Liste einmal) -> 'Ja, das stimmt'
    -> Ergebnis. Demo-Modus (FakeLLM), erfundene Daten."""
    seite = browser.new_page()
    seite.goto(URL)

    def letzte_antwort(anzahl_vorher: int) -> str:
        seite.wait_for_function("n => document.querySelectorAll('.nachricht.bot').length > n", arg=anzahl_vorher,
                                timeout=20000)
        return seite.locator(".nachricht.bot").last.inner_text()

    n = seite.locator(".nachricht.bot").count()
    seite.fill("#eingabe", "2026 haben wir einer freien Grafikerin (Einzelperson) 1.500 € für ein Logo gezahlt.")
    seite.click("#senden")
    text = letzte_antwort(n)
    assert "Wofür war dieser Auftrag gedacht?" in text, f"Rückfrage nach dem Zweck fehlt: {text!r}"
    for verboten in ("Typischer Verwerter", "Generalklausel", "eigenwerbend"):
        assert verboten not in text, f"Rechtskategorie in der Rückfrage: {verboten!r} in {text!r}"
    knoepfe = seite.locator(".nachricht.bot").last.locator(".vorschlag")
    beschriftungen = [knoepfe.nth(i).inner_text().strip() for i in range(knoepfe.count())]
    for erwartet in ("Werbung für mein eigenes Unternehmen", "Werbung oder Öffentlichkeitsarbeit für Kunden",
                     "Eine Veranstaltung mit Künstlern", "Ein privater Auftrag", "Noch unbekannt / später klären"):
        assert erwartet in beschriftungen, f"Knopf {erwartet!r} fehlt: {beschriftungen!r}"

    n = seite.locator(".nachricht.bot").count()
    knoepfe.get_by_text("Werbung für mein eigenes Unternehmen", exact=True).first.click()
    text = letzte_antwort(n)
    assert "Bitte prüfen Sie, ob ich Ihre Angaben richtig verstanden habe" in text, text
    assert "Vorschlag des Systems, keine Angabe von Ihnen" in text, text
    assert "1.500,00 €" in text, f"Betrag in der Bestätigung fehlt: {text!r}"
    assert text.count("Position 1:") == 1, f"Liste doppelt angezeigt: {text!r}"
    assert "Abgabepflichtig" not in text, f"Ergebnis vor der Bestätigung: {text!r}"

    n = seite.locator(".nachricht.bot").count()
    seite.locator(".nachricht.bot").last.locator(".bestaetigung-knopf.ja").click()
    text = letzte_antwort(n)
    assert "Abgabepflichtig (Vorschlag)" in text, f"Kein Ergebnis nach der Bestätigung: {text!r}"
    seite.close()


if __name__ == "__main__":
    hauptlauf()
    print("Playwright-Oberflaechentest: OK")
