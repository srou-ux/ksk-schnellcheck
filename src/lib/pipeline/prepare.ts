import { extractText, getMeta } from "unpdf";

export interface PreparedDocument {
  pageCount: number;
  pages: Array<{ number: number; text: string; hasTextLayer: boolean }>;
  image: { mime: string; base64: string } | null;
  metadata: Record<string, string>;
}

export async function prepareDocument(bytes: Buffer, mime: string): Promise<PreparedDocument> {
  if (mime === "image/png" || mime === "image/jpeg") {
    return {
      pageCount: 1,
      pages: [{ number: 1, text: "", hasTextLayer: false }],
      image: { mime, base64: bytes.toString("base64") },
      metadata: {},
    };
  }
  if (mime !== "application/pdf") {
    throw new Error("Wir konnten die Datei nicht vorbereiten, weil nur PDF, PNG und JPG zugelassen sind.");
  }
  const data = new Uint8Array(bytes);
  const extracted = await extractText(data, { mergePages: false });
  const texts = Array.isArray(extracted.text) ? extracted.text : [extracted.text];
  let metadata: Record<string, string> = {};
  try {
    const meta = await getMeta(data);
    metadata = Object.fromEntries(Object.entries(meta.info ?? {}).map(([key, value]) => [key, String(value)]));
  } catch {
    metadata = {};
  }
  return {
    pageCount: extracted.totalPages,
    pages: texts.map((text, index) => ({
      number: index + 1,
      text: text ?? "",
      hasTextLayer: (text ?? "").trim().length >= 20,
    })),
    image: null,
    metadata,
  };
}
