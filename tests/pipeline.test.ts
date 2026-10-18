import { beforeAll, describe, expect, it } from "vitest";
import { stelleTestSaetzeFrei } from "./berechnungsfreigabe";
import { addDocument, createCase, createRun, deleteCaseFully, getCase, getDb, getReportByCase } from "@/lib/db";
import { dataDir } from "@/lib/config";
import { createLocalStorage } from "@/lib/storage";
import { createMockLlm } from "@/lib/llm/mock";
import { runSaasKiKernel } from "@/lib/saas-ki-kernel";

const marker = `---KSK-FELDER---
jahr: 2025
rolle: typischer_verwerter
empfaengerart: natuerliche_person
jahressumme: ja
summe_netto: 1000000
position: Honorar|honorar|wort|1000000
---ENDE---`;

function pdfWithText(lines: string[]): Buffer {
  const content = lines.map((line, index) => `BT /F1 12 Tf 72 ${740 - index * 16} Td (${line.replace(/[()\\]/g, "\\$&")}) Tj ET`).join("\n");
  const objects = [
    "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
    "2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n",
    "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n",
    `4 0 obj<</Length ${Buffer.byteLength(content)}>>stream\n${content}\nendstream\nendobj\n`,
    "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n",
  ];
  let out = "%PDF-1.4\n";
  const offsets = [0];
  for (const object of objects) {
    offsets.push(Buffer.byteLength(out));
    out += object;
  }
  const xref = Buffer.byteLength(out);
  out += `xref\n0 ${objects.length + 1}\n`;
  out += "0000000000 65535 f \n";
  for (let index = 1; index < offsets.length; index += 1) {
    out += `${String(offsets[index]).padStart(10, "0")} 00000 n \n`;
  }
  out += `trailer<</Size ${objects.length + 1}/Root 1 0 R>>\nstartxref\n${xref}\n%%EOF`;
  return Buffer.from(out, "latin1");
}

async function storeCase(title: string, text: string) {
  const item = createCase({ title, audience: "verein" });
  const id = crypto.randomUUID();
  const key = `cases/${item.id}/${id}`;
  await createLocalStorage(`${dataDir()}/storage`).put(key, pdfWithText(text.split("\n")));
  addDocument({
    id,
    case_id: item.id,
    kind: "rechnung",
    storage_key: key,
    original_name: "rechnung.pdf",
    mime_type: "application/pdf",
    size_bytes: 100,
  });
  const run = createRun({
    caseId: item.id,
    methodologyVersion: "v12",
    libraryId: null,
    libraryVersion: null,
    readingMode: "mock",
  });
  return { item, run };
}

beforeAll(() => {
  stelleTestSaetzeFrei();
});

describe("Pipeline", () => {
  it("schreibt einen eingefrorenen Bericht und löscht den Fall vollständig", async () => {
    const { item, run } = await storeCase("Pipeline 5 Prozent", marker);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm() });
    const report = getReportByCase(item.id);
    expect(report?.methodology_version).toBe("v12");
    const payload = JSON.parse(report!.payload_json) as { totalLevyCents: number; methodologyVersion: string; registerIds?: string[]; registerSnapshot?: unknown[] };
    expect(payload.totalLevyCents).toBe(50_000);
    expect(payload.methodologyVersion).toBe("v12");
    expect(payload.registerIds).toHaveLength(2);
    expect(payload.registerSnapshot).toHaveLength(2);
    const gespeichert = report as { register_snapshot_json?: string | null };
    expect(gespeichert.register_snapshot_json).toContain("abgabesatz");
    const paket = getDb().prepare("SELECT payload_json, temporary FROM stage_artifacts WHERE run_id = ? AND stage = 'paket'").get(run.id) as { payload_json: string; temporary: number };
    expect(paket.temporary).toBe(0);
    expect(JSON.parse(paket.payload_json).version).toBe("v12");
    await deleteCaseFully(item.id, (key) => createLocalStorage(`${dataDir()}/storage`).delete(key));
    expect(getCase(item.id)).toBeNull();
    expect(getReportByCase(item.id)).toBeNull();
  });

  it("stoppt ohne Bericht, wenn der Prüfer widerspricht", async () => {
    const { item, run } = await storeCase("Widerspruch", marker);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm({ examinerConsistent: false }) });
    expect(getReportByCase(item.id)).toBeNull();
  });

  it("stoppt ohne Bericht bei einem Summenfehler", async () => {
    const broken = `---KSK-FELDER---
jahr: 2025
rolle: typischer_verwerter
empfaengerart: natuerliche_person
jahressumme: ja
summe_netto: 35000
position: A|honorar|wort|10000
position: B|honorar|musik|20000
---ENDE---`;
    const { item, run } = await storeCase("Summe", broken);
    await runSaasKiKernel({ auftrag: "fall", runId: run.id, client: createMockLlm() });
    expect(getReportByCase(item.id)).toBeNull();
  });
});
