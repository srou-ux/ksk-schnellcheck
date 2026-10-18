/** Phase 2 ist vorbereitet und in Phase 1 nicht ausführbar. */
export const PHASE2_MESSAGE =
  "Wir können Nachweise in dieser Version noch nicht erneut prüfen. Ein Re-Run ist Phase 2 und ändert die Einordnung hier nicht.";

export type EvidenceMark = "KONSISTENT" | "TEILWEISE" | "NICHT_TRAGFAEHIG" | "UNGEKLÄRT";

export interface EvidenceCheck {
  id: "N-A" | "N-B" | "N-C" | "N-D";
  title: string;
  purpose: string;
}

export const EVIDENCE_CHECKS: EvidenceCheck[] = [
  { id: "N-A", title: "Dokumentqualität", purpose: "Prüft, ob der Nachweis lesbar und dem behaupteten Vorgang zuordenbar ist." },
  { id: "N-B", title: "Dreifaches Ablesen", purpose: "Liest den Nachweis mit drei Modellen und lässt Uneinigkeit ungeklärt." },
  { id: "N-C", title: "Kreuzprüfung", purpose: "Vergleicht Nachweis, Rechnung, Daten und Parteien. Kennzeichnet nie als echt." },
  { id: "N-D", title: "Kennzeichnung", purpose: "Setzt KONSISTENT, TEILWEISE, NICHT TRAGFÄHIG oder UNGEKLÄRT." },
];

export interface ReportV2Change {
  positionId: string;
  fromState: string;
  toState: string;
  reason: string;
}

export function startEvidenceRerun(): never {
  throw new Error(PHASE2_MESSAGE);
}
