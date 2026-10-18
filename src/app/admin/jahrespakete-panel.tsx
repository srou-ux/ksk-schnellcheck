import { listJahrespakete } from "@/lib/db";
import { listPaketQuellenStatus } from "@/lib/paket-quellen";

function statusText(status: string): string {
  return status.replaceAll("_", " ");
}

export function JahrespaketePanel() {
  const pakete = listJahrespakete();
  const quellen = listPaketQuellenStatus();

  return (
    <section className="space-y-4 rounded-xl border border-line bg-card p-4">
      <div>
        <h2 className="text-2xl">Jahrespakete</h2>
        <p className="mt-1 text-sm text-ink/70">
          Persistente Paketversionen je Jahr. Freigabe und Aktivierung werden getrennte, ausdrücklich bestätigte Aktionen.
        </p>
      </div>
      {pakete.length === 0 ? (
        <p className="rounded-md bg-paper px-4 py-3 text-sm">
          Noch keine Paketversion angelegt. Dieser erste Schritt stellt Datenmodell und Übersicht bereit; der geführte Paketaufbau folgt als nächster Admin-Schritt.
        </p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="py-2 pr-3">Jahr</th>
              <th className="py-2 pr-3">Version</th>
              <th className="py-2 pr-3">Status</th>
              <th className="py-2 pr-3">Methodik</th>
              <th className="py-2 pr-3">Regelstand</th>
              <th className="py-2 pr-3">Vollständigkeit</th>
              <th className="py-2">Aktiv</th>
            </tr>
          </thead>
          <tbody>
            {pakete.map((paket) => (
              <tr key={paket.id} className="border-b border-line/60" data-testid="jahrespaket-zeile">
                <td className="py-2 pr-3">{paket.jahr}</td>
                <td className="py-2 pr-3">v{paket.version}</td>
                <td className="py-2 pr-3">{statusText(paket.status)}</td>
                <td className="py-2 pr-3">{paket.methodology_version}</td>
                <td className="py-2 pr-3">{paket.rules_stamp}</td>
                <td className="py-2 pr-3 font-semibold text-unclear" data-testid="jahrespaket-vollstaendigkeit">
                  {paket.content_hash ? "Inhalt erfasst" : "unvollständig"}
                </td>
                <td className="py-2">{paket.is_active ? "ja" : "nein"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="border-t border-line pt-4">
        <h3 className="text-xl">Paketquellen und RAG-Nachweise</h3>
        <p className="mt-1 text-sm text-ink/70">Ein Upload allein ist nicht verwendbar. Archiv, Verarbeitung, aktuelles Indexmanifest und beide RAG-Prüfungen müssen nachweisbar sein.</p>
      </div>
      {quellen.length === 0 ? (
        <p className="rounded-md bg-paper px-4 py-3 text-sm">Noch keine archivierte Quelle einer Paketversion zugeordnet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="py-2 pr-3">Paket</th>
                <th className="py-2 pr-3">Quelle</th>
                <th className="py-2 pr-3">Archiv</th>
                <th className="py-2 pr-3">Upload</th>
                <th className="py-2 pr-3">Verarbeitung</th>
                <th className="py-2 pr-3">RAG-Prüfung</th>
                <th className="py-2">Fehler</th>
              </tr>
            </thead>
            <tbody>
              {quellen.map((quelle) => (
                <tr key={quelle.paketQuelleId} className="border-b border-line/60" data-testid="paketquelle-zeile">
                  <td className="py-2 pr-3">{quelle.jahr}/v{quelle.paketVersion}</td>
                  <td className="py-2 pr-3">
                    <span className="block">{quelle.originalName}</span>
                    <span className="text-xs text-ink/60">{quelle.archivQuelleId}</span>
                  </td>
                  <td className="py-2 pr-3">{quelle.archivstatus}</td>
                  <td className="py-2 pr-3">{quelle.uploadstatus}</td>
                  <td className="py-2 pr-3">{quelle.verarbeitungsstatus}</td>
                  <td className="py-2 pr-3 font-semibold" data-testid="paketquelle-rag-status">{quelle.ragPruefergebnis}</td>
                  <td className="py-2 text-danger">{quelle.fehler.length ? quelle.fehler.join(" ") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
