import { json, readBody } from "@/lib/http";
import { jahreswechselHinweis } from "@/lib/mistral/zahlen-werte";
import { bearbeiteEntwurf, gebeFrei, ladeEintraege, legeEntwurfAn, type WertEingabe } from "@/lib/zahlen-register";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const HINWEIS = "Das System prüft nur, ob Quelle, Fundstelle, Dokumentstand, Gültigkeit und Anwendungsbereich ausgefüllt sind. Das ist keine fachliche Prüfung und keine Bestätigung, dass der Wert richtig ist.";

function heute(): string {
  return new Date().toISOString().slice(0, 10);
}

function eingabe(body: {
  gruppe?: string;
  beschreibung?: string;
  betrag?: string;
  einheit?: string;
  gueltig_ab?: string;
  gueltig_bis?: string | null;
  quelle?: string;
  fundstelle?: string;
  dokumentstand?: string;
  anwendungsbereich?: string;
} | null): WertEingabe {
  if (typeof body?.betrag !== "string") throw new Error("Der Betrag muss als Text gesendet werden, damit keine Rundung entsteht.");
  if (body.einheit !== "euro" && body.einheit !== "prozent") throw new Error("Die Einheit muss Euro oder Prozent sein.");
  return {
    gruppe: body.gruppe ?? "",
    beschreibung: body.beschreibung,
    betrag: body.betrag,
    einheit: body.einheit,
    gueltigAb: body.gueltig_ab ?? "",
    gueltigBis: body.gueltig_bis ? body.gueltig_bis : null,
    quelle: body.quelle,
    fundstelle: body.fundstelle,
    dokumentstand: body.dokumentstand,
    anwendungsbereich: body.anwendungsbereich,
  };
}

export async function GET(): Promise<Response> {
  try {
    return json({ eintraege: ladeEintraege(), heute: heute(), jahreswechsel: jahreswechselHinweis(), hinweis: HINWEIS });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Die Werteliste konnte nicht gelesen werden.";
    return json({ error: message }, 400);
  }
}

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await readBody<{
      aktion?: string;
      id?: string;
      gruppe?: string;
      beschreibung?: string;
      betrag?: string;
      einheit?: string;
      gueltig_ab?: string;
      gueltig_bis?: string | null;
      quelle?: string;
      fundstelle?: string;
      dokumentstand?: string;
      anwendungsbereich?: string;
    }>(request);
    const werte = eingabe(body);
    if (body?.aktion === "bearbeiten") {
      if (!body.id) throw new Error("Der Entwurf fehlt.");
      bearbeiteEntwurf(body.id, werte);
    } else if (body?.aktion === "freigeben") {
      gebeFrei(werte);
    } else {
      legeEntwurfAn(werte);
    }
    return json({ eintraege: ladeEintraege(), heute: heute(), jahreswechsel: jahreswechselHinweis(), hinweis: HINWEIS });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Die Werteliste konnte nicht gespeichert werden.";
    return json({ error: message }, 400);
  }
}
