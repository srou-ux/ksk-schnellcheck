"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { ReportView } from "@/components/report-view";
import type { Audience, FrozenReport } from "@/lib/domain/types";

interface CasePayload {
  case: { id: string; title: string; audience: Audience; status: string };
  documents: Array<{ id: string; original_name: string; mime_type: string; size_bytes: number }>;
  run: { status: string; current_stage: string | null; error_layperson: string | null; examiner_finding: string | null } | null;
  report: FrozenReport | null;
}

const stages = ["A", "B", "C", "D", "E", "F", "G"];
const stageLabel: Record<string, string> = {
  A: "Vorbereitung",
  B: "Formular",
  C: "Freitext",
  D: "Abgleich",
  E: "Bewertung",
  F: "Prüfer",
  G: "Bericht",
};

export function CaseWorkspace({ caseId }: { caseId: string }) {
  const router = useRouter();
  const [data, setData] = useState<CasePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch(`/api/cases/${caseId}`);
      const body = await response.json();
      if (!response.ok) {
        setError(body.error ?? "Der Fall ist nicht da.");
        return;
      }
      setData(body);
    } catch {
      setError("Wir konnten den Fall nicht laden.");
    }
  }, [caseId]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let cancelled = false;
    async function tick() {
      await load();
      if (cancelled) return;
    }
    void tick();
    timer = setInterval(() => {
      void load();
    }, 1500);
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [load]);

  async function upload(file: File) {
    setError(null);
    setUploading(true);
    const form = new FormData();
    form.set("file", file);
    const response = await fetch(`/api/cases/${caseId}/documents`, { method: "POST", body: form });
    const body = await response.json();
    if (!response.ok) {
      setUploading(false);
      setError(body.error ?? "Die Datei konnte nicht gespeichert werden.");
      return;
    }
    await load();
    setUploading(false);
    await start();
  }

  async function start() {
    setError(null);
    const response = await fetch(`/api/cases/${caseId}/run`, { method: "POST" });
    const body = await response.json();
    if (!response.ok) setError(body.error ?? "Die Prüfung konnte nicht starten.");
    await load();
  }

  async function remove() {
    if (!window.confirm("Fall, Rechnung, Bericht und Chat werden unwiderruflich gelöscht.")) return;
    await fetch(`/api/cases/${caseId}`, { method: "DELETE" });
    router.push("/");
  }

  if (!data && !error) return <p>Der Fall wird geladen …</p>;
  if (!data) return <p className="text-danger">{error}</p>;
  const running = data.run && (data.run.status === "queued" || data.run.status === "running");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl">{data.case.title}</h1>
          <p className="mt-1 text-sm text-ink/60">{data.case.audience === "steuerberater" ? "Fundstellen" : "Verein"} · {data.case.status}</p>
        </div>
        <button onClick={() => void remove()} className="text-sm text-danger">Fall löschen</button>
      </div>
      <section
        onDragOver={(event) => { event.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDrag(false);
          const file = event.dataTransfer.files[0];
          if (file) void upload(file);
        }}
        className={`rounded-xl border border-dashed p-6 ${drag ? "border-stamp bg-emerald-50" : "border-line bg-card"}`}
      >
        <h2 className="text-xl">Rechnung</h2>
        <p className="mt-1 text-sm text-ink/70">PDF, PNG oder JPG, höchstens 20 MB. Nach dem Hochladen startet die Prüfung.</p>
        <input
          ref={fileRef}
          type="file"
          accept="application/pdf,image/png,image/jpeg,.pdf,.png,.jpg,.jpeg"
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void upload(file);
          }}
        />
        {data.documents.map((document) => (
          <p key={document.id} className="mt-3 text-sm">{document.original_name} · {document.mime_type} · {document.size_bytes} Bytes</p>
        ))}
        <button
          disabled={Boolean(running) || uploading}
          onClick={() => {
            if (data.documents.length === 0) fileRef.current?.click();
            else void start();
          }}
          className="mt-4 rounded-md bg-stamp px-4 py-2 text-white disabled:opacity-50"
        >
          {uploading ? "Rechnung wird hochgeladen …" : running ? "Prüfung läuft …" : data.documents.length === 0 ? "Rechnung hochladen und prüfen" : "Prüfung starten"}
        </button>
      </section>
      {error ? <p className="text-sm text-danger">{error}</p> : null}
      {data.run ? (
        <section>
          <h2 className="text-xl">Lauf</h2>
          <ol className="mt-3 flex flex-wrap gap-2">
            {stages.map((stage) => {
              const current = data.run?.current_stage;
              const reached = current ? stages.indexOf(current) >= stages.indexOf(stage) : false;
              return <li key={stage} className={`rounded-full border px-3 py-1 text-sm ${reached ? "border-stamp text-stamp" : "border-line text-ink/40"}`}>{stage} {stageLabel[stage]}</li>;
            })}
          </ol>
          {data.run.error_layperson ? <p className="mt-3 text-sm text-danger">{data.run.error_layperson}</p> : null}
          {data.run.examiner_finding ? <p className="mt-2 text-sm">Prüfer: {data.run.examiner_finding}</p> : null}
        </section>
      ) : null}
      {data.report ? (
        <>
          <ReportView report={data.report} audience={data.case.audience} />
          <ChatPanel caseId={caseId} defaultMode={data.case.audience === "steuerberater" ? "steuerberater" : "nutzer"} />
        </>
      ) : null}
    </div>
  );
}
