/** Anzeigewerte für das Jahr 2026, abgelesen aus dem Regelregister. Keine zweite Rechenlogik. */

export const JAHR = 2026;
export const GRENZWERT_EURO = 1000;
export const ABGABESATZ_PROZENT = 4.9;

export type Positionsstatus = "ZAEHLT" | "OFFEN" | "SPERRE" | "AUSGESCHLOSSEN" | "AUSGENOMMEN";
export type Entscheidung = "uebernehmen" | "ksk-auskunft" | "verwerfen";
export type AmpelStufe = "leer" | "ok" | "offen" | "sperre" | "ueber-grenze";

export interface Position {
  id: string;
  text: string;
  betrag: number | null;
  status: Positionsstatus;
  regel: string;
  fundstelle: string;
}

export interface AuditEintrag {
  id: string;
  zeit: string;
  positionId: string;
  aktion: Entscheidung;
  von: Positionsstatus;
  nach: Positionsstatus;
  text: string;
}

export interface Dokument {
  id: string;
  name: string;
  zeit: string;
  positionen: Position[];
}

export interface ChatNachricht {
  id: string;
  rolle: "nutzer" | "assistent";
  text: string;
  positionId?: string;
  vorschlag?: AssistentVorschlag;
}

export interface AssistentVorschlag {
  position: string;
  betrag: number | null;
  rechtslage: string;
  konsequenzEuro: number | null;
  optionen: Entscheidung[];
}

export interface Pruefstand {
  dokumente: Dokument[];
  audit: AuditEintrag[];
  nachrichten: ChatNachricht[];
}

export const LEERER_STAND: Pruefstand = { dokumente: [], audit: [], nachrichten: [] };

export const STATUS_LABEL: Record<Positionsstatus, string> = {
  ZAEHLT: "Zählt",
  OFFEN: "Offen — im Chat klären",
  SPERRE: "Sperre",
  AUSGESCHLOSSEN: "Ausgeschlossen",
  AUSGENOMMEN: "Ausgenommen",
};

export const ENTSCHEIDUNG_LABEL: Record<Entscheidung, string> = {
  uebernehmen: "Übernehmen",
  "ksk-auskunft": "KSK-Auskunft",
  verwerfen: "Verwerfen",
};

export function euro(betrag: number): string {
  return betrag.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

export function abgabeEuro(bemessung: number): number {
  return Math.round(bemessung * 49) / 1000;
}

export function allePositionen(dokumente: Dokument[]): Position[] {
  return dokumente.flatMap((dokument) => dokument.positionen);
}

export function jahressumme(dokumente: Dokument[]): number {
  return allePositionen(dokumente)
    .filter((position) => position.status === "ZAEHLT")
    .reduce((summe, position) => summe + (position.betrag ?? 0), 0);
}

export function jahresbild(dokumente: Dokument[]): {
  stufe: AmpelStufe;
  titel: string;
  summe: number;
  offen: number;
  fortschritt: number;
} {
  const positionen = allePositionen(dokumente);
  const summe = jahressumme(dokumente);
  const offen = positionen.filter((position) => position.status === "OFFEN").length;
  const fortschritt = Math.min(100, Math.round((summe / GRENZWERT_EURO) * 100));
  if (positionen.length === 0) {
    return { stufe: "leer", titel: "Noch keine Rechnung", summe: 0, offen: 0, fortschritt: 0 };
  }
  if (positionen.some((position) => position.status === "SPERRE")) {
    return { stufe: "sperre", titel: "Sperre", summe, offen, fortschritt };
  }
  if (offen > 0) {
    return { stufe: "offen", titel: "Offen", summe, offen, fortschritt };
  }
  if (summe > GRENZWERT_EURO) {
    return { stufe: "ueber-grenze", titel: "Vorschlag: über dem Grenzwert", summe, offen, fortschritt };
  }
  return { stufe: "ok", titel: "Nicht abgabepflichtig", summe, offen, fortschritt };
}

export function dokumentStatus(dokument: Dokument): "Sperre" | "Offen" | "Fertig" {
  if (dokument.positionen.some((position) => position.status === "SPERRE")) return "Sperre";
  if (dokument.positionen.some((position) => position.status === "OFFEN")) return "Offen";
  return "Fertig";
}

export function naechsterStatus(aktion: Entscheidung, aktuell: Positionsstatus): Positionsstatus {
  if (aktion === "uebernehmen") return "ZAEHLT";
  if (aktion === "verwerfen") return "AUSGENOMMEN";
  return aktuell;
}

export function vorschlagPositionen(dokumentId: string, dateiname: string): Position[] {
  const zeilen: Array<Omit<Position, "id">> = [
    {
      text: "Solo-Gesang Auftritt Jubiläumskonzert",
      betrag: 400,
      status: "ZAEHLT",
      regel: "C1-Musik",
      fundstelle: "KSVG § 24 Abs. 1",
    },
    {
      text: "Moderation Konzertabend",
      betrag: 150,
      status: "ZAEHLT",
      regel: "C1-Publizistik",
      fundstelle: "KSVG § 24 Abs. 1",
    },
    {
      text: "Druckkosten Programmheft, Druckerei Nord GmbH",
      betrag: 350,
      status: "AUSGESCHLOSSEN",
      regel: "R02-GmbH",
      fundstelle: "KSK-FAQ Unternehmen, Zahlung an eine Kapitalgesellschaft",
    },
    {
      text: "Übersetzung Programmheft durch beeidigte Übersetzerin",
      betrag: 200,
      status: "OFFEN",
      regel: "C4-Quellenlücke",
      fundstelle: "Im Regelkatalog keine belegte Einordnung",
    },
  ];
  if (/summe|sperre/i.test(dateiname)) {
    zeilen.push({
      text: "Positionen und gedruckte Nettosumme weichen voneinander ab",
      betrag: null,
      status: "SPERRE",
      regel: "A3-Summenfehler",
      fundstelle: "Rechenprobe der Rechnung, keine Schätzung",
    });
  }
  return zeilen.map((zeile, index) => ({ ...zeile, id: `${dokumentId}-${index + 1}` }));
}

export function positionFinden(dokumente: Dokument[], positionId: string | null): Position | null {
  if (!positionId) return null;
  return allePositionen(dokumente).find((position) => position.id === positionId) ?? null;
}

function rechtslage(position: Position): string {
  if (position.status === "OFFEN") {
    return `${position.regel}: Die Leistung ist im Regelkatalog nicht belegt. Sie wird nicht automatisch entschieden.`;
  }
  if (position.status === "SPERRE") {
    return `${position.regel}: Die Rechnung sperrt die Gesamtberechnung, bis die Zahlen zusammenpassen.`;
  }
  if (position.status === "AUSGESCHLOSSEN" || position.status === "AUSGENOMMEN") {
    return `${position.regel}: Der Betrag zählt nicht in die Jahressumme. Fundstelle: ${position.fundstelle}.`;
  }
  return `${position.regel}: Der Betrag zählt in die Jahressumme ${JAHR}. Fundstelle: ${position.fundstelle}.`;
}

export function assistentVorschlag(frage: string, position: Position | null, summe: number): AssistentVorschlag & { text: string } {
  const ziel = position;
  const konsequenz = ziel?.betrag != null ? abgabeEuro(ziel.betrag) : null;
  const kopf = ziel
    ? `Position: ${ziel.text}\nBetrag: ${ziel.betrag == null ? "kein Einzelbetrag" : euro(ziel.betrag)}\nRechtslage: ${rechtslage(ziel)}\nKonsequenz: ${konsequenz == null ? "keine Euro-Änderung bezifferbar" : `${euro(konsequenz)} Abgabe bei ${ABGABESATZ_PROZENT.toLocaleString("de-DE")} % , wenn der Betrag in die Bemessung ${JAHR} kommt. Jahressumme der zählenden Positionen bisher ${euro(summe)}.`}`
    : `Keine einzelne Position im Kontext. Jahressumme der zählenden Positionen: ${euro(summe)}. Grenzwert ${JAHR}: ${euro(GRENZWERT_EURO)}.`;
  const bezug = frage.trim() ? `Ihre Frage: ${frage.trim()}\n\n` : "";
  return {
    position: ziel?.text ?? "Jahresbild",
    betrag: ziel?.betrag ?? null,
    rechtslage: ziel ? rechtslage(ziel) : "Ohne Positionsbezug bleibt die Einordnung beim Jahresbild.",
    konsequenzEuro: konsequenz,
    optionen: ["uebernehmen", "ksk-auskunft", "verwerfen"],
    text: `${bezug}${kopf}\n\nDas ist ein Vorschlag. Sie entscheiden.`,
  };
}

export function berichtstext(stand: Pruefstand): string {
  const bild = jahresbild(stand.dokumente);
  const zeilen = [
    `Prüfbericht ${JAHR}`,
    `Jahresbild: ${bild.titel}`,
    `Jahressumme (zählende Positionen): ${euro(bild.summe)}`,
    `Grenzwert: ${euro(GRENZWERT_EURO)}`,
    "",
    "Vorschlag, keine Rechts- oder Steuerberatung.",
    "",
  ];
  for (const dokument of stand.dokumente) {
    zeilen.push(`Dokument: ${dokument.name} (${dokumentStatus(dokument)})`);
    for (const position of dokument.positionen) {
      zeilen.push(
        `- ${position.text} | ${position.betrag == null ? "—" : euro(position.betrag)} | ${STATUS_LABEL[position.status]} | ${position.regel} | ${position.fundstelle}`,
      );
    }
    zeilen.push("");
  }
  if (stand.audit.length > 0) {
    zeilen.push("Entscheidungen");
    for (const eintrag of stand.audit) {
      zeilen.push(`- ${eintrag.zeit} | ${eintrag.text} | ${STATUS_LABEL[eintrag.von]} → ${STATUS_LABEL[eintrag.nach]}`);
    }
  }
  return zeilen.join("\n");
}
