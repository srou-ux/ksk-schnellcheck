import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createCase, getCase, getDb, legeJahrespaketEntwurfAn } from "../src/lib/db";
import {
  aktualisiereVerarbeitungsstatus,
  archiviereOriginal,
  erzeugeIndexmanifest,
  listPaketQuellenStatus,
  ordneArchivquelleZu,
  ordnePaketBibliothekZu,
  protokolliereMistralUpload,
  protokolliereRagPruefung,
  pruefeExternenIndex,
} from "../src/lib/paket-quellen";
import { dataDir } from "../src/lib/config";

function setup(jahr: number) {
  const paket = legeJahrespaketEntwurfAn({ jahr, methodologyVersion: "v12", rulesStamp: `${jahr - 1}-10-01` });
  const library = ordnePaketBibliothekZu(paket.id, `lib-${jahr}-${crypto.randomUUID()}`);
  const archiv = archiviereOriginal({
    bytes: new TextEncoder().encode(`Amtlicher fiktiver Testinhalt ${jahr}`),
    originalName: `quelle-${jahr}.txt`,
    mimeType: "text/plain",
    herkunft: "https://example.invalid/amtlich",
    dokumentstand: `${jahr - 1}-09-01`,
    abrufdatum: `${jahr - 1}-10-01`,
  });
  const paketQuelleId = ordneArchivquelleZu(paket.id, archiv.id);
  return { paket, library, archiv, paketQuelleId };
}

describe("Paketquellen und RAG-Nachweise", () => {
  it("trennt Archividentität, Paketzuordnung und erneute Mistral-Uploads", () => {
    const { library, archiv, paketQuelleId } = setup(2051);
    const first = protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2051-a",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    });
    const second = protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2051-b",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    });

    expect(first.id).not.toBe(second.id);
    expect(first.mistral_document_id).not.toBe(second.mistral_document_id);
    const stored = getDb().prepare("SELECT * FROM archiv_quellen WHERE id = ?").get(archiv.id) as { id: string; sha256: string; dateipfad: string };
    expect(stored.id).toBe(archiv.id);
    expect(stored.sha256).toBe(archiv.sha256);
    expect(readFileSync(path.join(dataDir(), stored.dateipfad))).toEqual(Buffer.from(`Amtlicher fiktiver Testinhalt 2051`));
  });

  it("protokolliert fehlgeschlagene Verarbeitung und verhindert ein Indexmanifest", () => {
    const { paket, library, paketQuelleId } = setup(2052);
    const upload = protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2052",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Running",
    });
    aktualisiereVerarbeitungsstatus({ zuordnungId: upload.id, status: "error", fehler: "Indexierung fehlgeschlagen." });

    expect(() => erzeugeIndexmanifest(paket.id)).toThrow(/nicht vollständig verarbeitet/);
    expect(listPaketQuellenStatus().find((item) => item.paketQuelleId === paketQuelleId)).toMatchObject({
      uploadstatus: "hochgeladen",
      verarbeitungsstatus: "error",
      ragPruefergebnis: "ausstehend",
      fehler: ["Indexierung fehlgeschlagen."],
    });
  });

  it("weist unbekannte Dokumentreferenzen als fehlgeschlagen aus", () => {
    const { paket, library, paketQuelleId } = setup(2053);
    protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2053",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    });
    const manifest = erzeugeIndexmanifest(paket.id);
    const check = protokolliereRagPruefung({
      manifestId: manifest.id,
      paketQuelleId,
      art: "positiv",
      modell: "mistral-test",
      testfrage: "Testfrage",
      erwarteteDokumentIds: ["doc-2053"],
      referenzierteDokumentIds: ["doc-fremd"],
      anbieterBestanden: true,
      ergebnis: { marker: true },
    });
    expect(check.bestanden).toBe(false);
    expect(check.fehler).toMatch(/Unbekannte Dokumentreferenzen/);
    expect(check.fehler).toMatch(/Erwartete Dokumentreferenzen fehlen/);
  });

  it("macht RAG-Nachweise nach einem erneuten Upload ungültig", () => {
    const { paket, library, paketQuelleId } = setup(2054);
    protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2054-a",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    });
    const manifest = erzeugeIndexmanifest(paket.id);
    expect(protokolliereRagPruefung({
      manifestId: manifest.id, paketQuelleId, art: "positiv", modell: "mistral-test", testfrage: "Marker?",
      erwarteteDokumentIds: ["doc-2054-a"], referenzierteDokumentIds: ["doc-2054-a"], anbieterBestanden: true, ergebnis: {},
    }).bestanden).toBe(true);

    protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2054-b",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    });
    const stale = protokolliereRagPruefung({
      manifestId: manifest.id, paketQuelleId, art: "positiv", modell: "mistral-test", testfrage: "Marker?",
      erwarteteDokumentIds: ["doc-2054-a"], referenzierteDokumentIds: ["doc-2054-a"], anbieterBestanden: true, ergebnis: {},
    });
    expect(stale.bestanden).toBe(false);
    expect(stale.fehler).toMatch(/veraltet/);
    expect(listPaketQuellenStatus().find((item) => item.paketQuelleId === paketQuelleId)?.ragPruefergebnis).toBe("veraltet");
  });

  it("erkennt externe Abweichungen und sperrt Änderungen an freigegebenen Paketquellen", () => {
    const { paket, library, paketQuelleId } = setup(2055);
    protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-2055",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed", mistralDocumentHash: "remote-hash",
    });
    erzeugeIndexmanifest(paket.id);
    expect(pruefeExternenIndex(paket.id, [{ documentId: "doc-2055", hash: "remote-hash" }]).identisch).toBe(true);
    expect(pruefeExternenIndex(paket.id, [{ documentId: "doc-unbekannt", hash: "x" }])).toMatchObject({ identisch: false });
    expect(listPaketQuellenStatus().find((item) => item.paketQuelleId === paketQuelleId)?.fehler.join(" ")).toMatch(/weicht/);

    getDb().prepare("UPDATE jahrespakete SET status = 'freigegeben' WHERE id = ?").run(paket.id);
    expect(() => protokolliereMistralUpload({
      paketQuelleId, mistralLibraryId: library.mistral_library_id, mistralDocumentId: "doc-neu",
      uploadStatus: "hochgeladen", verarbeitungsstatus: "Completed",
    })).toThrow(/unveränderlich/);
    expect(() => getDb().prepare("DELETE FROM jahrespaket_quellen WHERE id = ?").run(paketQuelleId)).toThrow(/unveränderlich/);
  });

  it("lässt bestehende Falldaten durch die Migration und Quellenanlage unverändert", () => {
    const fall = createCase({ title: "Unveränderter Altfall", audience: "verein" });
    setup(2056);
    expect(getCase(fall.id)).toEqual(fall);
  });
});
