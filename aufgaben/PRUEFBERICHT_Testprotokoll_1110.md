# Prüfbericht zum Testprotokoll vom 11.10.2026 (Faktenerfassung und Gesprächssteuerung)

Grundlage: `KSK_Testprotokoll_Claude_Code.pdf` (manueller Test, nur erfundene Daten). Abgrenzung wie im Protokoll: Geprüft wurden Faktenerfassung und Gesprächssteuerung, nicht die fachliche Richtigkeit einer Endberechnung.

**Umgebung der Nachweise:** Modell `mistral-large-latest`, temperature 0, top_p 1 (`app/llm/mistral.py`). Lauf über GitHub Actions („Dialog nachspielen“, Schritte in `aufgaben/audit/dialog_testprotokoll_1110.json`, Bericht `aufgaben/audit/dialog_nachgespielt_large.md`). Branch `main`, Stände `7a87d79` (erste Messung) bis `cc42c98` (letzter Lauf). Welche Version das Deployment des Nutzers hatte, war nicht dokumentiert und ist nicht mehr feststellbar.

## 1. Reproduziert und Ursache

Das Nachspielen schreibt bei jedem Schritt mit: den Fallstand vorher, was ans Modell geht, die rohe Modellantwort und den Fallstand nachher.

| Beobachtung | Reproduziert? | Ursache |
|---|---|---|
| Eigenwerbung erneut abgefragt | ja | Das Modell setzt `verwerterart` nie, auch nicht bei „Wir betreiben ausschließlich Eigenwerbung“. Die Gegenprüfung `absichere_verwerterart` erkannte „Eigenwerbung“, nutzte das aber nur zum Prüfen eines Modellwerts, nicht zum Ergänzen. **Unser Code.** |
| Rechtsformen erneut abgefragt | ja | Das Modell setzte in Schritt 1 keine Rechtsform. Bei mehreren Positionen riet `ergaenze_rechtsform` bewusst nicht. Die Druckkosten bekamen nicht die Rechtsform derselben Grafikerin. **Fehlende Zuordnung im Code.** |
| „vortrag und reproduktion“ | sinngemäß ja (diesmal „material_auslagen“) | Das Modell erfand Rollen, das Schema ließ jeden Text zu, und die Anzeige zeigte die Rolle statt der Bezeichnung. Deshalb war die Umbenennung unsichtbar. Erfundene Rollen wirkten nicht auf die Rechnung, gültige Sonderrollen schon. **Schema und Anzeige.** |
| Korrektur 1.200 → 900 | anfangs ja, später nicht mehr | Das Modell hätte 900 − 300 rechnen müssen und ließ den alten Rest stehen. **Das Modell sollte rechnen, das verstößt gegen Grundregel 3.** |
| Rechtsform-Konflikt nicht behandelt | ja | Das Modell löschte die Rechtsform still, einen Zustand „widersprüchlich“ gab es nicht. Außerdem meldete das Modell einmal einen „Widerspruch“ bei einem vom System abgeleiteten Feld (`taetigkeit_id`). |
| Neuer Fall | Trennung ja | Intern sauber getrennt (neue Sitzung, keine alten Positionen, alter Fall erhalten). Aber das Modell trug „Verein“ (den Auftraggeber) als Rechtsform der Musiker ein, obwohl „unbekannt“ gesagt war. Einen Zustand „unbekannt“ gab es nur für die Zahl der Veranstaltungen. |
| Sackgasse bei „ungeklärt“ und Übersicht | ja | Kein Zustand „unbekannt“, keine Übersicht. Das Modell lieferte in Schritt 9 kaputtes JSON, und es gab keinen zweiten Versuch. |
| Alte Bestätigungsknöpfe | geprüft, kein Fehler | `/bestaetigen` vergleicht den Fakten-Hash. Ein alter Knopf ist nach jeder Änderung wirkungslos (Test). |

## 2. Geändert

**Verbindlicher Fallstand** (`app/fallstand.py`, neu):
- Das Modell bekommt den gespeicherten Stand und **nur die neue Nachricht**, nicht mehr den Chatverlauf.
- Python übernimmt die Antwort nach festen Regeln:
  - Was das Modell nicht liefert, bleibt.
  - Positionen werden einzeln zusammengeführt.
  - Weniger Positionen gibt es nur, wenn die Nachricht ausdrücklich etwas entfernt.
  - Ein Widerspruch ändert den alten Wert nicht.
- Vom System abgeleitete Werte gehen nicht ans Modell.

**Zustände** (`Fakten.unbekannt`, `Fakten.widersprueche`):
- **Ausdrücklich unbekannt:** Die Angabe wird nicht erneut gefragt, blockiert aber eine davon abhängige Bewertung („zurückgestellt“). Erkannt wird das deterministisch („Das Jahr … sind unbekannt“, „Das ist noch ungeklärt“), oder der Nutzer drückt den Knopf **„Noch unbekannt / später klären“**, den jede Frage hat.
- **Widersprüchlich:** Das System stellt eine gezielte Frage mit Knöpfen für beide Werte und „noch ungeklärt“, zeigt keine Faktenbestätigung und gibt keine Bewertung. Erkannt wird der Widerspruch vom Modell oder deterministisch: Konfliktwort plus zwei Rechtsformen plus genannter Betrag.

**Übersicht** auf Wunsch („Welche Angaben sind erfasst?“), und immer, sobald etwas unbekannt oder widersprüchlich ist: was erfasst ist, was offen ist und was als Nächstes fehlt.

**Rechnung mit enthaltenen Teilen:**
- Der Rechnungsbetrag wird gespeichert (`Fakten.rechnungen`), die Teile sind eigene Positionen.
- Den Rest rechnet der **Kern** (`kern.rechnen.restbetrag`). Das Modell rechnet nicht mehr.
- Eine Korrektur ändert nur den Rechnungsbetrag.
- „davon/darin“ wird nicht doppelt gezählt (P-39).
- Eine Rest-Position ohne Rechnungsbetrag oder ein Teil, der so groß ist wie die ganze Rechnung, führt zu einer gezielten Rückfrage statt zu einer stillen Null (P-28).

**Einzelursachen:**
- Eigenwerbung aus dem Text ergänzen.
- Rollen nur aus der festen Liste; Sonderrollen nur für den Betrag, der direkt beim Beleg-Wort steht.
- Die Anzeige zeigt die Bezeichnung.
- Rechtsform je Zeile über den genannten Betrag zuordnen; Positionen desselben Auftragnehmers teilen die Rechtsform.
- Verneinung („ohne Druckkosten“) beachten.
- Ein vom Modell selbst addierter Gesamtbetrag wird verworfen.
- Bei kaputtem JSON, bloßen Zahlen in Listen oder fremden Schlüsseln gibt es einen zweiten Versuch. Harmlose Formfehler werden ohne Raten bereinigt.

**Oberfläche:** Auch Fragen mit Knöpfen lassen sich per Text beantworten.

Geänderte Dateien:
- `app/fallstand.py` und `app/fallstand_begriffe.json` (neu)
- `app/router.py`, `app/pflichtangaben.py`, `app/zuordnung.py`, `app/bestaetigung.py`, `app/schema.py`
- `app/llm/mistral.py`, `app/llm/fake.py`, `app/llm/base.py`, `app/taetigkeiten.py`, `app/static/index.html`
- `kern/rechnen.py` (nur `restbetrag`)
- Werkzeuge: `aufgaben/audit/dialog_nachspielen.py`, `aufgaben/audit/abnahme_teil1f.py` (nur die Etiketten)

## 3. Regressionstests

`tests/app/test_testprotokoll_1110.py`: 33 Tests offline mit kontrollierten Modellantworten, die den echten Antworten nachgebildet sind. Sie bestehen alle. Sie decken ab:
- bereits genannte Pflichtangaben
- enthaltene Kosten ohne Doppelzählung
- gemeinsamer Auftragnehmer
- Betragskorrektur bei unveränderten übrigen Fakten
- alte Bestätigung ist ungültig
- Widerspruch statt stiller Auflösung (vom Modell gemeldet und vom Modell verschwiegen)
- „ungeklärt“ bleibt offen
- Fallwechsel ohne alte Daten
- getrennte Rechnungs- und Veranstaltungsanzahl
- Übersicht statt Sackgasse
- Knopf „Noch unbekannt“
- Modell bekommt den Fallstand statt des Chats

Angepasst wurden alte Tests nur dort, wo sie das alte Verhalten festschrieben:
- Optionslisten haben jetzt zusätzlich den Knopf „Noch unbekannt“.
- Testetiketten wie „E3 Jahr unbekannt“ hießen sonst als Nutzeraussage „Jahr ist unbekannt“; sie heißen jetzt „… fehlt“.

## 4. Tatsächlich ausgeführte Live-Tests (mistral-large-latest)

- **Testprotokoll nachgespielt, fünf Läufe:** Im letzten Lauf verhalten sich alle 9 Schritte wie gewünscht.
  - Schritt 1: Faktenbestätigung ohne Rückfrage, 300 + 900 + 800, Rechnung 1.200.
  - Schritt 4: 600 / Rechnung 900.
  - Schritt 6: gezielte Widerspruchsfrage.
  - Schritte 7 bis 9: getrennter Fall; Jahr, Rechtsform und Einnahmeabsicht „ausdrücklich unbekannt“; Übersicht; „zurückgestellt“.
- **Prüfkatalog (52 Fälle):** **33 richtig, 19 nachgefragt, 0 falsch, 0 Fehler** (`aufgaben/audit/pruefkatalog_ergebnis_large.md`). Zum Vergleich Mistral ohne SaaS: 13 richtig, 36 falsch.
- **Testfall 20 Positionen:** 17 richtig, 4 nachgefragt, **0 falsch, 0 Fehler** (Lauf vor der letzten Bereinigung).

## 5. Offen

- **Speicher:** Der Fallstand liegt weiter nur im Arbeitsspeicher und ist nach einem Neustart weg. Dauerhaft in PostgreSQL: Konzept im Projektplan, Abschnitt 15, noch nicht gebaut.
- **Erkennung „unbekannt“:** Sie arbeitet mit Wortlisten (`app/fallstand_begriffe.json`) und ist nie vollständig. Absichtlich nicht erkannt wird zum Beispiel „ob sich der Betrag auf mehrere Rechnungen verteilt, ist unbekannt“.
- **Einnahmeabsicht unbekannt:** Die Bewertung wird zurückgestellt. Beide Ausgänge wie bei der Zahl der Veranstaltungen zu rechnen, wäre möglich, ist aber nicht gebaut.
- **Unklare Fallabgrenzung:** Ohne ausdrückliches „neuer Fall“ wird nicht nachgefragt.
- **Formfehler des Modells:** Gelegentlich bleibt ein Formfehler auch im zweiten Versuch. Dann kommt eine feste Rückfrage, nicht geraten.
- **Fachlich (Steuerberater):** Druckkosten innerhalb der Rechnung einer Grafikerin werden als „nachträgliche Vervielfältigung“ (R-49) ausgeschlossen. Ob es Druckvorstufe oder Erstdruck war, fragt das System nicht. Siehe Prüfliste, Frage F-09.

## 6. Zentrale Projektprüfung

- `python scripts/pruefe_alles.py` auf GitHub („Prüfen“, alle fünf Jobs): **grün** beim letzten Stand.
- Lokal meldet die Prüfung nur wegen fehlender Pakete (fastapi, httpx) einen Fehler bei den Chatbot-Tests. Alle übrigen Prüfungen sind lokal grün.
