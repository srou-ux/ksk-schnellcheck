function cleanLine(line: string): string {
  return line.replace(/^[-*•\d.)\s]+/, "").replace(/\*+/g, "").replace(/__/g, "").trim();
}

function firstString(record: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

export function formatCitation(item: unknown): string {
  if (typeof item === "string") return cleanLine(item);
  if (!item || typeof item !== "object") return "";
  const record = item as Record<string, unknown>;
  const nested = record.document ?? record.source ?? record.file;
  const nestedName = nested && typeof nested === "object"
    ? firstString(nested as Record<string, unknown>, ["name", "title", "filename", "file_name", "document_name"])
    : "";
  const name = firstString(record, ["document_name", "documentName", "filename", "file_name", "fileName", "title", "name", "source"]) || nestedName;
  if (!name) return "";
  const section = firstString(record, ["section", "abschnitt", "heading"]);
  const page = record.page ?? record.page_number ?? record.pageNumber;
  if (section) return `${name}, Abschnitt ${section}`;
  if (typeof page === "number" || (typeof page === "string" && page.trim())) return `${name}, Seite ${page}`;
  return name;
}

export function citationsFromResponse(value: unknown, found: string[] = [], depth = 0): string[] {
  if (depth > 8 || value == null) return found;
  if (Array.isArray(value)) {
    for (const item of value) citationsFromResponse(item, found, depth + 1);
    return found;
  }
  if (typeof value !== "object") return found;
  const record = value as Record<string, unknown>;
  if (Array.isArray(record.citations)) {
    for (const item of record.citations) {
      const label = formatCitation(item);
      if (label) found.push(label);
    }
  }
  for (const [key, nested] of Object.entries(record)) {
    if (key === "citations") continue;
    if (nested && typeof nested === "object") citationsFromResponse(nested, found, depth + 1);
  }
  return found;
}

function inlineFundstellen(answer: string): string[] {
  return [...answer.matchAll(/Fundstelle[n]?\s*:\s*([^)\n]+)/gi)]
    .map((match) => cleanLine(match[1] ?? ""))
    .filter((line) => line.length > 1 && !/^keine\b/i.test(line));
}

export function fundstellenFromAnswer(answer: string): string[] {
  const match = answer.match(/(?:^|\n)\s*(?:\*\*|__)?Fundstellen?(?:\*\*|__)?\s*:?\s*([\s\S]*)$/i);
  const fromSection = match?.[1]
    ? match[1]
      .split(/\n+/)
      .flatMap((line) => line.split(/\s*;\s*/))
      .map(cleanLine)
      .filter((line) => line.length > 1 && !/^keine\b/i.test(line))
    : [];
  const lines = fromSection.length > 0 ? fromSection : inlineFundstellen(answer);
  return [...new Set(lines)];
}

export function visibleFundstellen(answer: string, sources: string[]): string[] {
  const structured = sources.map((item) => item.trim()).filter(Boolean);
  const lines = structured.length > 0 ? structured : fundstellenFromAnswer(answer);
  return [...new Set(lines)];
}
