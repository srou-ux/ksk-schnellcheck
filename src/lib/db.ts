import { mkdirSync } from "node:fs";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import { dataDir } from "./config";
import { loadSecrets } from "./secrets";

let db: DatabaseSync | null = null;

export interface CaseRow {
  id: string;
  user_id: string | null;
  org_id: string | null;
  title: string;
  audience: string;
  status: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface DocumentRow {
  id: string;
  case_id: string;
  user_id: string | null;
  org_id: string | null;
  kind: string;
  storage_key: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  page_count: number | null;
  created_at: string;
}

export interface RunRow {
  id: string;
  case_id: string;
  user_id: string | null;
  org_id: string | null;
  methodology_version: string;
  library_id: string | null;
  library_version: string | null;
  status: string;
  current_stage: string | null;
  gate_report_json: string | null;
  error_layperson: string | null;
  examiner_finding: string | null;
  reading_mode: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ReportRow {
  id: string;
  run_id: string;
  case_id: string;
  user_id: string | null;
  org_id: string | null;
  report_version: number;
  methodology_version: string;
  payload_json: string;
  created_at: string;
}

export interface LibraryRow {
  id: string;
  mistral_library_id: string | null;
  name: string;
  description: string | null;
  version_label: string;
  is_active: number;
  created_at: string;
}

export interface LibraryDocumentRow {
  id: string;
  library_id: string;
  mistral_file_id: string | null;
  mistral_document_id: string | null;
  name: string;
  status: string;
  page_count: number | null;
  summary: string | null;
  error: string | null;
  created_at: string;
}

export type JahrespaketStatus = "entwurf" | "zur_freigabe" | "freigegeben" | "ersetzt" | "zurueckgezogen";

export interface JahrespaketRow {
  id: string;
  jahr: number;
  version: number;
  status: JahrespaketStatus;
  methodology_version: string;
  rules_stamp: string;
  content_hash: string | null;
  pruefer_name: string | null;
  freigabe_kommentar: string | null;
  freigegeben_am: string | null;
  is_active: number;
  created_at: string;
}

export function getDb(): DatabaseSync {
  if (process.env.NODE_ENV !== "test") loadSecrets();
  if (!db) {
    const dir = dataDir();
    mkdirSync(dir, { recursive: true });
    db = new DatabaseSync(path.join(dir, "ksk.sqlite"), { timeout: 10000 });
    db.exec("PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;");
    migrate(db);
  }
  return db;
}

export function closeDb(): void {
  db?.close();
  db = null;
}

function migrate(database: DatabaseSync): void {
  database.exec(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS cases (
      id TEXT PRIMARY KEY,
      user_id TEXT,
      org_id TEXT,
      title TEXT NOT NULL,
      audience TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      deleted_at TEXT
    );
    CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      kind TEXT NOT NULL,
      storage_key TEXT NOT NULL,
      original_name TEXT NOT NULL,
      mime_type TEXT NOT NULL,
      size_bytes INTEGER NOT NULL,
      page_count INTEGER,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS runs (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      methodology_version TEXT NOT NULL,
      library_id TEXT,
      library_version TEXT,
      status TEXT NOT NULL,
      current_stage TEXT,
      gate_report_json TEXT,
      error_layperson TEXT,
      examiner_finding TEXT,
      reading_mode TEXT,
      created_at TEXT NOT NULL,
      completed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS stage_artifacts (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      stage TEXT NOT NULL,
      confirmed INTEGER NOT NULL,
      temporary INTEGER NOT NULL,
      payload_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reports (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      case_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      report_version INTEGER NOT NULL,
      methodology_version TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS chat_messages (
      id TEXT PRIMARY KEY,
      case_id TEXT NOT NULL,
      report_id TEXT NOT NULL,
      user_id TEXT,
      org_id TEXT,
      mode TEXT NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      citations_json TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reference_libraries (
      id TEXT PRIMARY KEY,
      mistral_library_id TEXT,
      name TEXT NOT NULL,
      description TEXT,
      version_label TEXT NOT NULL,
      is_active INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reference_documents (
      id TEXT PRIMARY KEY,
      library_id TEXT NOT NULL,
      mistral_file_id TEXT,
      mistral_document_id TEXT,
      name TEXT NOT NULL,
      status TEXT NOT NULL,
      page_count INTEGER,
      summary TEXT,
      error TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS llm_usage (
      id TEXT PRIMARY KEY,
      endpoint TEXT NOT NULL,
      model TEXT NOT NULL,
      prompt_tokens INTEGER NOT NULL,
      completion_tokens INTEGER NOT NULL,
      total_tokens INTEGER NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jobs (
      id TEXT PRIMARY KEY,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL,
      status TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      error TEXT,
      created_at TEXT NOT NULL,
      locked_at TEXT,
      finished_at TEXT
    );
    CREATE TABLE IF NOT EXISTS zahlen_register (
      id TEXT PRIMARY KEY,
      gruppe TEXT NOT NULL,
      version INTEGER NOT NULL,
      betrag REAL,
      einheit TEXT NOT NULL,
      gueltig_ab TEXT NOT NULL,
      gueltig_bis TEXT,
      quelle TEXT NOT NULL,
      freigabe TEXT NOT NULL,
      beschreibung TEXT NOT NULL,
      thema TEXT,
      stichworte_json TEXT,
      bedingung TEXT,
      created_at TEXT NOT NULL,
      wert_cent INTEGER,
      wert_exakt TEXT,
      wert_bps INTEGER,
      anwendungsbereich TEXT,
      fundstelle TEXT,
      dokumentstand TEXT,
      freigabe_nachweis TEXT,
      herkunft TEXT
    );
    CREATE TABLE IF NOT EXISTS zahlen_revisionen (
      id TEXT PRIMARY KEY,
      zeile_id TEXT NOT NULL,
      aktion TEXT NOT NULL,
      zustand_json TEXT NOT NULL,
      grund TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jahrespakete (
      id TEXT PRIMARY KEY,
      jahr INTEGER NOT NULL,
      version INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'entwurf',
      methodology_version TEXT NOT NULL,
      rules_stamp TEXT NOT NULL,
      content_hash TEXT,
      pruefer_name TEXT,
      freigabe_kommentar TEXT,
      freigegeben_am TEXT,
      is_active INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
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
    CREATE TABLE IF NOT EXISTS jahrespaket_quellen (
      id TEXT PRIMARY KEY,
      jahrespaket_id TEXT NOT NULL,
      archiv_quelle_id TEXT NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE (jahrespaket_id, archiv_quelle_id),
      FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id),
      FOREIGN KEY (archiv_quelle_id) REFERENCES archiv_quellen(id)
    );
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
    CREATE TABLE IF NOT EXISTS jahrespaket_vorbereitungen (
      id TEXT PRIMARY KEY,
      jahrespaket_id TEXT NOT NULL,
      jahr INTEGER NOT NULL,
      anforderung_version TEXT NOT NULL,
      status TEXT NOT NULL,
      schritt TEXT NOT NULL,
      fortschritt INTEGER NOT NULL,
      modell TEXT NOT NULL,
      prompt_version TEXT NOT NULL,
      luecken_json TEXT NOT NULL,
      fehler TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      completed_at TEXT,
      FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id)
    );
    CREATE TABLE IF NOT EXISTS jahrespaket_quellenfunde (
      id TEXT PRIMARY KEY,
      vorbereitung_id TEXT NOT NULL,
      jahrespaket_id TEXT NOT NULL,
      kategorie TEXT NOT NULL,
      titel TEXT NOT NULL,
      url TEXT NOT NULL,
      herausgeber TEXT,
      dokumentstand TEXT,
      zeitbezug TEXT NOT NULL,
      status TEXT NOT NULL,
      archiv_quelle_id TEXT,
      fehler TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (vorbereitung_id) REFERENCES jahrespaket_vorbereitungen(id),
      FOREIGN KEY (jahrespaket_id) REFERENCES jahrespakete(id),
      FOREIGN KEY (archiv_quelle_id) REFERENCES archiv_quellen(id)
    );
    CREATE TABLE IF NOT EXISTS jahrespaket_nachrecherchen (
      id TEXT PRIMARY KEY,
      vorbereitung_id TEXT NOT NULL,
      aufgabe_key TEXT NOT NULL,
      kategorie TEXT NOT NULL,
      typ TEXT NOT NULL,
      suchauftrag TEXT NOT NULL,
      status TEXT NOT NULL,
      versuche INTEGER NOT NULL DEFAULT 0,
      max_versuche INTEGER NOT NULL DEFAULT 3,
      ergebnis_json TEXT,
      fehler TEXT,
      kosten_usd REAL NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      UNIQUE (vorbereitung_id, aufgabe_key),
      FOREIGN KEY (vorbereitung_id) REFERENCES jahrespaket_vorbereitungen(id)
    );
    CREATE TABLE IF NOT EXISTS quellenkatalog (
      id TEXT PRIMARY KEY,
      katalog_key TEXT NOT NULL UNIQUE,
      art TEXT NOT NULL,
      titel TEXT NOT NULL,
      url TEXT NOT NULL,
      dokumentnummer TEXT,
      herausgeber TEXT,
      listenherkunft TEXT NOT NULL,
      archiv_quelle_id TEXT,
      erfasst_am TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (archiv_quelle_id) REFERENCES archiv_quellen(id)
    );
    CREATE TABLE IF NOT EXISTS quellen_auswertungen (
      id TEXT PRIMARY KEY,
      sha256 TEXT NOT NULL,
      jahr INTEGER NOT NULL,
      umfang_version TEXT NOT NULL,
      auswertung_version TEXT NOT NULL,
      ergebnis_json TEXT NOT NULL,
      created_at TEXT NOT NULL,
      UNIQUE (sha256, jahr, umfang_version, auswertung_version)
    );
  `);
  const stamp = new Date().toISOString();
  const note = database.prepare("INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?, ?)");
  note.run("001-phase1", stamp);
  note.run("002-zahlen-register", stamp);
  for (const [name, ddl] of [
    ["wert_cent", "INTEGER"],
    ["wert_exakt", "TEXT"],
    ["wert_bps", "INTEGER"],
    ["anwendungsbereich", "TEXT"],
    ["fundstelle", "TEXT"],
    ["dokumentstand", "TEXT"],
    ["freigabe_nachweis", "TEXT"],
    ["herkunft", "TEXT"],
  ] as const) {
    addColumn(database, "zahlen_register", name, ddl);
  }
  addColumn(database, "reports", "register_ids_json", "TEXT");
  addColumn(database, "reports", "register_snapshot_json", "TEXT");
  database.exec("DROP INDEX IF EXISTS zahlen_register_fassung");
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS zahlen_register_version
      ON zahlen_register (gruppe, version)`);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS zahlen_freigegeben_anfang
      ON zahlen_register (gruppe, anwendungsbereich, gueltig_ab, wert_exakt)
      WHERE freigabe = 'freigegeben'`);
  korrigiereImportfreigaben(database);
  note.run("003-zahlen-freigabe", stamp);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS jahrespakete_jahr_version
      ON jahrespakete (jahr, version)`);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS jahrespakete_aktive_version
      ON jahrespakete (jahr) WHERE is_active = 1`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespakete_aktiv_nur_freigegeben_insert
      BEFORE INSERT ON jahrespakete
      WHEN NEW.is_active = 1 AND NEW.status != 'freigegeben'
      BEGIN
        SELECT RAISE(ABORT, 'Ein aktives Jahrespaket muss freigegeben sein.');
      END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespakete_aktiv_nur_freigegeben_update
      BEFORE UPDATE OF is_active, status ON jahrespakete
      WHEN NEW.is_active = 1 AND NEW.status != 'freigegeben'
      BEGIN
        SELECT RAISE(ABORT, 'Ein aktives Jahrespaket muss freigegeben sein.');
      END`);
  note.run("004-jahrespakete", stamp);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS archiv_quellen_id_hash
      ON archiv_quellen (id, sha256)`);
  database.exec(`CREATE INDEX IF NOT EXISTS jahrespaket_zuordnungen_quelle_zeit
      ON jahrespaket_mistral_zuordnungen (jahrespaket_quelle_id, created_at DESC)`);
  database.exec(`CREATE INDEX IF NOT EXISTS jahrespaket_manifeste_paket_zeit
      ON jahrespaket_indexmanifeste (jahrespaket_id, created_at DESC)`);
  database.exec(`CREATE INDEX IF NOT EXISTS jahrespaket_rag_manifest_art_zeit
      ON jahrespaket_rag_pruefungen (indexmanifest_id, art, created_at DESC)`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS archiv_quellen_unveraenderlich_update
      BEFORE UPDATE ON archiv_quellen BEGIN SELECT RAISE(ABORT, 'Archivquellen sind unveränderlich.'); END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS archiv_quellen_unveraenderlich_delete
      BEFORE DELETE ON archiv_quellen BEGIN SELECT RAISE(ABORT, 'Archivquellen sind unveränderlich.'); END`);
  for (const [name, table, packageExpression] of [
    ["paketquelle", "jahrespaket_quellen", "OLD.jahrespaket_id"],
    ["zuordnung", "jahrespaket_mistral_zuordnungen", "(SELECT q.jahrespaket_id FROM jahrespaket_quellen q WHERE q.id = OLD.jahrespaket_quelle_id)"],
  ] as const) {
    database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_${name}_freigabe_update
        BEFORE UPDATE ON ${table}
        WHEN (SELECT status FROM jahrespakete WHERE id = ${packageExpression}) = 'freigegeben'
        BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
    database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_${name}_freigabe_delete
        BEFORE DELETE ON ${table}
        WHEN (SELECT status FROM jahrespakete WHERE id = ${packageExpression}) = 'freigegeben'
        BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  }
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_paketquelle_freigabe_insert
      BEFORE INSERT ON jahrespaket_quellen
      WHEN (SELECT status FROM jahrespakete WHERE id = NEW.jahrespaket_id) = 'freigegeben'
      BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_bibliothek_freigabe_insert
      BEFORE INSERT ON jahrespaket_bibliotheken
      WHEN (SELECT status FROM jahrespakete WHERE id = NEW.jahrespaket_id) = 'freigegeben'
      BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_bibliothek_freigabe_update
      BEFORE UPDATE OF jahrespaket_id, mistral_library_id ON jahrespaket_bibliotheken
      WHEN (SELECT status FROM jahrespakete WHERE id = OLD.jahrespaket_id) = 'freigegeben'
      BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_bibliothek_freigabe_delete
      BEFORE DELETE ON jahrespaket_bibliotheken
      WHEN (SELECT status FROM jahrespakete WHERE id = OLD.jahrespaket_id) = 'freigegeben'
      BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  database.exec(`CREATE TRIGGER IF NOT EXISTS jahrespaket_zuordnung_freigabe_insert
      BEFORE INSERT ON jahrespaket_mistral_zuordnungen
      WHEN (SELECT p.status FROM jahrespakete p JOIN jahrespaket_quellen q ON q.jahrespaket_id = p.id WHERE q.id = NEW.jahrespaket_quelle_id) = 'freigegeben'
      BEGIN SELECT RAISE(ABORT, 'Freigegebene Paketquellen sind unveränderlich.'); END`);
  note.run("005-paket-quellen-rag", stamp);
  database.exec(`CREATE UNIQUE INDEX IF NOT EXISTS jahrespaket_vorbereitung_aktiv
      ON jahrespaket_vorbereitungen (jahr) WHERE status IN ('queued', 'running')`);
  database.exec(`CREATE INDEX IF NOT EXISTS jahrespaket_quellenfunde_vorbereitung
      ON jahrespaket_quellenfunde (vorbereitung_id, created_at)`);
  note.run("006-jahrespaket-vorbereitung", stamp);
  for (const [table, name, ddl] of [
    ["jahrespaket_quellenfunde", "dokumentstand_art", "TEXT"],
    ["jahrespaket_quellenfunde", "gueltig_ab", "TEXT"],
    ["jahrespaket_quellenfunde", "gueltig_bis", "TEXT"],
    ["jahrespaket_quellenfunde", "anwendung_status", "TEXT NOT NULL DEFAULT 'ungeklaert'"],
    ["jahrespaket_quellenfunde", "luecken_typ", "TEXT"],
    ["jahrespaket_quellenfunde", "paket_quelle_id", "TEXT"],
    ["jahrespaket_vorbereitungen", "kostenlimit_usd", "REAL NOT NULL DEFAULT 1.00"],
    ["jahrespaket_vorbereitungen", "kosten_usd", "REAL NOT NULL DEFAULT 0"],
  ] as const) addColumn(database, table, name, ddl);
  database.exec(`CREATE INDEX IF NOT EXISTS jahrespaket_nachrecherchen_status
      ON jahrespaket_nachrecherchen (vorbereitung_id, status, created_at)`);
  note.run("007-jahrespaket-recherche-workflow", stamp);
  addColumn(database, "archiv_quellen", "dokumentstand_genauigkeit", "TEXT");
  note.run("008-quellenkatalog", stamp);
  addColumn(database, "jahrespaket_quellenfunde", "workflow_version", "TEXT NOT NULL DEFAULT 'legacy-recherche'");
  const debugMigration = database.prepare("SELECT id FROM schema_migrations WHERE id = '009-recherche-status-debug'").get();
  if (!debugMigration) {
    database.exec(`UPDATE jahrespaket_quellenfunde
      SET anwendung_status = 'ungeklaert', luecken_typ = COALESCE(luecken_typ, 'zeitliche_anwendung')
      WHERE anwendung_status = 'belegt' AND (
        lower(zeitbezug) LIKE '%nicht gesondert verifiziert%'
        OR lower(zeitbezug) LIKE '%nicht abschließend verifiziert%'
        OR lower(zeitbezug) LIKE '%darf nicht%übertragen%'
        OR lower(zeitbezug) LIKE '%inkrafttreten%nicht%verifiziert%'
      )`);
    database.exec(`UPDATE jahrespaket_nachrecherchen SET status = 'hinweis', fehler = 'Kein automatisch lösbarer Rechercheauftrag.'
      WHERE aufgabe_key LIKE 'gemeldet:%' AND (
        lower(suchauftrag) LIKE '%noch zukünftigen%'
        OR lower(suchauftrag) LIKE '%bedeutet hier%'
      )`);
    database.exec(`UPDATE jahrespaket_nachrecherchen SET fehler =
      'Kostenlimit: ' || printf('%.6f', (SELECT v.kosten_usd FROM jahrespaket_vorbereitungen v WHERE v.id = vorbereitung_id)) ||
      ' USD verbraucht + 0.12 USD Reserve > ' || printf('%.2f', (SELECT v.kostenlimit_usd FROM jahrespaket_vorbereitungen v WHERE v.id = vorbereitung_id)) || ' USD Limit.'
      WHERE status = 'kostenlimit'`);
  }
  note.run("009-recherche-status-debug", stamp);
}

function addColumn(database: DatabaseSync, table: string, name: string, ddl: string): void {
  const cols = database.prepare(`PRAGMA table_info(${table})`).all() as Array<{ name: string }>;
  if (cols.some((col) => col.name === name)) return;
  try {
    database.exec(`ALTER TABLE ${table} ADD COLUMN ${name} ${ddl}`);
  } catch (error) {
    if (error instanceof Error && /duplicate column name/i.test(error.message)) return;
    throw error;
  }
}

export function korrigiereImportfreigaben(database?: DatabaseSync): number {
  const db = database ?? getDb();
  const rows = db.prepare(`SELECT * FROM zahlen_register
    WHERE freigabe = 'freigegeben' AND (freigabe_nachweis IS NULL OR freigabe_nachweis = '')`).all() as Array<Record<string, unknown>>;
  if (rows.length === 0) return 0;
  const stamp = new Date().toISOString();
  const revision = db.prepare(`INSERT INTO zahlen_revisionen (id, zeile_id, aktion, zustand_json, grund, created_at)
    VALUES (?, ?, 'freigabe_korrigiert', ?, ?, ?)`);
  const update = db.prepare(`UPDATE zahlen_register
    SET freigabe = 'entwurf', herkunft = COALESCE(herkunft, 'import')
    WHERE id = ? AND freigabe = 'freigegeben' AND (freigabe_nachweis IS NULL OR freigabe_nachweis = '')`);
  db.exec("BEGIN IMMEDIATE");
  try {
    for (const row of rows) {
      revision.run(
        crypto.randomUUID(),
        String(row.id),
        JSON.stringify(row),
        "Import ohne Freigabenachweis. Der Status wird auf Entwurf gesetzt. Der vorherige Zustand liegt in zahlen_revisionen.",
        stamp,
      );
      update.run(String(row.id));
    }
    db.exec("COMMIT");
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
  return rows.length;
}

function now(): string {
  return new Date().toISOString();
}

export function createCase(input: { title: string; audience: string }): CaseRow {
  const id = crypto.randomUUID();
  const stamp = now();
  getDb().prepare(`INSERT INTO cases (id, user_id, org_id, title, audience, status, created_at, updated_at, deleted_at)
    VALUES (?, NULL, NULL, ?, ?, 'entwurf', ?, ?, NULL)`).run(id, input.title, input.audience, stamp, stamp);
  return getCase(id)!;
}

export function listCases(): CaseRow[] {
  return getDb().prepare("SELECT * FROM cases WHERE deleted_at IS NULL ORDER BY created_at DESC").all() as unknown as CaseRow[];
}

export function getCase(id: string): CaseRow | null {
  return (getDb().prepare("SELECT * FROM cases WHERE id = ? AND deleted_at IS NULL").get(id) as CaseRow | undefined) ?? null;
}

export function setCaseStatus(id: string, status: string): void {
  getDb().prepare("UPDATE cases SET status = ?, updated_at = ? WHERE id = ?").run(status, now(), id);
}

export function addDocument(input: Omit<DocumentRow, "created_at" | "user_id" | "org_id" | "page_count"> & { pageCount?: number | null }): DocumentRow {
  const stamp = now();
  getDb().prepare(`INSERT INTO documents (id, case_id, user_id, org_id, kind, storage_key, original_name, mime_type, size_bytes, page_count, created_at)
    VALUES (?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)`).run(
    input.id, input.case_id, input.kind, input.storage_key, input.original_name, input.mime_type, input.size_bytes, input.pageCount ?? null, stamp,
  );
  return getDb().prepare("SELECT * FROM documents WHERE id = ?").get(input.id) as unknown as DocumentRow;
}

export function listDocuments(caseId: string): DocumentRow[] {
  return getDb().prepare("SELECT * FROM documents WHERE case_id = ? ORDER BY created_at").all(caseId) as unknown as DocumentRow[];
}

export function getDocument(id: string): DocumentRow | null {
  return (getDb().prepare("SELECT * FROM documents WHERE id = ?").get(id) as unknown as DocumentRow | undefined) ?? null;
}

export function createRun(input: { caseId: string; methodologyVersion: string; libraryId: string | null; libraryVersion: string | null; readingMode: string }): RunRow {
  const id = crypto.randomUUID();
  const stamp = now();
  getDb().prepare(`INSERT INTO runs (id, case_id, user_id, org_id, methodology_version, library_id, library_version, status, current_stage, gate_report_json, error_layperson, examiner_finding, reading_mode, created_at, completed_at)
    VALUES (?, ?, NULL, NULL, ?, ?, ?, 'queued', 'A', NULL, NULL, NULL, ?, ?, NULL)`).run(
    id, input.caseId, input.methodologyVersion, input.libraryId, input.libraryVersion, input.readingMode, stamp,
  );
  return getRun(id)!;
}

export function getRun(id: string): RunRow | null {
  return (getDb().prepare("SELECT * FROM runs WHERE id = ?").get(id) as RunRow | undefined) ?? null;
}

export function latestRun(caseId: string): RunRow | null {
  return (getDb().prepare("SELECT * FROM runs WHERE case_id = ? ORDER BY created_at DESC LIMIT 1").get(caseId) as RunRow | undefined) ?? null;
}

export function updateRun(id: string, patch: Partial<Pick<RunRow, "status" | "current_stage" | "gate_report_json" | "error_layperson" | "examiner_finding" | "completed_at">>): void {
  const current = getRun(id);
  if (!current) return;
  getDb().prepare(`UPDATE runs SET status = ?, current_stage = ?, gate_report_json = ?, error_layperson = ?, examiner_finding = ?, completed_at = ? WHERE id = ?`).run(
    patch.status ?? current.status,
    patch.current_stage === undefined ? current.current_stage : patch.current_stage,
    patch.gate_report_json === undefined ? current.gate_report_json : patch.gate_report_json,
    patch.error_layperson === undefined ? current.error_layperson : patch.error_layperson,
    patch.examiner_finding === undefined ? current.examiner_finding : patch.examiner_finding,
    patch.completed_at === undefined ? current.completed_at : patch.completed_at,
    id,
  );
}

export function addArtifact(runId: string, stage: string, payload: unknown, confirmed: boolean, temporary = true): void {
  getDb().prepare(`INSERT INTO stage_artifacts (id, run_id, stage, confirmed, temporary, payload_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), runId, stage, confirmed ? 1 : 0, temporary ? 1 : 0, JSON.stringify(payload), now());
}

export function clearTemporaryArtifacts(runId: string): void {
  getDb().prepare("DELETE FROM stage_artifacts WHERE run_id = ? AND temporary = 1").run(runId);
}

export function insertReport(input: { runId: string; caseId: string; methodologyVersion: string; payload: unknown }): ReportRow {
  const id = crypto.randomUUID();
  const version = Number((getDb().prepare("SELECT COUNT(*) AS n FROM reports WHERE case_id = ?").get(input.caseId) as { n: number }).n) + 1;
  const payload = input.payload as { registerIds?: string[]; registerSnapshot?: unknown };
  const ids = Array.isArray(payload?.registerIds) ? JSON.stringify(payload.registerIds) : null;
  const snapshot = payload?.registerSnapshot === undefined ? null : JSON.stringify(payload.registerSnapshot);
  getDb().prepare(`INSERT INTO reports (id, run_id, case_id, user_id, org_id, report_version, methodology_version, payload_json, created_at, register_ids_json, register_snapshot_json)
    VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)`).run(
    id, input.runId, input.caseId, version, input.methodologyVersion, JSON.stringify(input.payload), now(), ids, snapshot,
  );
  return getReportByCase(input.caseId)!;
}

export function getReportByCase(caseId: string): ReportRow | null {
  return (getDb().prepare("SELECT * FROM reports WHERE case_id = ? ORDER BY created_at DESC LIMIT 1").get(caseId) as ReportRow | undefined) ?? null;
}

export function addChat(input: { caseId: string; reportId: string; mode: string; role: string; content: string }): void {
  getDb().prepare(`INSERT INTO chat_messages (id, case_id, report_id, user_id, org_id, mode, role, content, citations_json, created_at)
    VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, NULL, ?)`).run(crypto.randomUUID(), input.caseId, input.reportId, input.mode, input.role, input.content, now());
}

export function listChat(caseId: string): Array<{ id: string; mode: string; role: string; content: string; created_at: string }> {
  return getDb().prepare("SELECT id, mode, role, content, created_at FROM chat_messages WHERE case_id = ? ORDER BY created_at").all(caseId) as unknown as Array<{ id: string; mode: string; role: string; content: string; created_at: string }>;
}

export function logLlmUsage(input: { endpoint: string; model: string; promptTokens: number; completionTokens: number; totalTokens: number }): void {
  getDb().prepare(`INSERT INTO llm_usage (id, endpoint, model, prompt_tokens, completion_tokens, total_tokens, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), input.endpoint, input.model, input.promptTokens, input.completionTokens, input.totalTokens, now());
}

export function enqueueJob(runId: string): string {
  const id = crypto.randomUUID();
  getDb().prepare("INSERT INTO jobs (id, type, payload_json, status, attempts, error, created_at, locked_at, finished_at) VALUES (?, 'pipeline', ?, 'queued', 0, NULL, ?, NULL, NULL)")
    .run(id, JSON.stringify({ runId }), now());
  return id;
}

export function claimNextJob(): { id: string; runId: string } | null {
  const row = getDb().prepare("SELECT id, payload_json FROM jobs WHERE status = 'queued' AND type = 'pipeline' ORDER BY created_at LIMIT 1").get() as { id: string; payload_json: string } | undefined;
  if (!row) return null;
  const changed = getDb().prepare("UPDATE jobs SET status = 'running', locked_at = ?, attempts = attempts + 1 WHERE id = ? AND status = 'queued'").run(now(), row.id);
  if (Number(changed.changes) !== 1) return null;
  const payload = JSON.parse(row.payload_json) as { runId: string };
  return { id: row.id, runId: payload.runId };
}

export function finishJob(id: string, error: string | null): void {
  getDb().prepare("UPDATE jobs SET status = ?, error = ?, finished_at = ? WHERE id = ?").run(error ? "failed" : "done", error, now(), id);
}

export function activeLibrary(): LibraryRow | null {
  return (getDb().prepare("SELECT * FROM reference_libraries WHERE is_active = 1 LIMIT 1").get() as LibraryRow | undefined) ?? null;
}

export function listLibraries(): LibraryRow[] {
  return getDb().prepare("SELECT * FROM reference_libraries ORDER BY created_at DESC").all() as unknown as LibraryRow[];
}

export function getLibrary(id: string): LibraryRow | null {
  return (getDb().prepare("SELECT * FROM reference_libraries WHERE id = ?").get(id) as LibraryRow | undefined) ?? null;
}

export function insertLibrary(input: { name: string; description: string; versionLabel: string; mistralLibraryId: string | null }): LibraryRow {
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO reference_libraries (id, mistral_library_id, name, description, version_label, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, 0, ?)`).run(id, input.mistralLibraryId, input.name, input.description, input.versionLabel, now());
  return getLibrary(id)!;
}

export function activateLibrary(id: string): void {
  const database = getDb();
  database.exec("BEGIN");
  try {
    database.prepare("UPDATE reference_libraries SET is_active = 0").run();
    database.prepare("UPDATE reference_libraries SET is_active = 1 WHERE id = ?").run(id);
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
}

export function deleteLibraryRow(id: string): void {
  const database = getDb();
  database.prepare("DELETE FROM reference_documents WHERE library_id = ?").run(id);
  database.prepare("DELETE FROM reference_libraries WHERE id = ?").run(id);
}

export function listLibraryDocuments(libraryId: string): LibraryDocumentRow[] {
  return getDb().prepare("SELECT * FROM reference_documents WHERE library_id = ? ORDER BY created_at").all(libraryId) as unknown as LibraryDocumentRow[];
}

export function insertLibraryDocument(input: { libraryId: string; name: string; status: string; mistralFileId: string | null; mistralDocumentId: string | null }): LibraryDocumentRow {
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO reference_documents (id, library_id, mistral_file_id, mistral_document_id, name, status, page_count, summary, error, created_at)
    VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?)`).run(id, input.libraryId, input.mistralFileId, input.mistralDocumentId, input.name, input.status, now());
  return getDb().prepare("SELECT * FROM reference_documents WHERE id = ?").get(id) as unknown as LibraryDocumentRow;
}

export function updateLibraryDocument(id: string, patch: Partial<Pick<LibraryDocumentRow, "status" | "page_count" | "summary" | "error" | "mistral_document_id" | "mistral_file_id">>): void {
  const current = getDb().prepare("SELECT * FROM reference_documents WHERE id = ?").get(id) as unknown as LibraryDocumentRow | undefined;
  if (!current) return;
  getDb().prepare(`UPDATE reference_documents SET status = ?, page_count = ?, summary = ?, error = ?, mistral_document_id = ?, mistral_file_id = ? WHERE id = ?`).run(
    patch.status ?? current.status,
    patch.page_count === undefined ? current.page_count : patch.page_count,
    patch.summary === undefined ? current.summary : patch.summary,
    patch.error === undefined ? current.error : patch.error,
    patch.mistral_document_id === undefined ? current.mistral_document_id : patch.mistral_document_id,
    patch.mistral_file_id === undefined ? current.mistral_file_id : patch.mistral_file_id,
    id,
  );
}

export function getLibraryDocument(id: string): LibraryDocumentRow | null {
  return (getDb().prepare("SELECT * FROM reference_documents WHERE id = ?").get(id) as unknown as LibraryDocumentRow | undefined) ?? null;
}

export function deleteLibraryDocumentRow(id: string): void {
  getDb().prepare("DELETE FROM reference_documents WHERE id = ?").run(id);
}

export function listJahrespakete(): JahrespaketRow[] {
  return getDb().prepare("SELECT * FROM jahrespakete ORDER BY jahr DESC, version DESC").all() as unknown as JahrespaketRow[];
}

export function legeJahrespaketEntwurfAn(input: { jahr: number; methodologyVersion: string; rulesStamp: string }): JahrespaketRow {
  if (!Number.isSafeInteger(input.jahr) || input.jahr < 1900 || input.jahr > 2200) {
    throw new Error("Das Paketjahr ist ungültig.");
  }
  const methodologyVersion = input.methodologyVersion.trim();
  const rulesStamp = input.rulesStamp.trim();
  if (!methodologyVersion || !rulesStamp) throw new Error("Methodikversion und Regelstand werden benötigt.");
  const database = getDb();
  const id = crypto.randomUUID();
  database.exec("BEGIN IMMEDIATE");
  try {
    const row = database.prepare("SELECT MAX(version) AS version FROM jahrespakete WHERE jahr = ?").get(input.jahr) as { version: number | null };
    const version = (row.version ?? 0) + 1;
    database.prepare(`INSERT INTO jahrespakete (
        id, jahr, version, status, methodology_version, rules_stamp, content_hash,
        pruefer_name, freigabe_kommentar, freigegeben_am, is_active, created_at
      ) VALUES (?, ?, ?, 'entwurf', ?, ?, NULL, NULL, NULL, NULL, 0, ?)`).run(
      id,
      input.jahr,
      version,
      methodologyVersion,
      rulesStamp,
      now(),
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return database.prepare("SELECT * FROM jahrespakete WHERE id = ?").get(id) as unknown as JahrespaketRow;
}

export function deleteCaseFully(caseId: string, removeFile: (key: string) => Promise<void>): Promise<void> {
  const documents = listDocuments(caseId);
  const database = getDb();
  const runIds = (database.prepare("SELECT id FROM runs WHERE case_id = ?").all(caseId) as unknown as Array<{ id: string }>).map((row) => row.id);
  database.exec("BEGIN");
  try {
    database.prepare("DELETE FROM chat_messages WHERE case_id = ?").run(caseId);
    database.prepare("DELETE FROM reports WHERE case_id = ?").run(caseId);
    for (const runId of runIds) {
      database.prepare("DELETE FROM stage_artifacts WHERE run_id = ?").run(runId);
      database.prepare("DELETE FROM jobs WHERE payload_json LIKE ?").run(`%${runId}%`);
    }
    database.prepare("DELETE FROM runs WHERE case_id = ?").run(caseId);
    database.prepare("DELETE FROM documents WHERE case_id = ?").run(caseId);
    database.prepare("DELETE FROM cases WHERE id = ?").run(caseId);
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return Promise.all(documents.map((document) => removeFile(document.storage_key))).then(() => undefined);
}
