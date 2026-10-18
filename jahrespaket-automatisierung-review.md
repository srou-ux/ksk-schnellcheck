# Review: fortsetzbare Jahrespaket-Recherche

Stand: 7. Oktober 2026

## Umsetzung

- Dokumentstand akzeptiert Tages- und Monatsstände (`YYYY-MM-DD`, `YYYY-MM`, Eingabe auch `MM.YYYY`). Die Admin-Anzeige formatiert Monatsstände als `MM.YYYY`.
- Dokumentstand, `gueltig_ab`, `gueltig_bis` und der Status der rechtlichen Anwendung werden getrennt gespeichert.
- Amtliche Quellen werden auch bei ungeklärter zeitlicher Anwendung archiviert. Ungeklärte Aussagen bleiben ausdrücklich offen.
- Unveränderte Dateien werden über SHA-256 im vorhandenen unveränderlichen Archiv wiederverwendet.
- Jeder Paketentwurf besitzt weiterhin genau eine Mistral-Library. Archivierte Quellen werden automatisch hochgeladen und bis zum Verarbeitungsstatus abgefragt.
- Der inzwischen von Mistral abgelehnte allgemeine File-Purpose `retrieval` ist nicht mehr Voraussetzung für den Library-Dokumentupload.
- Wiederholungen setzen dieselbe Vorbereitung und Paketversion fort. Bei vorhandenen Funden wird keine neue Vollrecherche ausgeführt.
- Offene Aufgaben sind typisiert: `technische_beschaffung`, `metadaten_fehlen`, `zeitliche_anwendung`, `fachlicher_widerspruch`, `quelle_fehlt`.
- Nachrecherchen haben einen stabilen Aufgabenschlüssel, höchstens drei Versuche und ein gespeichertes Ergebnis. Das Kostenlimit beträgt 1,00 USD; gezielte Folgefragen verwenden innerhalb desselben Anbieters `gpt-6.1-sol`. Aufgaben oberhalb des Limits erhalten den Status `kostenlimit`.
- Freigabe und Aktivierung bleiben unverändert manuell und wurden nicht in den Workflow aufgenommen.

## Datenbank

Migration `007-jahrespaket-recherche-workflow` in `src/lib/db.ts`:

- Neue Tabelle `jahrespaket_nachrecherchen` mit Aufgabe, Typ, stabilem Schlüssel, Status, Versuchen, Ergebnis, Fehler und Kosten.
- Neue Felder an `jahrespaket_quellenfunde`: `dokumentstand_art`, `gueltig_ab`, `gueltig_bis`, `anwendung_status`, `luecken_typ`, `paket_quelle_id`.
- Neue Felder an `jahrespaket_vorbereitungen`: `kostenlimit_usd`, `kosten_usd`.
- Bestehende Tabellen und Daten bleiben erhalten.

## Lokale Prüfung

- Gesamttests: 13 Testdateien, 79 Tests bestanden.
- TypeScript: bestanden.
- Gezielter ESLint-Lauf: bestanden.
- Next.js-Produktions-Build: bestanden.
- Fixtures prüfen insbesondere Monatsstand, Archivierung trotz offener Anwendung, Mistral-Verarbeitung, Wiederverwendung derselben Paketversion, SHA-256-Wiederverwendung, Fehlerklassifikation und maximal drei Nachrechercheversuche.

## Begrenzter Live-Test 2026

- Wiederverwendete Vorbereitung: `7f07d182-38db-48d4-a7bc-66c9f8be0ca5`.
- Wiederverwendetes Paket: `35a28eab-c39f-42b4-8fd5-059cb3f7ed26`.
- Keine neue Paketversion bei den Fortsetzungen.
- 15 Quellenfunde sichtbar, davon 12 im aktuellen Vorbereitungslauf archiviert und verarbeitet.
- Die Paket-Library meldete insgesamt 14 bereits vorhandene oder neu verarbeitete Paketdokumente.
- Zwei Monatsstände wurden normalisiert gespeichert und werden als Monat/Jahr angezeigt.
- Eine gezielte Nachrecherche zur zeitlichen Anwendung des KSVG wurde im ersten Versuch gelöst.
- Tatsächlich geschätzte OpenAI-Kosten des Laufes: 0,963166 USD bei einem Limit von 1,00 USD.
- 15 weitere Aufgaben wurden nachvollziehbar mit `kostenlimit` angehalten: sieben fehlende Metadaten, zwei zeitliche Anwendungen und sechs fehlende Quellen/Prüfumfangsnachweise.
- Keine automatische Freigabe oder Aktivierung.

Der erste Live-Versuch zeigte eine abgeschnittene strukturierte Antwort; das Antwortbudget wurde korrigiert. Der zweite zeigte die geänderte Mistral-Validierung für `purpose=retrieval`; der direkte Library-Upload wurde daraufhin erfolgreich geprüft. Beide Fehler und die erfolgreichen Fortsetzungen blieben am selben Entwurf gebunden.
