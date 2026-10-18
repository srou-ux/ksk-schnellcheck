import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { dataDir } from "@/lib/config";
import { getDb, type JahrespaketRow } from "@/lib/db";

export type ArchivQuelle = {
  id: string;
  dateipfad: string;
  sha256: string;
  herkunft: string;
  dokumentstand: string;
  abrufdatum: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type PaketBibliothek = {
  id: string;
  jahrespaket_id: string;
  mistral_library_id: string;
  remote_manifest_hash: string | null;
  remote_checked_at: string | null;
  blockiert_grund: string | null;
  created_at: string;
};

export type PaketQuelleStatus = {
  paketQuelleId: string;
  paketId: string;
  jahr: number;
  paketVersion: number;
  archivQuelleId: string;
  originalName: string;
  archivstatus: "vorhanden" | "fehlt" | "hash_abweichung";
  uploadstatus: string;
  verarbeitungsstatus: string;
  ragPruefergebnis: "bestanden" | "fehlgeschlagen" | "ausstehend" | "veraltet";
  fehler: string[];
  mistralLibraryId: string | null;
  mistralDocumentId: string | null;
};

type ZuordnungRow = {
  id: string;
  jahrespaket_quelle_id: string;
  mistral_library_id: string;
  mistral_document_id: string | null;
  upload_status: string;
  verarbeitungsstatus: string;
  mistral_document_hash: string | null;
  fehler: string | null;
  created_at: string;
  updated_at: string;
};

type ManifestDokument = {
  paketQuelleId: string;
  archivQuelleId: string;
  archivSha256: string;
  zuordnungId: string;
  mistralDocumentId: string;
  mistralDocumentHash: string | null;
};

type ManifestRow = {
  id: string;
  jahrespaket_id: string;
  mistral_library_id: string;
  manifest_hash: string;
  dokumente_json: string;
  created_at: string;
  invalidated_at: string | null;
  invalidated_reason: string | null;
};

const DOKUMENTSTAND = /^\d{4}(?:-\d{2}(?:-\d{2})?)?$/;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function now(): string {
  return new Date().toISOString();
}

function sha256(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
}

function paket(id: string): JahrespaketRow {
  const row = getDb().prepare("SELECT * FROM jahrespakete WHERE id = ?").get(id) as unknown as JahrespaketRow | undefined;
  if (!row) throw new Error("Die Jahrespaketversion existiert nicht.");
  return row;
}

function assertPaketSchreibbar(id: string): JahrespaketRow {
  const row = paket(id);
  if (row.status === "freigegeben") throw new Error("Freigegebene Paketquellen sind unveränderlich.");
  return row;
}

function bibliothek(paketId: string): PaketBibliothek {
  const row = getDb().prepare("SELECT * FROM jahrespaket_bibliotheken WHERE jahrespaket_id = ?").get(paketId) as unknown as PaketBibliothek | undefined;
  if (!row) throw new Error("Der Paketversion ist keine Mistral-Library zugeordnet.");
  return row;
}

function paketIdFuerQuelle(paketQuelleId: string): string {
  const row = getDb().prepare("SELECT jahrespaket_id FROM jahrespaket_quellen WHERE id = ?").get(paketQuelleId) as { jahrespaket_id: string } | undefined;
  if (!row) throw new Error("Die Paketquelle existiert nicht.");
  return row.jahrespaket_id;
}

function invalidiereManifeste(paketId: string, grund: string): void {
  getDb().prepare(`UPDATE jahrespaket_indexmanifeste
    SET invalidated_at = ?, invalidated_reason = ?
    WHERE jahrespaket_id = ? AND invalidated_at IS NULL`).run(now(), grund, paketId);
}

export function archiviereOriginal(input: {
  bytes: Uint8Array;
  originalName: string;
  mimeType: string;
  herkunft: string;
  dokumentstand: string;
  abrufdatum: string;
  genauigkeit?: "tag" | "monat" | "jahr" | "unbekannt";
}): ArchivQuelle {
  if (input.bytes.byteLength === 0) throw new Error("Das Originaldokument ist leer.");
  if (!input.originalName.trim() || !input.mimeType.trim() || !input.herkunft.trim()) throw new Error("Name, MIME-Typ und Herkunft werden benötigt.");
  if (!DOKUMENTSTAND.test(input.dokumentstand) || !ISO_DATE.test(input.abrufdatum)) throw new Error("Dokumentstand muss YYYY, YYYY-MM oder YYYY-MM-DD und Abrufdatum ein ISO-Datum sein.");
  const genauigkeit = input.genauigkeit ?? (input.dokumentstand.length === 4 ? "jahr" : input.dokumentstand.length === 7 ? "monat" : "tag");
  const hash = sha256(input.bytes);
  const existing = getDb().prepare("SELECT * FROM archiv_quellen WHERE sha256 = ? ORDER BY created_at LIMIT 1").get(hash) as unknown as ArchivQuelle | undefined;
  if (existing) {
    const existingPath = path.join(dataDir(), existing.dateipfad);
    if (!existsSync(existingPath) || sha256(readFileSync(existingPath)) !== hash) throw new Error("Das vorhandene Archivobjekt stimmt nicht mit seinem Hash überein.");
    return existing;
  }
  const relative = path.join("archive", "rechtsquellen", hash.slice(0, 2), hash);
  const absolute = path.join(dataDir(), relative);
  mkdirSync(path.dirname(absolute), { recursive: true });
  if (existsSync(absolute)) {
    if (sha256(readFileSync(absolute)) !== hash) throw new Error("Das vorhandene Archivobjekt stimmt nicht mit seinem Hash überein.");
  } else {
    writeFileSync(absolute, input.bytes, { flag: "wx" });
  }
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO archiv_quellen (
      id, dateipfad, sha256, herkunft, dokumentstand, abrufdatum, original_name, mime_type, size_bytes, created_at, dokumentstand_genauigkeit
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
    id, relative, hash, input.herkunft.trim(), input.dokumentstand, input.abrufdatum,
    input.originalName.trim(), input.mimeType.trim(), input.bytes.byteLength, now(), genauigkeit,
  );
  return getDb().prepare("SELECT * FROM archiv_quellen WHERE id = ?").get(id) as unknown as ArchivQuelle;
}

export function ordnePaketBibliothekZu(paketId: string, mistralLibraryId: string): PaketBibliothek {
  assertPaketSchreibbar(paketId);
  const libraryId = mistralLibraryId.trim();
  if (!libraryId) throw new Error("Die Mistral-Library-ID fehlt.");
  const existing = getDb().prepare("SELECT * FROM jahrespaket_bibliotheken WHERE jahrespaket_id = ?").get(paketId) as unknown as PaketBibliothek | undefined;
  if (existing) {
    if (existing.mistral_library_id !== libraryId) throw new Error("Die Paketversion besitzt bereits eine andere Mistral-Library.");
    return existing;
  }
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO jahrespaket_bibliotheken (
      id, jahrespaket_id, mistral_library_id, remote_manifest_hash, remote_checked_at, blockiert_grund, created_at
    ) VALUES (?, ?, ?, NULL, NULL, NULL, ?)`).run(id, paketId, libraryId, now());
  return bibliothek(paketId);
}

export function ordneArchivquelleZu(paketId: string, archivQuelleId: string): string {
  assertPaketSchreibbar(paketId);
  const source = getDb().prepare("SELECT id FROM archiv_quellen WHERE id = ?").get(archivQuelleId);
  if (!source) throw new Error("Die Archivquelle existiert nicht.");
  const existing = getDb().prepare("SELECT id FROM jahrespaket_quellen WHERE jahrespaket_id = ? AND archiv_quelle_id = ?").get(paketId, archivQuelleId) as { id: string } | undefined;
  if (existing) return existing.id;
  const id = crypto.randomUUID();
  getDb().prepare("INSERT INTO jahrespaket_quellen (id, jahrespaket_id, archiv_quelle_id, created_at) VALUES (?, ?, ?, ?)")
    .run(id, paketId, archivQuelleId, now());
  invalidiereManifeste(paketId, "Der Quellenbestand wurde geändert.");
  return id;
}

export function protokolliereMistralUpload(input: {
  paketQuelleId: string;
  mistralLibraryId: string;
  mistralDocumentId: string | null;
  uploadStatus: "hochgeladen" | "fehlgeschlagen";
  verarbeitungsstatus: string;
  mistralDocumentHash?: string | null;
  fehler?: string | null;
}): ZuordnungRow {
  const paketId = paketIdFuerQuelle(input.paketQuelleId);
  assertPaketSchreibbar(paketId);
  const library = bibliothek(paketId);
  if (library.mistral_library_id !== input.mistralLibraryId) throw new Error("Die Dokumentzuordnung gehört nicht zur Library dieser Paketversion.");
  if (input.uploadStatus === "hochgeladen" && !input.mistralDocumentId?.trim()) throw new Error("Ein erfolgreicher Upload benötigt eine Mistral-Dokument-ID.");
  const id = crypto.randomUUID();
  const stamp = now();
  getDb().prepare(`INSERT INTO jahrespaket_mistral_zuordnungen (
      id, jahrespaket_quelle_id, mistral_library_id, mistral_document_id, upload_status,
      verarbeitungsstatus, mistral_document_hash, fehler, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
    id, input.paketQuelleId, input.mistralLibraryId, input.mistralDocumentId?.trim() || null,
    input.uploadStatus, input.verarbeitungsstatus, input.mistralDocumentHash ?? null, input.fehler?.trim() || null, stamp, stamp,
  );
  invalidiereManifeste(paketId, "Eine Mistral-Dokumentzuordnung wurde hinzugefügt.");
  return getDb().prepare("SELECT * FROM jahrespaket_mistral_zuordnungen WHERE id = ?").get(id) as unknown as ZuordnungRow;
}

export function aktualisiereVerarbeitungsstatus(input: { zuordnungId: string; status: string; fehler?: string | null; mistralDocumentHash?: string | null }): void {
  const row = getDb().prepare(`SELECT z.*, q.jahrespaket_id FROM jahrespaket_mistral_zuordnungen z
    JOIN jahrespaket_quellen q ON q.id = z.jahrespaket_quelle_id WHERE z.id = ?`).get(input.zuordnungId) as (ZuordnungRow & { jahrespaket_id: string }) | undefined;
  if (!row) throw new Error("Die Mistral-Zuordnung existiert nicht.");
  assertPaketSchreibbar(row.jahrespaket_id);
  getDb().prepare(`UPDATE jahrespaket_mistral_zuordnungen
    SET verarbeitungsstatus = ?, fehler = ?, mistral_document_hash = ?, updated_at = ? WHERE id = ?`).run(
    input.status, input.fehler?.trim() || null, input.mistralDocumentHash ?? row.mistral_document_hash, now(), row.id,
  );
  invalidiereManifeste(row.jahrespaket_id, "Der Verarbeitungsstatus einer Dokumentzuordnung wurde geändert.");
}

function aktuelleZuordnungen(paketId: string): Array<ManifestDokument & { status: string; fehler: string | null }> {
  return getDb().prepare(`SELECT
      q.id AS paketQuelleId, q.archiv_quelle_id AS archivQuelleId, a.sha256 AS archivSha256,
      z.id AS zuordnungId, z.mistral_document_id AS mistralDocumentId,
      z.mistral_document_hash AS mistralDocumentHash, z.verarbeitungsstatus AS status, z.fehler AS fehler
    FROM jahrespaket_quellen q
    JOIN archiv_quellen a ON a.id = q.archiv_quelle_id
    LEFT JOIN jahrespaket_mistral_zuordnungen z ON z.id = (
      SELECT z2.id FROM jahrespaket_mistral_zuordnungen z2
      WHERE z2.jahrespaket_quelle_id = q.id ORDER BY z2.created_at DESC, z2.rowid DESC LIMIT 1
    )
    WHERE q.jahrespaket_id = ? ORDER BY q.id`).all(paketId) as unknown as Array<ManifestDokument & { status: string; fehler: string | null }>;
}

export function erzeugeIndexmanifest(paketId: string): ManifestRow {
  assertPaketSchreibbar(paketId);
  const library = bibliothek(paketId);
  const rows = aktuelleZuordnungen(paketId);
  if (rows.length === 0) throw new Error("Das Paket besitzt keine Quellen.");
  const incomplete = rows.find((row) => !row.zuordnungId || !row.mistralDocumentId || !["completed", "complete", "done"].includes(String(row.status).toLowerCase()));
  if (incomplete) throw new Error(`Die Quelle ${incomplete.archivQuelleId} ist nicht vollständig verarbeitet.`);
  const documents: ManifestDokument[] = rows.map((row) => ({
    paketQuelleId: row.paketQuelleId,
    archivQuelleId: row.archivQuelleId,
    archivSha256: row.archivSha256,
    zuordnungId: row.zuordnungId,
    mistralDocumentId: row.mistralDocumentId,
    mistralDocumentHash: row.mistralDocumentHash,
  }));
  const json = JSON.stringify(documents);
  const manifestHash = sha256(`${library.mistral_library_id}\n${json}`);
  invalidiereManifeste(paketId, "Ein neuer Indexbestand wurde manifestiert.");
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO jahrespaket_indexmanifeste (
      id, jahrespaket_id, mistral_library_id, manifest_hash, dokumente_json, created_at, invalidated_at, invalidated_reason
    ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)`).run(id, paketId, library.mistral_library_id, manifestHash, json, now());
  return getDb().prepare("SELECT * FROM jahrespaket_indexmanifeste WHERE id = ?").get(id) as unknown as ManifestRow;
}

export function protokolliereRagPruefung(input: {
  manifestId: string;
  paketQuelleId?: string | null;
  art: "positiv" | "trennung";
  modell: string;
  testfrage: string;
  erwarteteDokumentIds: string[];
  referenzierteDokumentIds: string[];
  anbieterBestanden: boolean;
  ergebnis: unknown;
  fehler?: string | null;
}): { id: string; bestanden: boolean; fehler: string | null } {
  const manifest = getDb().prepare("SELECT * FROM jahrespaket_indexmanifeste WHERE id = ?").get(input.manifestId) as unknown as ManifestRow | undefined;
  if (!manifest) throw new Error("Das Indexmanifest existiert nicht.");
  const manifestIds = new Set((JSON.parse(manifest.dokumente_json) as ManifestDokument[]).map((item) => item.mistralDocumentId));
  const unknown = input.referenzierteDokumentIds.filter((id) => !manifestIds.has(id));
  const expectedMissing = input.erwarteteDokumentIds.filter((id) => !input.referenzierteDokumentIds.includes(id));
  const structuralOk = input.art === "positiv" ? unknown.length === 0 && expectedMissing.length === 0 : input.referenzierteDokumentIds.length === 0;
  const current = manifest.invalidated_at === null;
  const bestanden = input.anbieterBestanden && structuralOk && current;
  const errors = [
    manifest.invalidated_at ? "Das Indexmanifest ist veraltet." : null,
    unknown.length ? `Unbekannte Dokumentreferenzen: ${unknown.join(", ")}` : null,
    input.art === "positiv" && expectedMissing.length ? `Erwartete Dokumentreferenzen fehlen: ${expectedMissing.join(", ")}` : null,
    input.art === "trennung" && input.referenzierteDokumentIds.length ? "Die Trennungsprüfung hat fremde Dokumente referenziert." : null,
    input.fehler?.trim() || null,
  ].filter((value): value is string => Boolean(value));
  const id = crypto.randomUUID();
  getDb().prepare(`INSERT INTO jahrespaket_rag_pruefungen (
      id, jahrespaket_id, indexmanifest_id, jahrespaket_quelle_id, art, modell, testfrage,
      erwartete_dokument_ids_json, referenzierte_dokument_ids_json, bestanden, ergebnis_json, fehler, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`).run(
    id, manifest.jahrespaket_id, manifest.id, input.paketQuelleId ?? null, input.art, input.modell.trim(), input.testfrage.trim(),
    JSON.stringify(input.erwarteteDokumentIds), JSON.stringify(input.referenzierteDokumentIds), bestanden ? 1 : 0,
    JSON.stringify(input.ergebnis), errors.join(" ") || null, now(),
  );
  return { id, bestanden, fehler: errors.join(" ") || null };
}

export function pruefeExternenIndex(paketId: string, remote: Array<{ documentId: string; hash?: string | null }>): { identisch: boolean; grund: string | null } {
  const library = bibliothek(paketId);
  const manifest = getDb().prepare(`SELECT * FROM jahrespaket_indexmanifeste
    WHERE jahrespaket_id = ? AND invalidated_at IS NULL ORDER BY created_at DESC, rowid DESC LIMIT 1`).get(paketId) as unknown as ManifestRow | undefined;
  const expected = manifest ? (JSON.parse(manifest.dokumente_json) as ManifestDokument[])
    .map((item) => ({ documentId: item.mistralDocumentId, hash: item.mistralDocumentHash ?? null })) : [];
  const normalize = (items: Array<{ documentId: string; hash?: string | null }>) => JSON.stringify(items
    .map((item) => ({ documentId: item.documentId, hash: item.hash ?? null })).sort((a, b) => a.documentId.localeCompare(b.documentId)));
  const remoteHash = sha256(normalize(remote));
  const identical = Boolean(manifest) && normalize(expected) === normalize(remote);
  const reason = identical ? null : "Der aktuelle Mistral-Dokumentbestand weicht vom Indexmanifest ab.";
  const stamp = now();
  getDb().prepare(`UPDATE jahrespaket_bibliotheken
    SET remote_manifest_hash = ?, remote_checked_at = ?, blockiert_grund = ? WHERE id = ?`).run(remoteHash, stamp, reason, library.id);
  if (!identical && manifest) invalidiereManifeste(paketId, reason!);
  return { identisch: identical, grund: reason };
}

function archivstatus(source: ArchivQuelle): PaketQuelleStatus["archivstatus"] {
  const absolute = path.join(dataDir(), source.dateipfad);
  if (!existsSync(absolute)) return "fehlt";
  return sha256(readFileSync(absolute)) === source.sha256 ? "vorhanden" : "hash_abweichung";
}

export function listPaketQuellenStatus(): PaketQuelleStatus[] {
  const rows = getDb().prepare(`SELECT q.id AS paket_quelle_id, q.jahrespaket_id, p.jahr, p.version,
      a.*, b.mistral_library_id, b.blockiert_grund
    FROM jahrespaket_quellen q
    JOIN jahrespakete p ON p.id = q.jahrespaket_id
    JOIN archiv_quellen a ON a.id = q.archiv_quelle_id
    LEFT JOIN jahrespaket_bibliotheken b ON b.jahrespaket_id = p.id
    ORDER BY p.jahr DESC, p.version DESC, a.original_name`).all() as unknown as Array<ArchivQuelle & {
      paket_quelle_id: string; jahrespaket_id: string; jahr: number; version: number;
      mistral_library_id: string | null; blockiert_grund: string | null;
    }>;
  return rows.map((row) => {
    const mapping = getDb().prepare(`SELECT * FROM jahrespaket_mistral_zuordnungen
      WHERE jahrespaket_quelle_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1`).get(row.paket_quelle_id) as unknown as ZuordnungRow | undefined;
    const manifest = getDb().prepare(`SELECT * FROM jahrespaket_indexmanifeste
      WHERE jahrespaket_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1`).get(row.jahrespaket_id) as unknown as ManifestRow | undefined;
    const checks = manifest ? getDb().prepare(`SELECT art, bestanden, fehler FROM jahrespaket_rag_pruefungen
      WHERE indexmanifest_id = ? AND (art != 'positiv' OR jahrespaket_quelle_id = ?)
      ORDER BY created_at DESC, rowid DESC`).all(manifest.id, row.paket_quelle_id) as Array<{ art: string; bestanden: number; fehler: string | null }> : [];
    const positive = checks.find((item) => item.art === "positiv");
    const separation = checks.find((item) => item.art === "trennung");
    const errors = [mapping?.fehler, row.blockiert_grund, positive?.fehler, separation?.fehler].filter((value): value is string => Boolean(value));
    let rag: PaketQuelleStatus["ragPruefergebnis"] = "ausstehend";
    if (manifest?.invalidated_at) rag = "veraltet";
    else if (positive && separation) rag = positive.bestanden && separation.bestanden ? "bestanden" : "fehlgeschlagen";
    return {
      paketQuelleId: row.paket_quelle_id,
      paketId: row.jahrespaket_id,
      jahr: row.jahr,
      paketVersion: row.version,
      archivQuelleId: row.id,
      originalName: row.original_name,
      archivstatus: archivstatus(row),
      uploadstatus: mapping?.upload_status ?? "nicht hochgeladen",
      verarbeitungsstatus: mapping?.verarbeitungsstatus ?? "ausstehend",
      ragPruefergebnis: rag,
      fehler: errors,
      mistralLibraryId: row.mistral_library_id,
      mistralDocumentId: mapping?.mistral_document_id ?? null,
    };
  });
}
