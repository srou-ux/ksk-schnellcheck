import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { claimNextJob, createCase, getCase, getDb, listJahrespakete } from "../src/lib/db";
import { fuehreVorbereitungAus, holeVorbereitung, starteJahrespaketVorbereitung } from "../src/lib/jahrespaket-vorbereitung";

const mistral = {
  createLibrary: async () => `lib-${crypto.randomUUID()}`,
  upload: async () => ({ fileId: "file-fixture", documentId: `doc-${crypto.randomUUID()}` }),
  processing: async () => ({ status: "Completed" as const }), processingPolls: 1,
};
const quelle = (overrides: Record<string, unknown> = {}) => ({ kategorie:"ksvg",titel:"Amtliche Fassung",url:"https://www.gesetze-im-internet.de/ksvg/",herausgeber:"Bund",dokumentstand:"01.2183",zeitbezug:"Dokumentstand und Anwendung getrennt.",fuerJahrBelegt:false,gueltigAb:null,gueltigBis:null,anwendungStatus:"ungeklaert" as const,...overrides });

describe("automatische Jahrespaket-Vorbereitung",()=>{
  it("legt einen inaktiven Entwurf und getrennten Job an",()=>{const fall=createCase({title:"Bestandsfall",audience:"verein"});const v=starteJahrespaketVorbereitung(2181);expect(listJahrespakete().find((p)=>p.id===v.jahrespaket_id)).toMatchObject({jahr:2181,version:1,status:"entwurf",is_active:0});expect(getCase(fall.id)).toEqual(fall);expect(claimNextJob()).toBeNull();});
  it("verhindert parallele Läufe und setzt denselben Entwurf später fort",async()=>{const first=starteJahrespaketVorbereitung(2182);expect(()=>starteJahrespaketVorbereitung(2182)).toThrow(/bereits/);await fuehreVorbereitungAus(first.id,{...mistral,research:async()=>({luecken:[],quellen:[quelle({dokumentstand:"2182-01",fuerJahrBelegt:true,anwendungStatus:"belegt"})]}),targetedResearch:async()=>({luecken:[],quellen:[]}),download:async(url)=>({bytes:new TextEncoder().encode("fixture-2182"),mimeType:"text/plain",filename:"q.txt",finalUrl:url})});const resumed=starteJahrespaketVorbereitung(2182);expect(resumed.id).toBe(first.id);expect(resumed.jahrespaket_id).toBe(first.jahrespaket_id);expect(listJahrespakete().filter((p)=>p.jahr===2182)).toHaveLength(1);});
  it("archiviert trotz offener Anwendung, normalisiert Monatsstände und indexiert",async()=>{const v=starteJahrespaketVorbereitung(2183);await fuehreVorbereitungAus(v.id,{...mistral,research:async()=>({luecken:[],quellen:[quelle()]}),targetedResearch:async()=>({luecken:[],quellen:[]}),download:async(url)=>({bytes:new TextEncoder().encode("fixture-2183"),mimeType:"text/plain",filename:"ksvg.txt",finalUrl:url})});const result=holeVorbereitung(v.id)!;expect(result.status).toBe("completed");expect(result.quellen?.[0]).toMatchObject({dokumentstand:"2183-01",status:"archiviert",anwendung_status:"ungeklaert",luecken_typ:"zeitliche_anwendung",upload_status:"hochgeladen",verarbeitungsstatus:"Completed"});});
  it("begrenzt identische Nachrecherchen auf drei Versuche",async()=>{const v=starteJahrespaketVorbereitung(2184);let attempts=0;await fuehreVorbereitungAus(v.id,{...mistral,research:async()=>({luecken:["Pflichtquelle fehlt"],quellen:[]}),targetedResearch:async()=>{attempts++;return{luecken:[],quellen:[],kostenUsd:0.01};},download:async()=>{throw new Error("nicht erwartet");}});expect(attempts).toBeGreaterThan(0);expect(attempts).toBeLessThanOrEqual(3*6);const tasks=holeVorbereitung(v.id)!.nachrecherchen!;expect(tasks.every((t)=>t.versuche<=3)).toBe(true);expect(tasks.some((t)=>t.status==="offen_manuell")).toBe(true);});
  it("klassifiziert technische Beschaffungsfehler",async()=>{const v=starteJahrespaketVorbereitung(2185);await fuehreVorbereitungAus(v.id,{...mistral,research:async()=>({luecken:[],quellen:[quelle({dokumentstand:"2185-01",fuerJahrBelegt:true,anwendungStatus:"belegt"})]}),targetedResearch:async()=>({luecken:[],quellen:[]}),download:async()=>{throw new Error("HTTP-Testfehler");}});expect(holeVorbereitung(v.id)!.quellen?.[0]).toMatchObject({status:"fehler",luecken_typ:"technische_beschaffung",fehler:"HTTP-Testfehler"});expect(listJahrespakete().find((p)=>p.id===v.jahrespaket_id)).toMatchObject({status:"entwurf",is_active:0});});
  it("verwendet identische Archivdateien anhand der Prüfsumme wieder",async()=>{const bytes=new TextEncoder().encode("identische-fixture");for(const year of [2186,2187]){const v=starteJahrespaketVorbereitung(year);await fuehreVorbereitungAus(v.id,{...mistral,research:async()=>({luecken:[],quellen:[quelle({url:`https://www.bmas.de/${year}`,dokumentstand:`${year}-01`,fuerJahrBelegt:true,anwendungStatus:"belegt"})]}),targetedResearch:async()=>({luecken:[],quellen:[]}),download:async(url)=>({bytes,mimeType:"text/plain",filename:"gleich.txt",finalUrl:url})});}expect((getDb().prepare("SELECT COUNT(*) n FROM archiv_quellen WHERE sha256=(SELECT sha256 FROM archiv_quellen ORDER BY created_at DESC LIMIT 1)").get() as {n:number}).n).toBe(1);});
});

const mediencenter = `<html><body>
<a href="/fileadmin/Dokumente/Mediencenter_Unternehmer_Verwerter/Informationsschriften/Info_10_Ausnahmen.pdf">Informationsschrift Nr. 10 – Ausnahmen (PDF, 224 KB)</a>
<a href="/fileadmin/Dokumente/Mediencenter_Unternehmer_Verwerter/Informationsschriften/Info_12_Musikvereine.pdf">Informationsschrift Nr. 12 – Musikvereine (PDF, 198 KB)</a>
<a href="/fileadmin/Dokumente/Mediencenter_Unternehmer_Verwerter/Informationsschriften/Info_27_Vermittlung.pdf">Informationsschrift Nr. 27 – Vermittlung (PDF, 215 KB)</a>
<a href="/fileadmin/Dokumente/Mediencenter_Unternehmer_Verwerter/Informationsschriften/Info_06_englische_Version.pdf">Info No. 6 – Artistic (EN, PDF, 175 KB)</a>
<a href="/fileadmin/Dokumente/Mediencenter_Unternehmer_Verwerter/Vordrucke_und_Formulare/Meldebogen.pdf">Meldebogen zur Meldung (PDF, 318 KB)</a>
</body></html>`;
const mediencenterUrl = "https://www.kuenstlersozialkasse.de/service-und-medien/mediencenter-unternehmen-und-verwerter";

describe("Quellenkatalog vor der KI-Auswertung", () => {
  it("erkennt Info 10, 12 und 27 und trennt Formulare sowie Sprachfassungen", async () => {
    const { leseLinkliste } = await import("../src/lib/quellenkatalog-lese");
    const eintraege = leseLinkliste(mediencenter, mediencenterUrl, "Künstlersozialkasse");
    expect(eintraege.filter((item) => item.art === "informationsschrift").map((item) => item.dokumentnummer).sort()).toEqual(["10", "12", "27"]);
    expect(eintraege.find((item) => item.dokumentnummer === "6")?.art).toBe("sprachfassung");
    expect(eintraege.find((item) => item.titel.startsWith("Meldebogen"))?.art).toBe("formular");
    expect(eintraege.every((item) => item.url.startsWith("https://www.kuenstlersozialkasse.de/fileadmin/"))).toBe(true);
  });

  it("behält Monatsstände, archiviert offenen Zeitbezug und gibt den Entwurf nicht frei", async () => {
    const { listJahrespakete } = await import("../src/lib/db");
    const v = starteJahrespaketVorbereitung(2190);
    await fuehreVorbereitungAus(v.id, {
      ...mistral,
      capture: async () => [{ url: mediencenterUrl, html: mediencenter }, { url: "https://www.gesetze-im-internet.de/ksvg/index.html", html: "<html>Gesetz</html>" }, { url: "https://www.gesetze-im-internet.de/ksventgv/BJNR001560991.html", html: "<html>Verordnung</html>" }],
      evaluate: async () => ({ urteile: [{ katalogKey: "informationsschrift:10", anwendungStatus: "ungeklaert", gueltigAb: null, gueltigBis: null, dokumentstand: "01.2026", fundstelle: "Stand im Dokument", zahlen: [], aenderungen: "", luecken: [] }], luecken: [] }),
      targetedResearch: async () => ({ luecken: [], quellen: [] }),
      download: async (url) => ({ bytes: new TextEncoder().encode(`Stand: 01.2026\n${url}`), mimeType: "text/plain", filename: "quelle.txt", finalUrl: url }),
    });
    const result = holeVorbereitung(v.id)!;
    const info = result.quellen?.find((item) => item.titel.includes("Nr. 10"));
    expect(info).toMatchObject({ status: "archiviert", dokumentstand: "2026-01", dokumentstand_art: "monat", anwendung_status: "ungeklaert" });
    expect(info?.luecken_typ).not.toBe("metadaten_fehlen");
    expect(listJahrespakete().find((item) => item.id === v.jahrespaket_id)).toMatchObject({ status: "entwurf", is_active: 0 });
  });

  it("legt bei Wiederholung keine zweiten Archivdateien an und wertet ein anderes Jahr neu aus", async () => {
    let evaluations = 0;
    const bytes = new TextEncoder().encode("Stand: 01.2026\ngleicher-text");
    const run = async (jahr: number) => {
      const v = starteJahrespaketVorbereitung(jahr);
      await fuehreVorbereitungAus(v.id, {
        ...mistral,
        capture: async () => [{ url: mediencenterUrl, html: mediencenter }, { url: "https://www.gesetze-im-internet.de/ksvg/index.html", html: "<html></html>" }, { url: "https://www.gesetze-im-internet.de/ksventgv/BJNR001560991.html", html: "<html></html>" }],
        evaluate: async () => { evaluations += 1; return { urteile: [], luecken: [] }; },
        targetedResearch: async () => ({ luecken: [], quellen: [] }),
        download: async (url) => ({ bytes, mimeType: "text/plain", filename: "gleich.txt", finalUrl: url }),
      });
      return v;
    };
    const first = await run(2191);
    const again = starteJahrespaketVorbereitung(2191);
    expect(again.id).toBe(first.id);
    await fuehreVorbereitungAus(again.id, { ...mistral, capture: async () => { throw new Error("nicht erneut auslesen"); }, evaluate: async () => { evaluations += 1; return { urteile: [], luecken: [] }; }, targetedResearch: async () => ({ luecken: [], quellen: [] }), download: async () => { throw new Error("nicht erneut laden"); } });
    await run(2192);
    expect(evaluations).toBe(2);
    const hash = createHash("sha256").update(bytes).digest("hex");
    expect((getDb().prepare("SELECT COUNT(*) n FROM archiv_quellen WHERE sha256 = ?").get(hash) as { n: number }).n).toBe(1);
  });

  it("meldet einen geänderten Seitenaufbau und löscht vorhandene Katalogeinträge nicht", async () => {
    const { katalogNachKey, merkeKatalog } = await import("../src/lib/quellenkatalog");
    merkeKatalog([{ katalogKey: "informationsschrift:10", art: "informationsschrift", titel: "Info 10 bleibt", url: "https://www.kuenstlersozialkasse.de/fileadmin/alt/Info_10.pdf", dokumentnummer: "10", herausgeber: "Künstlersozialkasse", listenherkunft: "mediencenter" }]);
    const v = starteJahrespaketVorbereitung(2193);
    await fuehreVorbereitungAus(v.id, {
      ...mistral,
      capture: async () => [{ url: mediencenterUrl, html: "<html><body>Wartung</body></html>" }, { url: "https://www.gesetze-im-internet.de/ksvg/index.html", html: null, error: "HTTP 500" }, { url: "https://www.gesetze-im-internet.de/ksventgv/BJNR001560991.html", html: null, error: "HTTP 500" }],
      evaluate: async () => ({ urteile: [], luecken: [] }),
      targetedResearch: async () => ({ luecken: [], quellen: [] }),
      download: async () => { throw new Error("kein Download bei Layoutfehler der Liste"); },
    });
    expect(katalogNachKey("informationsschrift:10")).toMatchObject({ titel: "Info 10 bleibt" });
    expect(holeVorbereitung(v.id)!.nachrecherchen?.some((item) => /Seitenaufbau/.test(item.suchauftrag))).toBe(true);
  });

  it("übernimmt eine aktuelle Fassung nicht ungeprüft in ein historisches Jahr", async () => {
    const v = starteJahrespaketVorbereitung(2010);
    await fuehreVorbereitungAus(v.id, {
      ...mistral,
      capture: async () => [{ url: mediencenterUrl, html: mediencenter }, { url: "https://www.gesetze-im-internet.de/ksvg/index.html", html: "<html></html>" }, { url: "https://www.gesetze-im-internet.de/ksventgv/BJNR001560991.html", html: "<html></html>" }],
      evaluate: async () => ({ urteile: [{ katalogKey: "informationsschrift:10", anwendungStatus: "belegt", gueltigAb: null, gueltigBis: null, dokumentstand: "10.2026", fundstelle: "aktuelle Fassung", zahlen: ["4,9 Prozent"], aenderungen: "keine historischen Nachweise", luecken: [] }], luecken: [] }),
      targetedResearch: async () => ({ luecken: [], quellen: [] }),
      download: async (url) => ({ bytes: new TextEncoder().encode("Stand: 10.2026 aktuelle Gesamtausgabe"), mimeType: "text/plain", filename: "aktuell.txt", finalUrl: url }),
    });
    const info = holeVorbereitung(v.id)!.quellen?.find((item) => item.titel.includes("Nr. 10"));
    expect(info).toMatchObject({ status: "archiviert", anwendung_status: "ungeklaert" });
    expect(listJahrespakete().find((item) => item.id === v.jahrespaket_id)).toMatchObject({ status: "entwurf", is_active: 0 });
  });
});
