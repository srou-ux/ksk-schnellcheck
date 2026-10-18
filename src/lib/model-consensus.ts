import { euroAmounts } from "@/lib/mistral/rag-pruefung";

export type LaufSicht = { signatur: string; einig: boolean; kurz: string };

export type PrueferSicht = {
  id: string;
  label: string;
  ok: boolean;
  answer: string;
  documents: string[];
  amountKeys?: string[];
  amountLabels?: string[];
};

export type KonsensErgebnis = {
  status: "konsens" | "abweichung" | "keiner" | "nicht-pruefbar" | "hinweis";
  line: string;
  detail: string | null;
};

function groupWho(labels: string[]): string {
  const numbers = labels.map((label) => (label ?? "").match(/Prüfer\s+(\d+)/)?.[1] ?? "");
  if (numbers.every(Boolean)) return `Prüfer ${numbers.join(" & ")}`;
  return labels.join(" & ");
}

export function amountKeys(answer: string): { keys: string[]; labels: string[] } {
  const amounts = euroAmounts(answer);
  return {
    keys: amounts.map((item) => item.value.toFixed(2)),
    labels: amounts.map((item) => item.label),
  };
}

function signature(keys: string[], documents: string[]): string {
  return `${[...keys].sort().join(",")}|${[...documents].sort().join(",")}`;
}

function groupText(labels: string[], amounts: string[], documents: string[]): string {
  const who = groupWho(labels);
  const money = amounts.length > 0 ? amounts.join(", ") : "keine €-Beträge";
  const docs = documents.length > 0 ? documents.join(", ") : "keine Fundstelle";
  return `${who}: ${money} / ${docs}`;
}

function vorbereiten(rows: PrueferSicht[]): KonsensErgebnis & LaufSicht {
  const answered = rows.filter((row) => row.ok);
  if (answered.length < rows.length) {
    const line = `⚠️ nicht prüfbar (${answered.length}/${rows.length} geantwortet)`;
    return { status: "nicht-pruefbar", line, detail: null, signatur: `nicht-pruefbar|${answered.length}`, einig: false, kurz: line };
  }
  const prepared = answered.map((row) => {
    const amounts = row.amountKeys
      ? { keys: row.amountKeys, labels: row.amountLabels ?? [] }
      : amountKeys(row.answer);
    return { ...row, keys: amounts.keys, labels: amounts.labels, documents: [...row.documents].sort() };
  });
  const groups = new Map<string, typeof prepared>();
  for (const row of prepared) {
    const key = signature(row.keys, row.documents);
    groups.set(key, [...(groups.get(key) ?? []), row]);
  }
  const ordered = [...groups.values()].sort((a, b) => a.length - b.length);
  const detail = ordered.map((group) => groupText(group.map((row) => row.label), group[0].labels, group[0].documents)).join(" — ");
  const signatur = ordered.map((group) => signature(group[0].keys, group[0].documents)).join("||");
  if (groups.size === 1) {
    return { status: "konsens", line: `✅ Konsens ${rows.length}/${rows.length}`, detail: null, signatur, einig: true, kurz: detail };
  }
  if (rows.length > 2 && ordered.some((group) => group.length === rows.length - 1)) {
    const line = "⚠️ Abweichung 2/3 — NICHT OK, keine Mehrheitsentscheidung";
    return { status: "abweichung", line, detail, signatur, einig: false, kurz: detail };
  }
  const line = "❌ Kein Konsens — UNGEKLÄRT";
  return { status: "keiner", line, detail, signatur, einig: false, kurz: detail };
}

export function konsensVergleich(rows: PrueferSicht[]): KonsensErgebnis {
  const ergebnis = vorbereiten(rows);
  return { status: ergebnis.status, line: ergebnis.line, detail: ergebnis.detail };
}

export function laufSchluessel(rows: PrueferSicht[]): LaufSicht {
  const ergebnis = vorbereiten(rows);
  return { signatur: ergebnis.signatur, einig: ergebnis.einig, kurz: ergebnis.kurz };
}

export function vergleicheLaeufe(laeufe: LaufSicht[]): KonsensErgebnis {
  const detail = laeufe.map((lauf, index) => `Lauf ${index + 1}: ${lauf.kurz}`).join(" — ");
  const gleich = laeufe.length === 3 && laeufe.every((lauf) => lauf.einig && lauf.signatur === laeufe[0].signatur);
  if (gleich) return { status: "konsens", line: "✅ Dieselbe Antwort in 3 von 3 Läufen", detail };
  return { status: "keiner", line: "❌ Kein Konsens — die drei Läufe stimmen nicht überein", detail };
}
