# Auftrag: Befunde aus dem ersten Livetest im Codespace (10.10.2026)

Entwurf – vom Steuerberater zu prüfen. Nur in `app/` und `tests/app/` arbeiten; Werte und Texte, die Rechtsaussagen sind, gehören in den Regelkatalog (Excel), nicht in den Code. Erfolgskriterium: `python scripts/pruefe_alles.py` meldet „ALLES GRÜN", alle bisherigen Abnahmen bleiben bei 0 Lücken.

Getestet: Codespace, Demo-Modus (FakeLLM), Stand `d3a3555`. Alle Befunde wurden direkt gegen `app/router.py` nachgestellt.

## L1 (kritisch): Verwerterart wird stillschweigend angenommen
- Eingabe: `Werbeagentur 2026, freie Grafikerin, 900 €` → Faktenbestätigung zeigt nur Jahr, Leistung, Auftragnehmer, Position. Nach „Ja" kommt **„Nicht abgabepflichtig (Vorschlag)"**, weil 900 € unter der Schwelle liegen.
- Eine Werbeagentur ist typischer Verwerter (§ 24 Abs. 1 KSVG); dort gilt keine Schwelle. Das Ergebnis ist also voraussichtlich falsch.
- Ursache: `app/router.py` (um Zeile 335–343) setzt bei `verwerterart is None` stillschweigend `typischer_verwerter=False` bzw. `"generalklausel"`/Eigenwerbung. Das trifft auch Mistral, sobald das Modell `verwerterart` nicht setzt.
- Soll:
  1. `verwerterart` ist Pflichtangabe für jeden Kernaufruf, der davon abhängt (Schwellenprüfung, Veranstaltungen, Positionen). Fehlt sie: Rückfrage mit Knöpfen (Eigenwerbung / typischer Verwerter / Generalklausel – Texte aus festen Bausteinen), nie Standardwert.
  2. `verwerterart` erscheint in der Faktenbestätigung (z. B. „Art des Auftraggebers: Eigenwerbung").
  3. Kein Default mehr im Router; ein Wächter-Test prüft, dass ohne `verwerterart` kein Ergebnis „Nicht abgabepflichtig" oder „Abgabepflichtig" entsteht.
  4. Tests: 900 € mit `typischer_verwerter` → abgabepflichtig; 900 € mit `eigenwerber` 2026 → nicht abgabepflichtig; 900 € ohne Angabe → Rückfrage.

- **Mit Mistral bestätigt (10.10.2026, Codespace):** Gleiche Eingabe → Faktenbestätigung ohne Hinweis auf „Werbeagentur" → „Nicht abgabepflichtig (Vorschlag)", Norm „KSVG § 24 Abs. 2 Satz 1 Nr. 1" (Eigenwerbung). Das Modell setzt `verwerterart` nicht (vermutlich wegen des Verbots von Rechtseinstufungen aus Nachtrag 1f, Abschnitt I). Lösung daher im Router/den Pflichtangaben, nicht im Prompt: Wenn die Nutzerfrage einen Branchenbegriff nennt (z. B. Agentur), soll die Rückfrage ihn als Hinweis zeigen, die Einstufung trifft aber der Nutzer per Knopf.

## L2: Demo-Modus nutzt den Verlauf nicht
- `app/llm/fake.py::extrahiere_fakten` ignoriert `verlauf`. Nach einer Rückfrage („natürliche Person") gehen Jahr und Betrag der ersten Nachricht verloren; es folgen neue Rückfragen.
- Soll: wie im Mistral-Adapter Verlauf und Frage zusammen auswerten. Test: Dialog „Eigenwerbung 2026, Grafikerin für Flyer, 1.200 €" → „natürliche Person" führt zur Faktenbestätigung.

## L3: Eigener Knopf wird nicht erkannt
- Der Knopf sendet „natürliche Person", `_RECHTSFORM_MUSTER` sucht nur „natuerliche person". „Einzelperson", „Einzelunternehmer", „Privatperson" werden ebenfalls nicht erkannt.
- Soll: Umlaute normalisieren; jede Knopf-Option muss von der Extraktion erkannt werden (Test über alle `rueckfrage_optionen`). Kein Raten bei unklaren Wörtern.

## L4: Jeder Eurobetrag wird zur Position
- „… weil 1.200 € über der Schwelle von 1.000 € liegen" ergibt drei Positionen. Im Demo-Modus hinnehmbar, aber: bei mehreren Beträgen in einer Nachricht die Positionen in der Faktenbestätigung deutlich zeigen (ist der Fall) – nur dokumentieren, nicht umbauen.

## L5: Darstellung
- Rückfragetexte ohne Umlaute („natuerliche", „ansaessig"); Etikett „FAKTENBESTAETIGUNG NOETIG". Für die Anzeige echte Umlaute.
- Faktenbestätigung zeigt die Fakten doppelt (Satz und Liste); die Liste reicht.
- Faktenbestätigung zeigt interne Begriffe („Anfrageart: bewertung", „(honorar)"); für Nutzer verständliche Bezeichnungen verwenden oder weglassen.
- Subsumtionszeile zeigt „Summe 1200 € … Schwelle 1000 €" ohne deutsches Zahlenformat, darüber steht derselbe Inhalt formatiert; eine Zeile reicht, deutsches Format.

## L6: Fundstelle passt nicht zum Jahr
- Für 2026 erscheint in der Liste der Fundstellen „KSVG § 24 Abs. 2 S. 2, § 54". § 54 regelt nur 2025 (700 €). Fundstellen nach Jahr filtern (Gültigkeit aus dem Regelkatalog). Doppelte Fundstellen („S. 2" und „Satz 2 (aktuell)") zusammenfassen. Wenn die Ursache im Regelkatalog liegt: in `aufgaben/FUNDE_Chatbot.md` melden, nicht selbst ändern.

## Nachher
Arbeitsstand ergänzen, Kurzbericht: was behoben, Testergebnis, was offen.
