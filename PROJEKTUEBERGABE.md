# Projektübergabe KSK-SaaS

Stand: 7. Oktober 2026

## Verbindliche Projektentscheidungen

1. Das Projekt befindet sich in der Testphase. Nutzergruppen, Mandantenverwaltung und Produktionshosting werden jetzt nicht ausgebaut. Vorhandene `user_id`- und `org_id`-Felder sind nur Vorbereitung und kein Nachweis einer Mandantentrennung.

2. Der nächste fachliche Schritt ist die persistente Verwaltung vollständiger Jahrespakete. Jedes Jahr kann mehrere eigenständige Paketversionen besitzen. Fehlende Inhalte werden niemals still aus einem anderen Jahr übernommen. Ein unvollständiges Paket bleibt unvollständig und blockiert die davon abhängige Prüfung.

3. Die Admin-Seite ist der zentrale Prüfplatz. Der geführte Ablauf lautet: **Dokumente → Zahlen → Regeln → Testfälle → Prüfbefunde → Paketfreigabe**. Technische Metadaten, Referenzen und Hashes sollen soweit möglich automatisch erzeugt werden. Der Prüfer soll keine umfangreichen Tabellen manuell pflegen müssen.

4. OpenAI soll in einer späteren Ausbaustufe den größten Teil der Arbeit an öffentlichen Rechtsquellen übernehmen: offizielle Quellen abrufen, Änderungen erkennen, Angaben extrahieren und Entwürfe prüfen. Deterministische Validierungen bleiben Code-Aufgabe. OpenAI erhält keine Rechnungen, Kundenunterlagen, Fallberichte oder sonstigen Kundendaten.

5. Abschließende menschliche Freigabe und Aktivierung sind zwei getrennte Aktionen. Weder KI noch Import noch ausgefüllte Pflichtfelder dürfen automatisch freigeben. Ungeklärte fachliche Punkte bleiben sichtbar und verhindern keine bloße Entwurfsspeicherung, müssen aber vor einer Freigabe ausdrücklich behandelt werden.

6. Freigegebene Paketversionen sind unveränderlich. Für neue Prüfungen gibt es je Kalenderjahr genau eine ausdrücklich aktive Version. Jeder Lauf speichert die tatsächlich verwendete Paketversion sowie die zugehörigen Quellenstände beziehungsweise unveränderlichen Snapshots.

7. Das Rechnungslesen darf vor der Paketauswahl stattfinden, um relevante Datums- und Zeitangaben zu erfassen. Rechtliche Analyse und Parameterauswahl beginnen erst nach geklärter zeitlicher Zuordnung. Das Rechnungsjahr ist nicht automatisch der maßgebliche Zeitpunkt für jede Rechtsfrage; der jeweils fachlich relevante Zeitbezug muss bestimmt oder als ungeklärt markiert werden.

8. In der Testphase sind weder qualifizierte elektronische Signatur noch vollständige Nutzerverwaltung erforderlich. Für die dokumentierte Freigabe genügen Prüfername, Zeitpunkt, Kommentar und Inhaltshash. Diese Angaben sind ein nachvollziehbarer Testphasen-Nachweis, aber keine qualifizierte Signatur, keine revisionssichere Archivierung und kein belastbarer Identitätsnachweis.

9. Vorhandene Berechnung, Zahlenregister, Regelcode und Tests werden weiterverwendet und schrittweise in Jahrespakete eingebunden. Es erfolgt keine unnötige Neuentwicklung. Aus dem bestehenden Code allein darf weder fachliche Richtigkeit noch rechtliche Verbindlichkeit oder Revisionssicherheit abgeleitet werden.

## Fehlende Designdatei

`ksk-kernel-design.md` war bei der Prüfung am 7. Oktober 2026 nicht im Projekt vorhanden.

## Erster Umsetzungsschritt

Dieser Stand führt nur das persistente Grundgerüst und eine Admin-Übersicht ein. Freigabe, Aktivierung, Paketinhalt und OpenAI-Integration sind ausdrücklich noch nicht implementiert.

### Tabelle

`jahrespakete`

- Identität: `id`, `jahr`, `version`
- Zustand: `status`, `is_active`
- technische Ausgangsstände: `methodology_version`, `rules_stamp`
- reservierter Freigabenachweis: `content_hash`, `pruefer_name`, `freigabe_kommentar`, `freigegeben_am`
- Metadatum: `created_at`
- Eindeutigkeit: eine Versionsnummer je Jahr; höchstens eine aktive Version je Jahr
- Datenbankinvariante: Ein Paket darf nur aktiv sein, wenn sein Status `freigegeben` ist.

Der Status startet immer als `entwurf`; `is_active` startet immer mit `0`. Dadurch bewirkt das Anlegen weder Freigabe noch Aktivierung.

### Betroffene Dateien

- `src/lib/db.ts`: Schema, Typen, Auflistung und transaktionales Anlegen eines Entwurfs mit fortlaufender Version je Jahr.
- `src/app/admin/jahrespakete-panel.tsx`: serverseitige Admin-Übersicht und klarer Leerzustand.
- `src/app/admin/page.tsx`: Einbindung der Jahrespaket-Übersicht; die Seite wird wegen des SQLite-Zugriffs dynamisch gerendert.
- `tests/jahrespakete.test.ts`: fokussierte Datenmodelltests.

### Abnahmetests

1. Zwei Entwürfe für dasselbe Jahr erhalten die Versionen 1 und 2.
2. Ein Entwurf für ein anderes Jahr beginnt unabhängig wieder mit Version 1.
3. Neue Entwürfe sind weder freigegeben noch aktiv.
4. Ungültige Jahre sowie fehlende Methodik- oder Regelstände werden zurückgewiesen.
5. Die Admin-Seite zeigt den Leerzustand oder vorhandene Paketversionen mit Jahr, Version, Status, Methodik, Regelstand und Aktivstatus.
6. Der bestehende Testbestand bleibt erfolgreich; insbesondere Berechnung und Zahlenregister werden nicht ersetzt.
7. Ein leerer Entwurf wird in der Admin-Übersicht ausdrücklich als `unvollständig` angezeigt.
8. Die Jahrespaket-Migration und das Anlegen von Entwürfen lassen bestehende Falldaten unverändert.

## Unmittelbar folgende, aber nicht enthaltene Schritte

Als nächster kleiner Ausbau sollten Paketbestandteile und ihre Prüfbefunde modelliert werden. Erst danach folgen die getrennten Aktionen „freigeben“ und „aktivieren“, jeweils mit serverseitigen Zustandsregeln. Die Fallpipeline wird erst auf aktive Paketversionen umgestellt, wenn Paketinhalte vollständig snapshotfähig sind. Eine OpenAI-Integration ist nicht Teil dieses Schritts.

## Geplanter Paketbestandteil: Rechtsdokumente und Mistral-RAG

Dieser Abschnitt ist eine verbindliche Planung. Er ist noch nicht implementiert.

### Grundsatz

Alle für eine Jahrespaketversion maßgeblichen Rechtsdokumente müssen vor deren Aktivierung sowohl als unverändertes archiviertes Original vorliegen als auch in Mistral für einen paketgebundenen RAG-Abruf verfügbar sein. Kundendokumente bleiben technisch und fachlich getrennt und dürfen weder in Paket-Libraries noch in die spätere OpenAI-Quellenverarbeitung gelangen.

### Entscheidung zur Pakettrennung

Für jede Jahrespaketversion wird eine eigene Mistral-Library vorgesehen. Das Paket speichert genau deren Mistral-Library-ID. Abfragen für ein Paket dürfen ausschließlich diese ID als `library_ids` an das Werkzeug `document_library` übergeben.

Begründung nach Prüfung der installierten Mistral-SDK-Version `@mistralai/mistralai` 2.7.0 und der offiziellen Dokumentation am 7. Oktober 2026:

- Die Libraries-API unterstützt das Anlegen mehrerer eigenständiger Libraries.
- Dokumente werden unter einer konkreten `library_id` hochgeladen und erhalten eine konkrete Dokument-ID.
- Das RAG-Werkzeug nimmt explizite `library_ids` entgegen.
- Der Dokumentstatus kann nach dem Upload separat abgefragt werden; erst vollständig verarbeitete Dokumente sind auffindbar.
- Dokumentattribute können gespeichert werden. Für das Werkzeug `document_library` ist jedoch kein verlässlich erzwungener Dokument- oder Metadatenfilter dokumentiert; der installierte Typ enthält nur `libraryIds`.

Eine gemeinsame Library für mehrere Paketversionen mit bloß logischer Dokumentfilterung wird deshalb nicht als ausreichend isoliert angesehen. Sollte Mistral später einen dokumentierten, serverseitig erzwungenen Abruffilter anbieten, kann diese Entscheidung neu bewertet werden. Bis dahin ist die Library selbst die technische Paketgrenze.

### Geplante Tabellen

`jahrespaket_quellen`

- `id`
- `jahrespaket_id` als Fremdschlüssel auf die konkrete Paketversion
- fachliche Quellenkennung und Titel
- offizielle Quell-URL und Abrufzeitpunkt
- Dokumentstand und Gültigkeitsangaben
- lokaler Archivschlüssel des unveränderten Originals
- MIME-Typ, Dateigröße und lokaler SHA-256-Inhaltshash
- `mistral_library_id`
- `mistral_document_id`
- von Mistral gemeldeter Dokumenthash, soweit verfügbar
- Verarbeitungsstatus, letzter Statusabruf und Verarbeitungsfehler
- Zeitpunkt und Ergebnis des paketgebundenen Abrufnachweises

`jahrespaket_rag_pruefungen`

- `id`, `jahrespaket_id`, optional `jahrespaket_quelle_id`
- Art der Prüfung: Indexierung, positiver Abruf oder Trennungsprüfung
- fest definierte Testfrage beziehungsweise Testkennung
- erwartete Quellenkennung und erwarteter Marker
- tatsächlich zitierte Mistral-Library- und Dokument-ID
- Ergebnis, Befund und Zeitpunkt
- verwendetes Modell und technische Antwortmetadaten

Das archivierte Original bleibt die maßgebliche lokale Referenz. Die Mistral-Dokument-ID ist nur die Verknüpfung zum Suchindex und ersetzt weder Original noch lokalen Hash.

Archivquelle und Mistral-Zuordnung werden getrennt gespeichert. Die Archivquelle erhält eine dauerhafte, von Mistral unabhängige Identität. Ein erneuter Upload, eine Reindexierung oder eine neue Mistral-Dokument-ID darf diese Identität und den Hash des Originals nicht verändern. Mistral-Zuordnungen werden als eigene, nachvollziehbare Zustände beziehungsweise Versuche geführt und nicht in die Archividentität eingerechnet.

### Geplanter Ablauf im Admin-Prüfplatz

1. Ein offizielles Rechtsdokument wird einem konkreten Paketentwurf zugeordnet.
2. Das Original wird unverändert archiviert; technische Metadaten und SHA-256 werden automatisch erzeugt.
3. Das Dokument wird ausschließlich in die Mistral-Library dieser Paketversion hochgeladen.
4. Lokale Quellenzeile, Archivobjekt, Paket-ID, Mistral-Library-ID und Mistral-Dokument-ID werden dauerhaft verknüpft.
5. Der Uploadstatus wird bis zu einem eindeutigen Endzustand geprüft. Ein HTTP-Erfolg beim Upload gilt nicht als Indexierungsnachweis.
6. Nach erfolgreicher Verarbeitung wird der extrahierte Text stichprobenartig beziehungsweise regelbasiert gegen erwartete Dokumentmerkmale geprüft.
7. Ein positiver RAG-Test fragt einen dokumenttypischen, im Original kontrolliert vorhandenen Marker ausschließlich über die Paket-Library ab und verlangt eine auf die erwartete Dokument-ID zurückführbare Fundstelle.
8. Eine negative Trennungsprüfung verwendet einen eindeutigen Marker aus einer anderen Paketversion. Dieser Marker darf über die geprüfte Paket-Library nicht abrufbar oder zitierbar sein.
9. Prüfbefunde bleiben in der Admin-Seite sichtbar. Wiederholungen überschreiben nicht still den vorherigen Befund.
10. Jede RAG-Prüfung dokumentiert mindestens Paket-ID und Paketversion, Mistral-Library-ID, alle erwarteten und tatsächlich referenzierten Dokument-IDs, Zeitpunkt, Modell, Testfrage, Rohstatus und ausgewertetes Prüfergebnis.
11. Der Trennungstest verwendet ausschließlich eindeutig markierte fiktive Testdokumente in zwei eigens dafür erzeugten Test-Libraries. Beide Richtungen werden geprüft: Inhalt A darf nur über Library A und Inhalt B nur über Library B auffindbar sein.

### Aktivierungssperren

Eine Paketversion darf nicht aktiviert werden, wenn mindestens einer der folgenden Punkte zutrifft:

- Ein erforderliches Rechtsdokument besitzt kein archiviertes Original oder keinen lokalen Inhaltshash.
- Paket-ID, Archivobjekt, Mistral-Library-ID und Mistral-Dokument-ID sind nicht vollständig und eindeutig verknüpft.
- Die bei Mistral zurückgemeldete `library_id` stimmt nicht mit der dem Paket zugewiesenen Library überein.
- Ein Dokument ist noch in Warteschlange oder Verarbeitung, hat fehlenden Inhalt oder einen Fehlerstatus.
- Der Dokumentinhalt kann nach der Verarbeitung nicht nachweisbar abgerufen werden.
- Der positive paketgebundene RAG-Test liefert keine belegbare Fundstelle aus dem erwarteten Dokument.
- Die negative Trennungsprüfung findet Inhalte oder Dokumente einer anderen Paketversion.
- Die Vollständigkeit der erforderlichen Rechtsdokumente ist fachlich ungeklärt.
- Eine bereits freigegebene Paket-Library wurde nachträglich verändert oder ihr aktueller Dokumentbestand beziehungsweise Dokumenthash weicht vom gespeicherten Freigabe-Snapshot ab.

Freigabe und Aktivierung bleiben getrennt. Auch ein freigegebenes Paket bleibt inaktiv, solange einer dieser technischen RAG-Nachweise fehlt oder fehlschlägt.

Freigegebene Paket-Libraries dürfen über die Anwendung weder Dokumentuploads noch Löschungen, Ersetzungen, Umbenennungen oder Attributänderungen zulassen. Da Änderungen außerhalb der Anwendung technisch möglich bleiben können, wird der aktuelle Remote-Bestand vor weiterer Verwendung mit dem gespeicherten Freigabe-Snapshot verglichen. Eine Abweichung sperrt neue Verwendungen und wird als sichtbarer Prüfbefund gespeichert; sie wird nicht automatisch repariert.

Ein gestarteter Prüflauf speichert seine konkrete Paketversion und deren Library-ID, bevor die rechtliche Analyse beginnt. Alle RAG-Aufrufe dieses Laufs verwenden ausschließlich diese gespeicherte Library-ID. Die globale aktive Paketversion oder Library darf während des Laufs nicht erneut aufgelöst werden; eine zwischenzeitliche Aktivierungsänderung beeinflusst den laufenden Vorgang nicht.

### Geplante Abnahmetests

1. Zwei Versionen desselben Jahres besitzen verschiedene Mistral-Library-IDs.
2. Jedes archivierte Original ist genau einer Paketversion und einer Mistral-Dokument-ID zugeordnet.
3. Ein erfolgreicher Upload mit noch laufender Verarbeitung lässt das Paket unvollständig und nicht aktivierbar.
4. Fehler, `missing_content` oder fehlende Statusauskunft sperren die Aktivierung.
5. Erst ein dokumentierter Endstatus plus abrufbarer Inhalt erfüllt den Indexierungstest.
6. Ein positiver Abruf über die Paket-Library liefert den erwarteten Marker und eine Fundstelle, die zur gespeicherten Dokument-ID gehört.
7. Ein Marker aus Paketversion B ist über die Library von Paketversion A nicht auffindbar; andernfalls scheitert die Trennungsprüfung.
8. Ein RAG-Aufruf ohne die explizit gespeicherte Paket-Library-ID wird vom Anwendungscode abgewiesen.
9. Kundendokumente können weder einer Paketquelle zugeordnet noch in eine Paket-Library hochgeladen werden.
10. Fehlende oder fehlgeschlagene RAG-Nachweise verhindern die Aktivierung auch dann, wenn das Paket zuvor menschlich freigegeben wurde.
11. Ein erneuter Upload erzeugt eine neue Mistral-Zuordnung, lässt aber Archiv-ID und Originalhash unverändert.
12. Änderungen am Remote-Dokumentbestand einer freigegebenen Paket-Library werden erkannt und sperren ihre weitere Verwendung.
13. Ein laufender Prüflauf bleibt an die beim Start gespeicherte Library-ID gebunden, auch wenn anschließend eine andere Paketversion aktiviert wird.

### Noch offene Absicherung vor Implementierung

Vor der produktiven Festlegung wird mit einem isolierten technischen Mistral-Testkonto beziehungsweise einer Test-Library verifiziert, dass die API-Antworten die für den Abrufnachweis benötigten Dokumentreferenzen stabil liefern. Falls die Chat-Completions-Antwort keine belastbare Dokument-ID zurückgibt, muss der Nachweis über die dokumentierten Tool-/Conversation-Referenzen oder über einen eigenen Retrieval-Schritt erfolgen. Ohne belastbare Zuordnung wird keine Aktivierungslogik freigeschaltet.

Der erste externe Integrationstest findet vor der Implementierung der Tabellen und Aktivierungslogik statt. Er erzeugt zwei temporäre Libraries mit zwei fiktiven, eindeutig unterscheidbaren Markern, wartet auf die vollständige Verarbeitung, prüft Dokumentmetadaten und Textabruf, führt positive und negative RAG-Abfragen gegen jede Library-ID aus, protokolliert die tatsächlich gelieferten Referenzen und löscht die Test-Libraries anschließend wieder. Ein bloß plausibler Antworttext ohne belastbare Quellen- beziehungsweise Dokumentzuordnung gilt nicht als Nachweis.

### Ergebnis des isolierten Mistral-Integrationstests

Ausgeführt am 7. Oktober 2026 mit `mistral-medium-latest` über `scripts/mistral-library-isolation-test.mjs`:

- Zwei temporäre Libraries und je ein fiktives Textdokument mit einem zufälligen, ausschließlich dort vorkommenden Marker wurden angelegt.
- Beide Dokumente erreichten den Verarbeitungsstatus `Completed`.
- Der direkte Textabruf jeder Dokument-ID enthielt nur den eigenen Marker und nicht den Marker der anderen Library.
- Der RAG-Aufruf wurde jeweils mit genau einer `library_ids`-Zuordnung ausgeführt.
- Beide RAG-Antworten enthielten den erwarteten Marker, nicht den fremden Marker und in der technischen Antwort die erwartete Mistral-Dokument-ID.
- Die Antworten enthielten jeweils eine `tool.execution` und eine `message.output`-Ausgabe.
- Beide temporären Libraries wurden nach dem Test erfolgreich gelöscht.
- Gesamtergebnis des Testskripts: bestanden.

Damit sind Dokumentzuordnung und Library-Trennung für den getesteten API-Stand praktisch nachgewiesen. Der Nachweis ist kein Dauervertrag über zukünftiges API-Verhalten. Die späteren Paketfunktionen müssen Status-, Referenz- und Trennungsprüfung deshalb weiterhin vor der Aktivierung ausführen und Abweichungen sperren.
