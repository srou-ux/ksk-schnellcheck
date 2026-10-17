# Konzept: Prüfweg je Rechnung und Speicherung

Stand: 11.10.2026. Status: **Konzept, noch nicht gebaut.** Umsetzung erst, wenn der Chatbot stabil läuft (eine Sache nach der anderen). Keine Rechtsberatung; die mit „(prüfen)“ markierten Punkte muss ein Steuerberater oder Anwalt bestätigen.

## 1. Ziel

Für jede Rechnung soll nachvollziehbar sein, **wie** das System zu seinem Vorschlag kam: welche Fakten, welche Prüfschritte, welche Regeln (R-xx) und Textbausteine (TB-xx), welche Fundstellen und welche Fassung. So kann der Steuerberater jeden Vorschlag prüfen, und bei einer Betriebsprüfung lässt sich der Weg auch Jahre später zeigen.

## 2. Grundidee: Regeln einmal, Fälle klein

- Prüfschritte, Regeln und Textbausteine werden **einmal** gepflegt (Excel `regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx`), jeweils mit Version und Gültigkeit. Erwartet: etwa 20–50 Prüfschritte. Es gibt also nicht für jeden der vielen Fälle eigene Texte.
- Je Fall wird nur gespeichert, **welcher Weg** durch diese Schritte gegangen wurde (als Daten), nicht der fertige Text.
- Die Erklärung wird **bei Bedarf neu erzeugt**, aus Fakten, Prüfweg und Regelversion. Weil die alten Versionen nie überschrieben werden, entsteht immer genau dieselbe Erklärung wie damals.

## 3. Was je Rechnung gespeichert wird

| Inhalt | Beispiel |
|---|---|
| Bestätigte Fakten (ohne Namen, Adressen, IBAN, Rechnungsnummern) | Jahr, Betrag, Rechtsform, Art des Auftraggebers, Veranstaltungen |
| Prüfweg als Daten | Liste der Schritte mit Ergebnis, Regel-IDs, Fundstellen |
| Ergebnis des Kerns | Ergebnisklasse, Bemessungsgrundlage, Abgabe |
| Versionen | Version von Regelkatalog/`parameter.json`, Programmversion, Fakten-Hash |
| Entscheidung des Steuerberaters | bestätigt / geändert / abgelehnt, Kommentar (Pflicht bei Änderung), Person, Zeitpunkt |

Größe: etwa **1–3 KB je Rechnung**, bei einer Million Rechnungen etwa 1–3 GB. Das ist klein.

## 4. Was bewusst NICHT gespeichert wird

- Der Chattext und die rohen Antworten des Sprachmodells (enthalten oft Namen und überflüssige Angaben).
- Die fertig formulierte Erklärung (wird neu erzeugt, siehe Abschnitt 2).
- Hochgeladene Dokumente nach der Auswertung (Regel dafür später festlegen, prüfen).

Grund: Was nicht gespeichert ist, kann nicht verloren gehen oder in falsche Hände geraten (Datensparsamkeit).

## 5. Wie lange

- Mindestens **5 Jahre** nach Ablauf des Kalenderjahres, weil Aufzeichnungen nach § 28 KSVG (R-83) aufzubewahren sind und Prüfungen mehrere Jahre zurückgehen. Danach löschen. (prüfen)
- Ob zusätzlich steuerliche oder berufsrechtliche Fristen der Kanzlei gelten (zum Beispiel 10 Jahre), muss geklärt werden. (prüfen)

## 6. Nutzen der Entscheidungen des Steuerberaters

Weil seine Entscheidung mitgespeichert wird, sieht man später, wo das System falsch lag und welche Fälle oft „Grenzfall“ werden. Daraus werden Verbesserungen und Kanzleiregeln vorgeschlagen (nur nach Bestätigung gültig), ohne Kundendaten auszuwerten.

## 7. Offene Fragen (vor dem Bau klären)

1. Aufbewahrungsfrist bestätigen: 5 Jahre nach § 28 KSVG oder länger? (Steuerberater)
2. Datenschutz: DSGVO-Löschpflicht, Auftragsverarbeitungsvertrag mit den Kanzleien, Verschwiegenheit (Anwalt/Steuerberaterkammer).
3. Für wen zuerst die Ansicht des Prüfwegs: Steuerberater (ausführlich) oder Mandant (einfach)?
4. Speicherort: Datenbank in der EU bei einem Anbieter mit Sitz in Deutschland oder der EU.

## 8. Bezug zu bestehenden Dokumenten

Projektplan Abschnitt 5 (Datenmodell mit Historie) und Abschnitt 6 (Kontrolle durch den Steuerberater, „Protokollieren statt überschreiben“). Kopie dieses Konzepts im Projektplan (claude.ai-Projekt „ksk“, Abschnitt 15).
