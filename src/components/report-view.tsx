import { CATEGORY_LABEL, DEPENDENCY_LABEL, KIND_LABEL, PAYEE_LABEL, ROLE_LABEL, STATE_LABEL } from "@/lib/domain/labels";
import { formatEuro, formatPercentFromBps } from "@/lib/domain/money";
import type { Audience, FrozenReport, KskCategory, PositionState } from "@/lib/domain/types";

const stateClass: Record<PositionState, string> = {
  ABGABEPFLICHTIG: "text-danger",
  NICHT_ABGABEPFLICHTIG: "text-ok",
  UNGEKLÄRT: "text-unclear",
};

export function ReportView({ report, audience }: { report: FrozenReport; audience: Audience }) {
  const advisor = audience === "steuerberater";
  return (
    <section className="space-y-6">
      {report.readingMode === "mock" ? (
        <p className="rounded-md border border-unclear/40 bg-amber-50 px-4 py-3 text-sm text-unclear">
          Ablesung im Mock-Modus. Das ist keine Prüfung durch Mistral. Sobald ein Schlüssel gesetzt und der Mock aus ist, lesen die drei konfigurierten Modelle.
        </p>
      ) : null}
      {report.filingSeason ? (
        <p className="rounded-md border border-stamp/30 bg-emerald-50 px-4 py-3 text-sm">
          Meldesaison: die gesetzliche Frist für das Vorjahr endet am {report.filingDeadline}.
        </p>
      ) : (
        <p className="text-sm text-ink/70">Gesetzliche Meldefrist: {report.filingDeadline}.</p>
      )}
      <div>
        <h2 className="text-3xl">Bericht</h2>
        <p className="mt-2 text-ink/80">{advisor ? report.advisorSummary : report.laypersonSummary}</p>
        <p className="mt-2 text-sm text-ink/60">Methodik {report.methodologyVersion}, Quellenstand {report.rulesStamp}. Rundung: ganze Cent, kaufmännisch.</p>
      </div>
      <dl className="grid gap-3 rounded-xl border border-line bg-card p-4 text-sm md:grid-cols-3">
        <div><dt className="text-ink/50">Jahr</dt><dd>{report.year ?? "Ungeklärt"}</dd></div>
        <div><dt className="text-ink/50">Rolle des Auftraggebers</dt><dd>{ROLE_LABEL[report.payerRole]}</dd></div>
        <div><dt className="text-ink/50">Art des Leistenden</dt><dd>{PAYEE_LABEL[report.payeeKind]}</dd></div>
        <div><dt className="text-ink/50">Satz</dt><dd>{report.rateBps ? formatPercentFromBps(report.rateBps) : "nicht angesetzt"}</dd></div>
        <div><dt className="text-ink/50">Bemessungsgrundlage</dt><dd>{formatEuro(report.totalBasisCents)}</dd></div>
        <div><dt className="text-ink/50">Abgabe dieses Falls</dt><dd>{formatEuro(report.totalLevyCents)}</dd></div>
      </dl>
      <p className="text-sm text-ink/75">{report.totalNote}</p>
      <div>
        <h3 className="text-xl">Kategorien</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          {report.categories.map((bucket) => (
            <article key={bucket.category} className="rounded-lg border border-line bg-card p-3">
              <h4 className="font-serif">{CATEGORY_LABEL[bucket.category as KskCategory]}</h4>
              <p className="mt-2 text-sm">Basis {formatEuro(bucket.basisCents)}</p>
              <p className="text-sm">Abgabe {formatEuro(bucket.levyCents)}</p>
            </article>
          ))}
        </div>
        {report.uncategorisedPositionIds.length > 0 ? (
          <p className="mt-2 text-sm text-unclear">Ohne Kategorie und deshalb in keinem Topf: {report.uncategorisedPositionIds.join(", ")}.</p>
        ) : null}
      </div>
      <div className="space-y-3">
        <h3 className="text-xl">Positionen</h3>
        {report.positions.length === 0 ? <p className="text-sm">Keine bestätigte Position.</p> : null}
        {report.positions.map((position) => (
          <article key={position.id} className="rounded-xl border border-line bg-card p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h4 className="text-lg">{position.id} · {position.label === "UNGEKLÄRT" ? "Bezeichnung ungeklärt" : position.label}</h4>
              <span className={`text-sm font-semibold ${stateClass[position.state]}`}>{STATE_LABEL[position.state]}</span>
            </div>
            <p className="mt-1 text-sm text-ink/70">{KIND_LABEL[position.kind]} · {position.category === "UNGEKLÄRT" ? "Kategorie ungeklärt" : CATEGORY_LABEL[position.category]} · {formatEuro(position.amountCents)} · Quelle {position.source}</p>
            <p className="mt-2 text-sm">{position.rationaleLayperson}</p>
            {advisor && position.citation ? <p className="mt-2 text-sm text-ink/70">Fundstelle: {position.citation}</p> : null}
            {!advisor && position.citation ? <p className="mt-2 text-xs text-ink/50">Grundlage: {position.citation}</p> : null}
            {position.hint ? (
              <div className="mt-3 rounded-md bg-paper p-3 text-sm">
                <p>Position {position.id}: als ABGABEPFLICHTIG eingestuft. Möglicher Ausschlussgrund: {position.hint.possibleExclusionReason} Fundstelle: {position.hint.citation}.</p>
                <p className="mt-2">Benötigter Nachweis: {position.hint.requiredEvidence}</p>
                <p className="mt-2">{DEPENDENCY_LABEL[position.hint.dependency]}.</p>
                <p className="mt-2">Wann ein Nachweis nicht wirkt: {position.hint.whenEvidenceDoesNotWork}</p>
                <p className="mt-2 text-ink/70">{position.hint.note} Ohne Nachweis bleibt die Einstufung bestehen.</p>
              </div>
            ) : null}
          </article>
        ))}
      </div>
      {report.conflicts.length > 0 ? (
        <div>
          <h3 className="text-xl">Abweichungen</h3>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {report.conflicts.map((conflict) => (
              <li key={conflict.field}>{conflict.field}: Formular bleibt ({conflict.formValue}), Fließtext wich ab.</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div>
        <h3 className="text-xl">Tore</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {report.gates.map((gate) => (
            <li key={gate.id}>{gate.passed ? "Bestanden" : "Nicht bestanden"} · {gate.title}: {gate.layperson}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
