import { assistentVorschlag, jahressumme, type Dokument, type Position } from "@/lib/pruefstand";
import { json, readBody } from "@/lib/http";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/** Platzhalter ohne Sprachmodell. KI_ENABLED schaltet später den Dual-Modus frei. */
export async function POST(request: Request): Promise<Response> {
  if (process.env.KI_ENABLED === "true") {
    return json({ error: "Die KI-Anbindung ist noch nicht verbunden." }, 501);
  }
  const body = await readBody<{
    frage?: string;
    position?: Position | null;
    dokumente?: Dokument[];
  }>(request);
  const frage = body?.frage?.trim() ?? "";
  const dokumente = Array.isArray(body?.dokumente) ? body.dokumente : [];
  const vorschlag = assistentVorschlag(frage, body?.position ?? null, jahressumme(dokumente));
  return json({
    mock: true,
    kiEnabled: false,
    ...vorschlag,
  });
}
