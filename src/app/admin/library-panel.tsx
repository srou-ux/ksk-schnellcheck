"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type DocumentRow = {
  id: string;
  name: string;
  pageCount: number | null;
  summary: string | null;
  status: "Running" | "Completed" | "Fehler";
};

type Library = {
  id: string;
  name: string;
  description: string | null;
  documents: DocumentRow[];
};

export function LibraryPanel() {
  const [library, setLibrary] = useState<Library | null>(null);
  const [description, setDescription] = useState("Referenzkorpus für die KSK-Prüfung");
  const [error, setError] = useState<string | null>(null);
  const [keyLabel, setKeyLabel] = useState<string>("");
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<{ kind: "library" } | { kind: "document"; id: string; name: string } | null>(null);

  const load = useCallback(async () => {
    const response = await fetch("/api/mistral-test/library");
    const body = await response.json();
    if (!response.ok) {
      setError(body.error ?? "Die Library konnte nicht geladen werden.");
      setLibrary(null);
      return;
    }
    setError(null);
    setLibrary(body.library ?? null);
  }, []);

  const checkKey = useCallback(async () => {
    const response = await fetch("/api/mistral-test/key");
    const body = await response.json();
    const connected = body.status === "verbunden";
    setKeyLabel(connected ? "verbunden" : "nicht verbunden");
    if (connected) setError(null);
    else if (body.error) setError(body.error);
  }, []);

  useEffect(() => {
    void checkKey();
    void load();
  }, [checkKey, load]);

  useEffect(() => {
    if (!library?.documents.some((document) => document.status === "Running")) return;
    const timer = window.setInterval(() => void load(), 3000);
    return () => window.clearInterval(timer);
  }, [library, load]);

  async function create() {
    setBusy(true);
    setError(null);
    const response = await fetch("/api/mistral-test/library", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description }),
    });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) {
      setError(body.error ?? "Die Library konnte nicht angelegt werden.");
      return;
    }
    setLibrary(body.library ?? null);
  }

  async function upload(files: FileList | File[]) {
    const list = [...files];
    if (list.length === 0) return;
    setBusy(true);
    setError(null);
    const form = new FormData();
    for (const file of list) form.append("files", file);
    const response = await fetch("/api/mistral-test/documents", { method: "POST", body: form });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) setError(body.error ?? "Upload fehlgeschlagen, weil Mistral die Datei nicht angenommen hat.");
    else if (Array.isArray(body.errors) && body.errors.length > 0) setError(body.errors.join(" "));
    await load();
  }

  async function confirmDelete() {
    if (!confirm) return;
    setBusy(true);
    setError(null);
    const response = await fetch(
      confirm.kind === "library" ? "/api/mistral-test/library" : `/api/mistral-test/documents/${confirm.id}`,
      { method: "DELETE" },
    );
    const body = await response.json();
    setBusy(false);
    setConfirm(null);
    if (!response.ok) {
      setError(body.error ?? "Löschen ist fehlgeschlagen.");
      return;
    }
    await load();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl">KSK-Referenzen</h1>
        <div className="flex flex-wrap gap-3 text-sm">
          <button type="button" onClick={() => void checkKey()} className="rounded-md border border-line px-3 py-2">Schlüssel prüfen</button>
          <Link href="/admin/test" className="rounded-md border border-line px-3 py-2">RAG-Test</Link>
        </div>
      </div>
      {keyLabel === "verbunden" ? (
        <p className="rounded-md bg-emerald-50 px-4 py-3 text-base font-semibold text-ok">Die Verbindung steht.</p>
      ) : keyLabel ? (
        <p className="text-sm font-semibold text-unclear">nicht verbunden</p>
      ) : (
        <p className="text-sm text-ink/70">Die Verbindung wird geprüft.</p>
      )}
      {error ? <p className="text-sm text-danger">{error}</p> : null}

      {library ? (
        <section className="space-y-4 rounded-xl border border-line bg-card p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-2xl">{library.name}</h2>
              {library.description ? <p className="text-sm text-ink/70">{library.description}</p> : null}
            </div>
            <button type="button" onClick={() => setConfirm({ kind: "library" })} className="text-sm text-danger">Library löschen</button>
          </div>
          <div
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              void upload(event.dataTransfer.files);
            }}
            className={`rounded-lg border border-dashed px-4 py-8 text-center text-sm ${dragging ? "border-stamp bg-emerald-50" : "border-line"}`}
          >
            <p>Dateien hier ablegen. Mehrfachauswahl ist möglich. Gespeichert wird nur bei Mistral.</p>
            <label className="mt-3 inline-block cursor-pointer rounded-md bg-stamp px-4 py-2 text-white">
              Dateien wählen
              <input
                type="file"
                multiple
                className="sr-only"
                onChange={(event) => {
                  if (event.target.files) void upload(event.target.files);
                  event.target.value = "";
                }}
              />
            </label>
          </div>
          <ul className="space-y-3">
            {library.documents.length === 0 ? <li className="text-sm text-ink/70">Noch keine Dokumente.</li> : null}
            {library.documents.map((document) => (
              <li key={document.id} className="rounded-md border border-line px-3 py-2 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold">{document.name}</span>
                  <span className={document.status === "Completed" ? "text-ok" : document.status === "Fehler" ? "text-danger" : "text-unclear"}>{document.status}</span>
                </div>
                <p className="text-ink/70">Seiten: {document.pageCount ?? "—"}</p>
                {document.summary ? <p className="mt-1 text-ink/80">{document.summary}</p> : null}
                <button type="button" onClick={() => setConfirm({ kind: "document", id: document.id, name: document.name })} className="mt-2 text-danger">Dokument löschen</button>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void create();
          }}
          className="space-y-3 rounded-xl border border-line bg-card p-4"
        >
          <label className="block text-sm">
            Name
            <input value="KSK-Referenzen" readOnly className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
          </label>
          <label className="block text-sm">
            Beschreibung
            <input value={description} onChange={(event) => setDescription(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
          </label>
          <button disabled={busy} className="rounded-md bg-stamp px-4 py-2 text-white">Library anlegen</button>
        </form>
      )}

      {confirm ? (
        <div className="rounded-xl border border-danger/40 bg-card p-4">
          <p>
            {confirm.kind === "library"
              ? "Die Library KSK-Referenzen und alle Dokumente darin bei Mistral löschen?"
              : `Das Dokument „${confirm.name}“ bei Mistral löschen?`}
          </p>
          <div className="mt-3 flex gap-3">
            <button type="button" disabled={busy} onClick={() => void confirmDelete()} className="rounded-md bg-danger px-4 py-2 text-white">Löschen</button>
            <button type="button" onClick={() => setConfirm(null)} className="rounded-md border border-line px-4 py-2">Abbrechen</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
