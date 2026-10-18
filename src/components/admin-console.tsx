"use client";

import { useCallback, useEffect, useState } from "react";

interface Library {
  id: string;
  name: string;
  description: string | null;
  version_label: string;
  is_active: number;
  mistral_library_id: string | null;
}

interface LibraryDocument {
  id: string;
  name: string;
  status: string;
  page_count: number | null;
  summary: string | null;
  error: string | null;
}

export function AdminConsole() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [password, setPassword] = useState("browser-admin");
  const [error, setError] = useState<string | null>(null);
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [text, setText] = useState<string | null>(null);
  const [keyStatus, setKeyStatus] = useState<string>("unbekannt");
  const [mistralOn, setMistralOn] = useState(true);
  const [mistralKey, setMistralKey] = useState("");
  const [keyStored, setKeyStored] = useState(false);
  const [keyMessage, setKeyMessage] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", description: "", versionLabel: "LIB-KSK-v12@2026-10-05" });
  const [confirm, setConfirm] = useState<{ kind: "activate" | "delete"; id: string } | null>(null);

  const loadLibraries = useCallback(async () => {
    const response = await fetch("/api/admin/libraries");
    if (response.status === 401) {
      setAuthed(false);
      return;
    }
    const body = await response.json();
    setLibraries(body.libraries ?? []);
    setAuthed(true);
  }, []);

  const refreshKey = useCallback(async () => {
    const [storedResponse, statusResponse] = await Promise.all([
      fetch("/api/admin/mistral-key"),
      fetch("/api/admin/key-status"),
    ]);
    if (storedResponse.status === 401 || statusResponse.status === 401) {
      setAuthed(false);
      return;
    }
    if (storedResponse.ok) {
      const stored = await storedResponse.json();
      setKeyStored(Boolean(stored.stored));
    }
    if (statusResponse.ok) {
      const status = await statusResponse.json();
      setKeyStatus(status.status === "verbunden" ? "verbunden" : "nicht verbunden");
      setMistralOn(Boolean(status.enabled));
    }
  }, []);

  async function setUse(enabled: boolean) {
    setError(null);
    const response = await fetch("/api/admin/mistral-use", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    const body = await response.json();
    if (!response.ok) {
      setError(body.error ?? "Die Nutzung konnte nicht geändert werden.");
      return;
    }
    setMistralOn(Boolean(body.enabled));
    await refreshKey();
  }

  useEffect(() => {
    if (!authed) return;
    void refreshKey();
  }, [authed, refreshKey]);

  useEffect(() => {
    void fetch("/api/admin/session").then(async (response) => {
      const body = await response.json();
      setAuthed(Boolean(body.authenticated));
      setReady(true);
      if (body.authenticated) await loadLibraries();
    });
  }, [loadLibraries]);

  const loadDocuments = useCallback(async (libraryId: string) => {
    const response = await fetch(`/api/admin/libraries/${libraryId}/documents`);
    const body = await response.json();
    setDocuments(body.documents ?? []);
  }, []);

  useEffect(() => {
    if (!selected || !authed) return;
    void loadDocuments(selected);
    const timer = setInterval(() => void loadDocuments(selected), 3000);
    return () => clearInterval(timer);
  }, [selected, authed, loadDocuments]);

  async function login(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const response = await fetch("/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    const body = await response.json();
    if (!response.ok) {
      setError(body.error ?? "Anmeldung fehlgeschlagen.");
      return;
    }
    setPassword("");
    setAuthed(true);
    await loadLibraries();
  }

  async function createLibrary(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const response = await fetch("/api/admin/libraries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const body = await response.json();
    if (!response.ok) {
      setError(body.error ?? "Die Library konnte nicht angelegt werden.");
      return;
    }
    setForm({ name: "", description: "", versionLabel: "LIB-KSK-v12@2026-10-05" });
    await loadLibraries();
  }

  async function upload(files: FileList | null) {
    if (!selected || !files?.length) return;
    const formData = new FormData();
    for (const file of files) formData.append("files", file);
    const response = await fetch(`/api/admin/libraries/${selected}/documents`, { method: "POST", body: formData });
    const body = await response.json();
    if (!response.ok) setError(body.error ?? "Upload fehlgeschlagen.");
    await loadDocuments(selected);
  }

  async function confirmAction() {
    if (!confirm) return;
    const response = await fetch(confirm.kind === "activate" ? `/api/admin/libraries/${confirm.id}/activate` : `/api/admin/libraries/${confirm.id}`, { method: confirm.kind === "activate" ? "POST" : "DELETE" });
    const body = await response.json();
    if (!response.ok) setError(body.error ?? "Die Aktion ist fehlgeschlagen.");
    setConfirm(null);
    if (confirm.kind === "delete" && selected === confirm.id) setSelected(null);
    await loadLibraries();
  }

  if (!ready) return <p>Admin wird geladen …</p>;
  if (!authed) {
    return (
      <form onSubmit={login} className="mx-auto max-w-md space-y-4 rounded-xl border border-line bg-card p-6">
        <h1 className="text-3xl">Admin</h1>
        <p className="text-sm text-ink/70">Nur der Referenz-Korpus. Keine Kundendaten.</p>
        <label className="block text-sm">
          Admin-Passwort
          <input type="text" name="admin-password" autoComplete="off" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" />
        </label>
        {error ? <p className="text-sm text-danger">{error}</p> : null}
        <button className="rounded-md bg-stamp px-4 py-2 text-white">Anmelden</button>
      </form>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-4xl">Referenz-Libraries</h1>
        <div className="flex gap-3 text-sm">
          <button onClick={() => void refreshKey()} className="rounded-md border border-line px-3 py-2">Schlüssel erneut prüfen</button>
          <button onClick={() => void fetch("/api/admin/session", { method: "POST" }).then(() => setAuthed(false))} className="text-ink/60">Abmelden</button>
        </div>
      </div>
      <section className="rounded-xl border border-line bg-card p-4">
        {keyStatus === "verbunden" ? (
          <p className="rounded-md bg-emerald-50 px-4 py-3 text-base font-semibold text-ok">Die Verbindung steht.</p>
        ) : (
          <p className="rounded-md bg-amber-50 px-4 py-3 text-base font-semibold text-unclear">{keyStatus === "unbekannt" ? "Die Verbindung wird geprüft." : "Die Verbindung steht nicht."}{keyStored ? "" : " Kein Schlüssel auf diesem Rechner hinterlegt."}</p>
        )}
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <span>Nutzung für Prüfungen</span>
          <button type="button" onClick={() => void setUse(true)} className={`rounded-md px-4 py-2 ${mistralOn ? "bg-stamp text-white" : "border border-line"}`}>Ein</button>
          <button type="button" onClick={() => void setUse(false)} className={`rounded-md px-4 py-2 ${mistralOn ? "border border-line" : "bg-ink text-white"}`}>Aus</button>
          <span className="text-ink/70">{mistralOn ? "Prüfungen gehen an Mistral." : "Prüfungen bleiben im Mock-Modus. Der Schlüssel bleibt gespeichert."}</span>
        </div>
      </section>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          setError(null);
          setKeyMessage(null);
          const response = await fetch("/api/admin/mistral-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ apiKey: mistralKey }),
          });
          const body = await response.json();
          if (!response.ok) {
            setError(body.error ?? "Der Schlüssel konnte nicht gespeichert werden.");
            return;
          }
          setMistralKey("");
          setKeyStored(true);
          setKeyMessage("Gespeichert nur auf diesem Rechner. Der Schlüssel wird hier nicht wieder angezeigt.");
          await refreshKey();
        }}
        className="space-y-3 rounded-xl border border-line bg-card p-4"
      >
        <h2 className="text-xl">Mistral-Schlüssel</h2>
        <p className="text-sm text-ink/70">Der Schlüssel bleibt auf diesem Rechner und steht nicht im Browser-Code. {keyStored ? "Ein Schlüssel ist bereits hinterlegt." : "Noch kein Schlüssel hinterlegt."}</p>
        <label className="block text-sm">
          Schlüssel einfügen
          <input type="text" name="mistral-key" autoComplete="off" value={mistralKey} onChange={(event) => setMistralKey(event.target.value)} className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2" placeholder="Schlüssel aus der Mistral-Konsole" />
        </label>
        <button className="rounded-md bg-stamp px-4 py-2 text-white">Schlüssel speichern</button>
        {keyMessage ? <p className="text-sm text-ok">{keyMessage}</p> : null}
      </form>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      <form onSubmit={createLibrary} className="grid gap-3 rounded-xl border border-line bg-card p-4 md:grid-cols-3">
        <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Name" className="rounded-md border border-line bg-paper px-3 py-2" />
        <input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Beschreibung" className="rounded-md border border-line bg-paper px-3 py-2" />
        <input value={form.versionLabel} onChange={(event) => setForm({ ...form, versionLabel: event.target.value })} placeholder="Versionsbezeichnung" className="rounded-md border border-line bg-paper px-3 py-2" />
        <button className="rounded-md bg-stamp px-4 py-2 text-white md:col-span-3 md:w-fit">Library anlegen</button>
      </form>
      <ul className="space-y-2">
        {libraries.map((library) => (
          <li key={library.id} className="rounded-xl border border-line bg-card p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button onClick={() => { setSelected(library.id); setText(null); }} className="text-left">
                <span className="font-serif text-lg">{library.name}</span>
                <span className="mt-1 block text-sm text-ink/60">{library.version_label} {library.is_active ? "· aktiv" : ""}</span>
              </button>
              <span className="flex gap-3 text-sm">
                <button onClick={() => setConfirm({ kind: "activate", id: library.id })}>Aktiv setzen</button>
                <button className="text-danger" onClick={() => setConfirm({ kind: "delete", id: library.id })}>Löschen</button>
              </span>
            </div>
          </li>
        ))}
      </ul>
      {selected ? (
        <section className="rounded-xl border border-line bg-card p-4">
          <h2 className="text-xl">Dokumente</h2>
          <div
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => { event.preventDefault(); void upload(event.dataTransfer.files); }}
            className="mt-3 rounded-md border border-dashed border-line p-4 text-sm"
          >
            Dateien hierher ziehen oder auswählen. Es landet nur der Referenz-Korpus bei Mistral, keine Rechnung.
            <input type="file" multiple className="mt-2 block" onChange={(event) => void upload(event.target.files)} />
          </div>
          <ul className="mt-4 space-y-3 text-sm">
            {documents.map((document) => (
              <li key={document.id} className="border-t border-line pt-3">
                <p>{document.name} · {document.status} · Seiten {document.page_count ?? "nicht geliefert"}</p>
                <p className="text-ink/70">{document.summary ?? "Keine Zusammenfassung von Mistral."}</p>
                {document.error ? <p className="text-danger">{document.error}</p> : null}
                <span className="mt-1 flex gap-3">
                  <button onClick={() => void fetch(`/api/admin/libraries/${selected}/documents/${document.id}`).then((response) => response.json()).then((body) => setText(body.text ?? body.error))}>Text</button>
                  <button className="text-danger" onClick={() => void fetch(`/api/admin/libraries/${selected}/documents/${document.id}`, { method: "DELETE" }).then(() => loadDocuments(selected))}>Dokument löschen</button>
                </span>
              </li>
            ))}
          </ul>
          {text ? <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-paper p-3 text-xs">{text}</pre> : null}
        </section>
      ) : null}
      {confirm ? (
        <div className="fixed inset-0 grid place-items-center bg-ink/40 p-4">
          <div className="max-w-md rounded-xl bg-card p-5">
            <h3 className="text-xl">{confirm.kind === "activate" ? "Library aktiv setzen?" : "Library löschen?"}</h3>
            <p className="mt-2 text-sm">
              {confirm.kind === "activate"
                ? "Genau eine Library ist aktiv. Neue Läufe und der Chat nutzen danach nur noch diese. Bestehende Berichte behalten ihre gespeicherte Kennung."
                : "Die Library wird bei Mistral und hier gelöscht, mit allen Dokumenten darin. Kundendaten sind davon nicht betroffen."}
            </p>
            <div className="mt-4 flex gap-3">
              <button onClick={() => void confirmAction()} className="rounded-md bg-stamp px-4 py-2 text-white">Bestätigen</button>
              <button onClick={() => setConfirm(null)}>Abbrechen</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
