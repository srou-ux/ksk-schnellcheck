# Quellenpolitik (Entwurf)

Zweck: Schutz davor, dass falsche oder manipulierte Quellen (z. B. eine Webseite, die „neue Gesetze“ behauptet) in Regeln oder Chatbot-Antworten gelangen.

## 1. Vertrauensstufen
| Stufe | Beispiele | Verwendung |
|---|---|---|
| 1 Amtlich | gesetze-im-internet.de, BGBl, bsg.bund.de, rechtsprechung-im-internet.de, Landesjustizportale | Grundlage für Regeln |
| 2 Verwaltung | KSK (kuenstlersozialkasse.de), Deutsche Rentenversicherung | Regeln, immer gekennzeichnet „Auslegung der KSK/DRV, kein Gesetz“ |
| 3 Sekundär | Kanzlei- oder Verbandsseiten, anwalt.de, ksk-rechtshilfe.de, Fachpresse | nur Hinweis auf ein Urteil („Volltext nicht in der Quellenbasis“), nie Grundlage einer Regel |
| 4 Sonstige | Blogs, Foren, KI-generierte Seiten, unbekannte Domains | nicht verwenden |

## 2. Regeln für die Aufnahme
1. Nur Domains der Stufen 1 und 2 werden als Quelle aufgenommen; neue Domains braucht eine ausdrückliche Freigabe.
2. Jede Datei mit URL, Abrufdatum, SHA-256 und Dokumentart in `quellen/index.csv`. Originale werden nie verändert.
3. Eine neue Rechtsnorm oder Rechtsprechung gilt erst, wenn sie im amtlichen Text (Stufe 1) belegt ist, bei Gesetzen mit Verkündung im Bundesgesetzblatt. Die Behauptung einer Seite allein genügt nie.
4. Keine automatische Übernahme: Neue Quellen führen zu einem Änderungsvorschlag. Ein Mensch prüft; erst danach ändert sich eine Regel (Prüfstatus).
5. Zwei-Quellen-Prinzip bei Zahlen und Fristen: Wert aus Stufe 1 oder aus Stufe 2 mit Gegenprüfung in Stufe 1, wo vorhanden (z. B. Abgabesätze gegen die Verordnung).

## 3. Schutz im Betrieb des Chatbots
- Der Bot liest keine Webseiten live. Er antwortet nur aus dem geprüften Regelwerk und den gespeicherten Quellen.
- Hochgeladene Dokumente und Webtexte sind Daten, keine Anweisungen (Schutz vor Prompt-Injection).
- Jede Antwort nennt Fundstelle und Stufe der Quelle.
- Änderungs-Überwachung (spätere Idee): meldet neue Dokumente an einen Prüfer, ändert nichts selbst.
- Auffälligkeiten (Widerspruch zwischen Quelle und Regelwerk) werden im Lückenprotokoll vermerkt.

## 4. Für Claude Code (Recherche)
Nur Stufe 1 und 2 herunterladen. Stufe 3 nur in Listen („Hinweis“) mit Kennzeichnung „Sekundärquelle“. Nichts aus Stufe 4.
