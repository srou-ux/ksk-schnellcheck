import { geldTreffer, istInterneQuelle } from "@/lib/mistral/rag-pruefung";

export type ChunkBeleg = {
  id: string;
  dokument: string;
  seite: string | null;
  text: string;
};

function textVon(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function seiteVon(record: Record<string, unknown>): string | null {
  const meta = record.metadata;
  const quellen = [record];
  if (meta && typeof meta === "object") quellen.push(meta as Record<string, unknown>);
  for (const quelle of quellen) {
    for (const [key, value] of Object.entries(quelle)) {
      if (!/page|seite/i.test(key)) continue;
      if (typeof value === "number" && Number.isFinite(value)) return String(value);
      if (typeof value === "string" && value.trim()) return value.trim();
    }
  }
  return null;
}

function dokumentVon(record: Record<string, unknown>): string {
  for (const key of ["title", "document_name", "documentName", "filename", "file_name", "name"]) {
    const value = textVon(record[key]);
    if (value && !/^(document_library|web_search|library_search)$/i.test(value)) return value;
  }
  return "";
}

function schnipsel(record: Record<string, unknown>): Array<{ text: string; seite: string | null }> {
  const roh = record.snippets ?? record.snippet;
  if (!Array.isArray(roh)) return [];
  return roh.flatMap((item) => {
    if (typeof item === "string" && item.trim()) return [{ text: item.trim(), seite: null }];
    if (!item || typeof item !== "object") return [];
    const objekt = item as Record<string, unknown>;
    const text = textVon(objekt.content) || textVon(objekt.text) || textVon(objekt.snippet);
    return text ? [{ text, seite: seiteVon(objekt) }] : [];
  });
}

function textDesChunks(record: Record<string, unknown>): string {
  const teile = schnipsel(record);
  if (teile.length > 0) return teile.map((teil) => teil.text).join("\n");
  for (const key of ["content", "text", "description"]) {
    const value = textVon(record[key]);
    if (value) return value;
  }
  return "";
}

function siehtAusWieChunk(record: Record<string, unknown>): boolean {
  const hatSnippet = Array.isArray(record.snippets) || Array.isArray(record.snippet) || Boolean(textVon(record.content));
  return Boolean(dokumentVon(record) && (hatSnippet || textVon(record.description) || textVon(record.text)));
}

function zuChunks(record: Record<string, unknown>, idHinweis: string): ChunkBeleg[] {
  const dokument = dokumentVon(record);
  const id = textVon(record.id) || textVon(record.url) || idHinweis;
  const teile = schnipsel(record);
  if (teile.length > 0 && teile.some((teil) => teil.seite)) {
    return teile.map((teil, index) => ({
      id: `${id}:${index}`,
      dokument: dokument || id,
      seite: teil.seite ?? seiteVon(record),
      text: teil.text,
    }));
  }
  const text = teile.map((teil) => teil.text).join("\n") || textDesChunks(record);
  if (!dokument && !text) return [];
  return [{ id, dokument: dokument || id, seite: seiteVon(record), text }];
}

function walkChunks(value: unknown, gefunden: ChunkBeleg[], tiefe: number): void {
  if (tiefe > 8 || value == null) return;
  if (typeof value === "string") {
    try {
      walkChunks(JSON.parse(value) as unknown, gefunden, tiefe + 1);
    } catch {
      // Kein JSON.
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) walkChunks(item, gefunden, tiefe + 1);
    return;
  }
  if (typeof value !== "object") return;
  const record = value as Record<string, unknown>;
  for (const [key, nested] of Object.entries(record)) {
    if (key === "result" && typeof nested === "string") {
      walkChunks(nested, gefunden, tiefe + 1);
      continue;
    }
    if (nested && typeof nested === "object" && !Array.isArray(nested) && siehtAusWieChunk(nested as Record<string, unknown>)) {
      gefunden.push(...zuChunks(nested as Record<string, unknown>, key));
      continue;
    }
    if (nested && typeof nested === "object") walkChunks(nested, gefunden, tiefe + 1);
  }
}

export function chunksAusWert(value: unknown): ChunkBeleg[] {
  const gefunden: ChunkBeleg[] = [];
  walkChunks(value, gefunden, 0);
  const eigene = new Map<string, ChunkBeleg>();
  for (const chunk of gefunden) {
    const schluessel = `${chunk.id}|${chunk.dokument}|${chunk.seite ?? ""}|${chunk.text.slice(0, 80)}`;
    if (!eigene.has(schluessel)) eigene.set(schluessel, chunk);
  }
  return [...eigene.values()];
}

export function kurzName(dokument: string): string {
  const info = dokument.match(/info[_ -]?(\d+)/i);
  if (info) return `Info_${info[1]}`;
  return dokument.replace(/\.pdf$/i, "");
}

export function chunkZeile(chunks: ChunkBeleg[]): string {
  if (chunks.length === 0) return "keine";
  const gruppen = new Map<string, { seiten: string[]; ids: string[] }>();
  for (const chunk of chunks) {
    const name = kurzName(chunk.dokument);
    const gruppe = gruppen.get(name) ?? { seiten: [], ids: [] };
    const seite = chunk.seite ? `Seite ${chunk.seite}` : "";
    if (seite && !gruppe.seiten.includes(seite)) gruppe.seiten.push(seite);
    if (chunk.id && !gruppe.ids.includes(chunk.id)) gruppe.ids.push(chunk.id);
    gruppen.set(name, gruppe);
  }
  return [...gruppen].map(([name, gruppe]) => {
    const kopf = gruppe.seiten.length > 0 ? `${name}, ${gruppe.seiten.join(" / ")}` : name;
    if (gruppe.seiten.length > 0 || gruppe.ids.length === 0) return kopf;
    const ids = gruppe.ids.map((id) => id.length > 12 ? id.slice(0, 8) : id).join(", ");
    return `${kopf} · ${ids}`;
  }).join(" / ");
}

export function chunkSignatur(chunks: ChunkBeleg[]): string {
  return chunks
    .map((chunk) => `${chunk.id}|${kurzName(chunk.dokument)}|${chunk.seite ?? ""}`)
    .sort()
    .join(";");
}

export function dokumentbasisWarnung(rows: Array<{ label: string; chunks: ChunkBeleg[] }>): string | null {
  const antworten = rows.filter((row) => row.chunks);
  if (antworten.length < 2) return null;
  const signaturen = new Set(antworten.map((row) => chunkSignatur(row.chunks)));
  if (signaturen.size <= 1) return null;
  const teile = antworten.map((row) => {
    const pruefer = row.label.match(/Prüfer\s+\d+/)?.[0] ?? row.label;
    return `${pruefer} erhielt ${row.chunks.length} Chunks`;
  });
  return `⚠️ Uneinheitliche Dokumentbasis: ${teile.join(", ")} — Retrieval variiert, Konsens verzerrend.`;
}

export function ohneInterneChunks(chunks: ChunkBeleg[]): ChunkBeleg[] {
  return chunks.filter((chunk) => !istInterneQuelle(chunk.dokument) && !istInterneQuelle(chunk.id));
}

function euroZeile(value: number): string {
  if (Number.isInteger(value)) return `${String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ".")} €`;
  return `${value.toFixed(2).replace(".", ",")} €`;
}

export function betraegeImText(chunks: ChunkBeleg[]): string[] {
  const zeilen: string[] = [];
  const gesehen = new Set<string>();
  for (const chunk of chunks) {
    for (const treffer of geldTreffer(chunk.text)) {
      const zeile = `${euroZeile(treffer.value)} in ${kurzName(chunk.dokument)}`;
      if (gesehen.has(zeile)) continue;
      gesehen.add(zeile);
      zeilen.push(zeile);
    }
  }
  return zeilen.slice(0, 20);
}

export function stellenBlock(chunks: ChunkBeleg[]): string {
  const betraege = betraegeImText(chunks);
  const kopf = betraege.length > 0
    ? `## Beträge wörtlich in den Dokumentstellen\n${betraege.map((zeile) => `- ${zeile}`).join("\n")}\n\n`
    : "";
  const teile = chunks.slice(0, 12).map((chunk, index) => {
    const name = [kurzName(chunk.dokument), chunk.seite ? `Seite ${chunk.seite}` : ""].filter(Boolean).join(", ");
    return `### Stelle ${index + 1}: ${name}\n${chunk.text.trim().slice(0, 2500)}`;
  });
  return `${kopf}## Dokumentstellen (identisch für alle Prüfer, vom System abgerufen)\n${teile.join("\n\n")}`;
}
