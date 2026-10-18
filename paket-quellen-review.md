# Paketquellen und RAG-Prüfprotokolle — Prüfexport

Stand: 7. Oktober 2026

Dieser Export beschreibt ausschließlich die implementierte Quellenzuordnung und die RAG-Prüfprotokolle für Jahrespakete. Er enthält keine Schlüssel, Umgebungsdateien, Datenbankinhalte, Kundenunterlagen oder sonstigen Kundendaten.

Nicht implementiert wurden Paketaktivierung, OpenAI-Integration und Umschaltung der Kundenfallpipeline.

## Geänderte Dateien

- `src/lib/db.ts`: additive Migration `005-paket-quellen-rag`, Schutztrigger und nebenläufigkeitstolerante Spaltenerweiterung.
- `src/lib/paket-quellen.ts`: Archivierung, Paket-/Library-Zuordnung, Uploadversuche, Verarbeitungsstatus, Indexmanifeste, RAG-Protokolle, Remote-Abweichungsprüfung und Admin-Statusprojektion.
- `src/app/admin/jahrespakete-panel.tsx`: Statusansicht je Paketquelle.
- `tests/paket-quellen.test.ts`: sechs neue Domänen- und Persistenztests.
- `e2e/paket-quellen.spec.ts`: Browser-Abnahmetest für die neue Admin-Sektion.

## Migration 005

Die Migration ist rein additiv. Bestehende Fall-, Dokument-, Lauf-, Berichts-, Chat-, Library- und Zahlenregistertabellen werden nicht gelöscht oder umgeschrieben.

### `archiv_quellen`

```sql
CREATE TABLE IF NOT EXISTS archiv_quellen (
  id TEXT PRIMARY KEY,
  dateipfad TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  herkunft TEXT NOT NULL,
  dokumentstand TEXT NOT NULL,
  abrufdatum TEXT NOT NULL,
  original_name TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
```

Die Datei wird unter `data/archive/rechtsquellen/<Hash-Präfix>/<SHA-256>` beziehungsweise im konfigurierten `KSK_DATA_DIR` abgelegt. `writeFileSync(..., { flag: "wx" })` verhindert Überschreiben. Existiert der Inhalt bereits, wird sein Hash erneut geprüft. Datenbanktrigger verbieten Update und Delete archivierter Quellen.

### `jahrespaket_bibliotheken`

```sql
CREATE TABLE IF NOT EXISTS jahrespaket_bibliotheken (
  id TEXT PRIMARY KEY,
  jahrespaket_id TEXT NOT NULL UNIQUE,
  mistral_library_id TEXT NOT NULL UNIQUE,
  remote_manifest_hash TEXT,
  remote_checked_at TEXT,
  blockiert_grund TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id)
);
```

Damit besitzt jede Paketversion höchstens eine eigene Library und dieselbe Mistral-Library kann nicht zwei Paketversionen zugeordnet werden.

### `jahrespaket_quellen`

```sql
CREATE TABLE IF NOT EXISTS jahrespaket_quellen (
  id TEXT PRIMARY KEY,
  jahrespaket_id TEXT NOT NULL,
  archiv_quelle_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (jahrespaket_id, archiv_quelle_id),
  FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id),
  FOREIGN KEY (archiv_quelle_id) REFERENCES archiv_quellen(id)
);
```

Diese Tabelle ordnet ein unveränderliches Archivoriginal einer konkreten Paketversion zu. Sie enthält bewusst keine Mistral-Dokument-ID.

### `jahrespaket_mistral_zuordnungen`

```sql
CREATE TABLE IF NOT EXISTS jahrespaket_mistral_zuordnungen (
  id TEXT PRIMARY KEY,
  jahrespaket_quelle_id TEXT NOT NULL,
  mistral_library_id TEXT NOT NULL,
  mistral_document_id TEXT,
  upload_status TEXT NOT NULL,
  verarbeitungsstatus TEXT NOT NULL,
  mistral_document_hash TEXT,
  fehler TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (jahrespaket_quelle_id) REFERENCES jahrespaket_quellen(id)
);
```

Jeder erneute Upload erzeugt eine neue Zeile. Archiv-ID und Originalhash bleiben unverändert. Ein erfolgreicher Upload benötigt eine Dokument-ID; Library-ID und Paket-Library müssen übereinstimmen.

### `jahrespaket_indexmanifeste`

```sql
CREATE TABLE IF NOT EXISTS jahrespaket_indexmanifeste (
  id TEXT PRIMARY KEY,
  jahrespaket_id TEXT NOT NULL,
  mistral_library_id TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  dokumente_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  invalidated_at TEXT,
  invalidated_reason TEXT,
  FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id)
);
```

Das kanonische Manifest enthält pro Paketquelle Archiv-ID, Archivhash, Zuordnungs-ID, Mistral-Dokument-ID und optional den Mistral-Dokumenthash. Sein SHA-256 bindet den Nachweis an Library und Dokumentbestand. Neue Quellen, Uploadversuche oder Statusänderungen invalidieren alle zuvor aktuellen Manifeste.

### `jahrespaket_rag_pruefungen`

```sql
CREATE TABLE IF NOT EXISTS jahrespaket_rag_pruefungen (
  id TEXT PRIMARY KEY,
  jahrespaket_id TEXT NOT NULL,
  indexmanifest_id TEXT NOT NULL,
  jahrespaket_quelle_id TEXT,
  art TEXT NOT NULL,
  modell TEXT NOT NULL,
  testfrage TEXT NOT NULL,
  erwartete_dokument_ids_json TEXT NOT NULL,
  referenzierte_dokument_ids_json TEXT NOT NULL,
  bestanden INTEGER NOT NULL,
  ergebnis_json TEXT NOT NULL,
  fehler TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id),
  FOREIGN KEY (indexmanifest_id) REFERENCES jahrespaket_indexmanifeste(id),
  FOREIGN KEY (jahrespaket_quelle_id) REFERENCES jahrespaket_quellen(id)
);
```

Positive Prüfungen bestehen nur, wenn alle erwarteten Dokument-IDs referenziert werden, keine unbekannte ID vorkommt und das Manifest aktuell ist. Negative Trennungsprüfungen bestehen nur ohne referenzierte Dokument-ID. Rohes Prüfergebnis und konkrete Fehler werden dauerhaft gespeichert.

### Schutztrigger und Indizes

- Eindeutige Archiv-ID-/Hash-Kombination.
- Indizes für aktuelle Uploadzuordnung, Manifest und RAG-Prüfung.
- Archivquellen können weder aktualisiert noch gelöscht werden.
- Nach Paketfreigabe blockieren Datenbanktrigger Insert, Update und Delete von Paketquellen und Mistral-Zuordnungen.
- Library-ID und Paketbezug einer freigegebenen Paket-Library können nicht geändert oder gelöscht werden.
- Technische Remote-Prüffelder dürfen weiter aktualisiert werden, damit externe Abweichungen auch nach Freigabe dokumentiert und gesperrt werden können.

## Neue Domänenfunktionen

Vollständig implementiert in `src/lib/paket-quellen.ts`:

```ts
archiviereOriginal(input)
ordnePaketBibliothekZu(paketId, mistralLibraryId)
ordneArchivquelleZu(paketId, archivQuelleId)
protokolliereMistralUpload(input)
aktualisiereVerarbeitungsstatus(input)
erzeugeIndexmanifest(paketId)
protokolliereRagPruefung(input)
pruefeExternenIndex(paketId, remoteDocuments)
listPaketQuellenStatus()
```

Wesentliche Zustandsregeln:

1. Ein Archivoriginal wird inhaltsadressiert und nie überschrieben.
2. Archividentität, Paketzuordnung und Mistral-Uploadversuch sind getrennte Datensätze.
3. Ein Indexmanifest kann nur entstehen, wenn jede Paketquelle eine aktuelle Dokument-ID mit abgeschlossenem Verarbeitungsstatus besitzt.
4. Jeder neue Upload oder Verarbeitungsstatus macht ältere Manifeste und daran gebundene RAG-Nachweise veraltet.
5. Unbekannte Dokumentreferenzen lassen eine positive Prüfung scheitern.
6. Ein abweichender Remote-Dokumentbestand invalidiert das Manifest und setzt einen sichtbaren Sperrgrund.
7. Freigegebene Quellenbestände sind auf Funktions- und Datenbankebene schreibgeschützt.

## Admin-Anzeige

Das Server Component `src/app/admin/jahrespakete-panel.tsx` zeigt je Paketquelle:

- Paketjahr und Paketversion,
- Archiv-ID und Originalname,
- Archivstatus `vorhanden`, `fehlt` oder `hash_abweichung`,
- Uploadstatus,
- Verarbeitungsstatus,
- RAG-Status `ausstehend`, `bestanden`, `fehlgeschlagen` oder `veraltet`,
- konkrete Upload-, Verarbeitungs-, RAG- oder Remote-Abweichungsfehler.

Die Oberfläche sagt ausdrücklich: „Ein Upload allein ist nicht verwendbar.“

## Tests

`tests/paket-quellen.test.ts` prüft:

1. Getrennte Archividentität, Paketzuordnung und zwei erneute Uploadzuordnungen.
2. Unveränderten Archivhash und unveränderten Archivinhalt nach erneutem Upload.
3. Fehlgeschlagene Verarbeitung, sichtbaren Fehler und blockierte Manifesterstellung.
4. Unbekannte Dokumentreferenzen und fehlende erwartete Referenzen.
5. Veraltete Prüfnachweise nach erneutem Upload.
6. Identischen sowie extern abweichenden Remote-Dokumentbestand.
7. Schreibsperren nach Paketfreigabe.
8. Erhalt bereits vorhandener Falldaten.

`e2e/paket-quellen.spec.ts` prüft konzeptionell im Browser:

- Überschrift der Quellen-/RAG-Sektion,
- sichtbaren Hinweis, dass Upload allein nicht verwendbar ist,
- den leeren Ausgangszustand.

## Tatsächliche Prüfergebnisse

Ausgeführt mit `C:\Program Files\nodejs\node.exe`:

```powershell
& 'C:\Program Files\nodejs\node.exe' 'node_modules/typescript/bin/tsc' --noEmit

$env:NODE_ENV='test'
& 'C:\Program Files\nodejs\node.exe' 'node_modules/vitest/vitest.mjs' run tests/paket-quellen.test.ts tests/jahrespakete.test.ts
& 'C:\Program Files\nodejs\node.exe' 'node_modules/vitest/vitest.mjs' run

& 'C:\Program Files\nodejs\node.exe' 'node_modules/eslint/bin/eslint.js' src/lib/db.ts src/lib/paket-quellen.ts src/app/admin/jahrespakete-panel.tsx tests/paket-quellen.test.ts e2e/paket-quellen.spec.ts
```

Ergebnisse:

- TypeScript: Exitcode 0.
- Relevante Tests: 2 Dateien, 11 Tests bestanden.
- Vollständiger Vitest-Bestand: 12 Dateien, 73 Tests bestanden.
- Gezielter ESLint-Lauf: Exitcode 0, keine Warnungen oder Fehler im finalen Lauf.
- Vitest gibt weiterhin die bereits bekannte, nicht fehlschlagende Vite-Warnung zur künftig geplanten nativen Konfigurationsladung aus.

### Browserprüfung

Der neue Playwright-Test wurde angelegt, aber nicht als bestanden gewertet:

- Der normale Playwright-Lauf erreichte nach 180 Sekunden sein Zeitlimit, ohne Testergebnis.
- Ein bereits vorhandener Node-Prozess auf Port 3000 stammt vom 6. Oktober 2026 und antwortete bei einer HTTP-Prüfung nicht innerhalb von 30 Sekunden. Er wurde nicht beendet, weil er nicht in diesem Arbeitsschritt gestartet wurde.
- Der direkte Playwright-Start scheiterte eindeutig daran, dass das erwartete Chromium-Executable nicht installiert ist.

Lokaler Nachholbefehl:

```powershell
npx playwright install chromium
npx playwright test e2e/paket-quellen.spec.ts
```

Der Browsercheck ist damit offen, nicht bestanden.

## Bewusste Grenzen

- Keine Paketaktivierung.
- Keine automatische Paketfreigabe.
- Keine OpenAI-Integration.
- Keine Verwendung der neuen Pakettabellen durch Kundenfallläufe.
- Keine neue Upload-UI oder schreibende Admin-Route; dieser Schritt liefert Persistenz, Zustandslogik, Prüfprotokolle und lesende Admin-Transparenz.
- Die externe Bestandsprüfung erhält einen von einem späteren Mistral-Adapter gelesenen Remote-Bestand. Die Netzwerk-Orchestrierung wird erst mit der kontrollierten Quellen-Uploadfunktion angebunden.
