# KSK-Assistant

Phase 1 prüft Rechnungen an selbständige Künstlerinnen, Künstler und Publizistinnen auf die Künstlersozialabgabe. Unlesbares bleibt ungeklärt. Ein Sprachmodell bewertet nicht an der Pipeline vorbei.

## Start

```bash
npm install
copy config\secrets.env.example config\secrets.env
npm run dev
```

`config/secrets.env` ist gitignored. Das Backend lädt sie beim Start in die Umgebung und überschreibt dabei keine schon gesetzten Variablen. Der Schlüssel bleibt auf dem Server. Das Frontend ruft Mistral nicht auf.

Ohne Schlüssel läuft die Ablesung im Mock-Modus. Der Bericht sagt das sichtbar. `KSK_LLM_MODE=mistral` erzwingt den echten Dienst und bricht ab, wenn der Schlüssel fehlt.

Modelle stehen in `config/models.json`: Ablesen `mistral-small-4`, `mistral-medium-3.5`, `mistral-large-3`; Bewertung und Chat `mistral-medium-3.5`; Prüfer `mistral-large-3`.

## Was Phase 1 kann

1. Fall anlegen, für Verein/KMU oder Steuerberater.
2. Eine Rechnung als PDF, PNG oder JPG hochladen, höchstens 20 MB. Ablage hinter einer Speicher-Schnittstelle, lokal unter `data/storage`.
3. Pipeline A bis G: Vorbereitung, dreifaches Ablesen von Formular und Fließtext, Abgleich in Cent, Bewertung nach Methodik v12, Prüfer, eingefrorener Bericht.
4. Bericht mit Position, Zustand, Betrag, Fundstelle, Klärungshinweis und den Kategorien Wort, Bildende Kunst, Musik, Darstellende Kunst.
5. Admin unter `/admin` mit Passwort aus `ADMIN_PASSWORD`: Libraries anlegen, Dateien an Mistral geben (`purpose=retrieval` und Zuordnung zur Library), Status, Text, aktiv setzen, löschen, Schlüsseltest ohne Anzeige des Schlüssels.
6. Chat zum Bericht in zwei Modi. Er zitiert. Er rechnet nicht und stuft nicht um.

`user_id` und `org_id` sind in den Tabellen vorhanden und in Phase 1 leer. SQLite liegt in `data/ksk.sqlite` und ist über normales SQL nach PostgreSQL mitnehmbar.

Die Warteschlange läuft im Prozess. `after()` stößt sie nach der Antwort an. Dieselbe Job-Tabelle kann später ein eigener Worker lesen.

## Regeln

Abgabesätze und Jahresgrenzen nur aus `rules/saetze.json`. 2025: 5,0 Prozent und 700 Euro. 2026: 4,9 Prozent und 1.000 Euro. 2027 fehlt absichtlich. Die Jahresgrenze gilt nur für § 24 Abs. 2 KSVG. Rundung: kaufmännisch auf ganze Cent, beschrieben in `saetze.json`.

Die Methodik v12 ist eingefroren. Berichte speichern die Version. Alte Berichte werden nicht umgedeutet.

Zwischen-JSON der Stufen wird nach dem Lauf gelöscht. Es bleiben Rechnung und Bericht. Einen Fall löschen entfernt Dokumente, Bericht und Chat.

## Tests

```bash
npm test
npx playwright install chromium
npm run test:e2e
```

Rücktests: 390-Euro-Fall, 5,0-Prozent-Fall, Summenfehler, S3a an der Grenze von genau 700 Euro.

## Phase 2, vorbereitet und nicht gebaut

`src/lib/phase2/nachweis.ts` beschreibt N-A bis N-D. Kennzeichnungen sind KONSISTENT, TEILWEISE, NICHT TRAGFÄHIG oder UNGEKLÄRT, nie „echt“. Ein Re-Run mit Nachweis, Bericht V2 und das Steuerberater-Gate vor dem Upload sind nicht aufrufbar. `POST /api/cases/:id/rerun` antwortet mit 501.

Phase 3, nur als Richtung: ein Fall bündelt später Vertrag, Rechnung und Nachweise. Die Validatoren V01 bis V06 laufen schon jetzt gegen die lokalen Regeldateien, weil Suche in einer Library dafür zu ungenau ist.

## Deployment

Vercel über `vercel.json`. SQLite auf dem Serverless-Dateisystem ist nicht dauerhaft. Für einen echten Betrieb kommt die vorbereitete PostgreSQL-Migration, bevor Fälle produktiv liegen. Der Mistral-Schlüssel wird dort als Umgebungsvariable gesetzt, nicht im Client.

## Gesperrte Ideen

Nicht gebaut, nicht als Schalter, nicht als Entwurf im Code:

Eine bezahlte Rechnung ist ein abgeschlossener Realvorgang. Die Abgabe darauf fällt an. Die Künstlersozialkasse prüft gegen Belege, nicht gegen nachträglich geändertes Papier. Nachträgliches Umschreiben oder das Konstruieren von Nachweisen, um eine pflichtige Zahlung zu beseitigen, ist kein Feature.

Ein Abgabe-Gestaltungs-Check für künftige Aufträge wäre, wenn überhaupt, nur vor Vertragsschluss denkbar, nur mit legalen Hebeln, die zum Vertrag passen und belegbar sind, und nur mit Freigabe einer Steuerberaterin oder eines Steuerberaters. Das wird hier nicht gebaut.

Mustervorlagen für künftige Verträge und Rechnungen wären, wenn überhaupt, nur allgemeine Bausteine mit echtem Sachgrund, keine Einzelfallberatung durch ein Modell. Die Grenze des Rechtsdienstleistungsgesetzes und des Steuerberatungsgesetzes bliebe: Information mit Vorlage kann zulässig sein, individuelle Beratung nicht. Auch das wird hier nicht gebaut.
