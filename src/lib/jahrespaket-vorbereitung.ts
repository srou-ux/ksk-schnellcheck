import { lookup } from "node:dns/promises";
import { existsSync, readFileSync } from "node:fs";
import { isIP } from "node:net";
import path from "node:path";
import OpenAI from "openai";
import requirements from "../../config/ksk-quellenanforderungen-v1.json";
import { appConfig, dataDir } from "@/lib/config";
import { getDb } from "@/lib/db";
import { createRemoteLibrary, fetchDocumentMeta, uploadReferenceFile } from "@/lib/mistral/libraries";
import { aktualisiereVerarbeitungsstatus, archiviereOriginal, erzeugeIndexmanifest, ordneArchivquelleZu, ordnePaketBibliothekZu, protokolliereMistralUpload, protokolliereRagPruefung } from "@/lib/paket-quellen";
import { ausgangsquellen, ergaenzeGesetzestexte, festeEinstiege, katalogNachKey, merkeKatalog, setzeKatalogArchiv } from "@/lib/quellenkatalog";
import { anwendungFuerJahr, htmlText, leseDokumentstand, leseLinkliste, mediencenterLayout, standAusText, type AnwendungStatus } from "@/lib/quellenkatalog-lese";

export type { AnwendungStatus } from "@/lib/quellenkatalog-lese";
export type LueckenTyp = "technische_beschaffung" | "metadaten_fehlen" | "zeitliche_anwendung" | "fachlicher_widerspruch" | "quelle_fehlt";
export type QuellenFund = {
  kategorie: string; titel: string; url: string; herausgeber: string;
  dokumentstand: string | null; zeitbezug: string; fuerJahrBelegt: boolean;
  gueltigAb?: string | null; gueltigBis?: string | null; anwendungStatus?: AnwendungStatus;
};
export type RechercheErgebnis = { quellen: QuellenFund[]; luecken: string[]; kostenUsd?: number };
export type QuellenFundStatus = QuellenFund & {
  id: string; status: string; archiv_quelle_id: string | null; paket_quelle_id: string | null;
  luecken_typ: LueckenTyp | null; fehler: string | null; upload_status?: string | null; verarbeitungsstatus?: string | null;
};
export type NachrechercheStatus = {
  id: string; aufgabe_key: string; kategorie: string; typ: LueckenTyp; suchauftrag: string;
  status: string; versuche: number; max_versuche: number; ergebnis_json: string | null; fehler: string | null; kosten_usd: number;
};
export type VorbereitungStatus = {
  id: string; jahrespaket_id: string; jahr: number; anforderung_version: string; status: string;
  schritt: string; fortschritt: number; modell: string; prompt_version: string; luecken_json: string;
  kostenlimit_usd: number; kosten_usd: number; fehler: string | null; created_at: string; updated_at: string;
  completed_at: string | null; quellen?: QuellenFundStatus[]; nachrecherchen?: NachrechercheStatus[];
};

type Download = { bytes: Uint8Array; mimeType: string; filename: string; finalUrl: string };
type ErfassteSeite = { url: string; html: string | null; error?: string };
type DokumentUrteil = {
  katalogKey: string; anwendungStatus: AnwendungStatus; gueltigAb: string | null; gueltigBis: string | null;
  dokumentstand: string | null; fundstelle: string; zahlen: string[]; aenderungen: string; luecken: string[];
};
type AuswertungErgebnis = { urteile: DokumentUrteil[]; luecken: string[]; kostenUsd?: number };
type Dependencies = {
  research?: (jahr: number) => Promise<RechercheErgebnis>;
  capture?: () => Promise<ErfassteSeite[]>;
  evaluate?: (input: { jahr: number; dokumente: Array<{ katalogKey: string; titel: string; text: string }> }) => Promise<AuswertungErgebnis>;
  targetedResearch?: (jahr: number, aufgabe: NachrechercheStatus) => Promise<RechercheErgebnis>;
  download?: (url: string) => Promise<Download>;
  createLibrary?: (name: string, description: string) => Promise<string>;
  upload?: (input: { libraryId: string; filename: string; bytes: Buffer; mime: string }) => Promise<{ fileId: string | null; documentId: string }>;
  processing?: (libraryId: string, documentId: string) => Promise<{ status: "Running" | "Completed" | "Fehler" }>;
  processingPolls?: number;
  ragVerify?: (input: { paketId: string; libraryId: string; documents: Array<{ paketQuelleId: string; documentId: string }> }) => Promise<{ modell: string; positiveReferenzen: string[]; trennungReferenzen: string[]; positivBestanden: boolean; trennungBestanden: boolean; ergebnis: unknown }>;
};

const terminalProcessing = new Set(["completed", "failed"]);
const ACTIVE = ["queued", "running"];
const REQUIRED = new Set(requirements.umfang.filter((item) => item.pflicht).map((item) => item.id));
const now = () => new Date().toISOString();
const modelName = () => process.env.OPENAI_RESEARCH_MODEL?.trim() || "gpt-6-astra";

function preparationRow(id: string): VorbereitungStatus | null {
  return (getDb().prepare("SELECT * FROM jahrespaket_vorbereitungen WHERE id = ?").get(id) as unknown as VorbereitungStatus | undefined) ?? null;
}

export function holeVorbereitung(id: string): VorbereitungStatus | null {
  const row = preparationRow(id);
  if (!row) return null;
  const quellen = getDb().prepare(`SELECT f.*,
      (SELECT z.upload_status FROM jahrespaket_mistral_zuordnungen z WHERE z.jahrespaket_quelle_id=f.paket_quelle_id ORDER BY z.created_at DESC LIMIT 1) upload_status,
      (SELECT z.verarbeitungsstatus FROM jahrespaket_mistral_zuordnungen z WHERE z.jahrespaket_quelle_id=f.paket_quelle_id ORDER BY z.created_at DESC LIMIT 1) verarbeitungsstatus
    FROM jahrespaket_quellenfunde f WHERE f.vorbereitung_id=? ORDER BY f.created_at`).all(id) as unknown as QuellenFundStatus[];
  const nachrecherchen = getDb().prepare("SELECT * FROM jahrespaket_nachrecherchen WHERE vorbereitung_id = ? ORDER BY created_at").all(id) as unknown as NachrechercheStatus[];
  return { ...row, quellen, nachrecherchen };
}

export function letzteVorbereitungen(): VorbereitungStatus[] {
  return (getDb().prepare("SELECT id FROM jahrespaket_vorbereitungen ORDER BY created_at DESC LIMIT 20").all() as Array<{ id: string }>).map((row) => holeVorbereitung(row.id)!);
}

function enqueue(preparationId: string, stamp: string): void {
  getDb().prepare(`INSERT INTO jobs (id, type, payload_json, status, attempts, error, created_at, locked_at, finished_at)
    VALUES (?, 'jahrespaket_vorbereitung', ?, 'queued', 0, NULL, ?, NULL, NULL)`).run(crypto.randomUUID(), JSON.stringify({ preparationId }), stamp);
}

export function starteJahrespaketVorbereitung(jahr: number): VorbereitungStatus {
  if (!Number.isSafeInteger(jahr) || jahr < 1983 || jahr > 2200) throw new Error("Das Vorbereitungsjahr ist ungültig.");
  const db = getDb(); const stamp = now();
  db.exec("BEGIN IMMEDIATE");
  try {
    const active = db.prepare("SELECT id FROM jahrespaket_vorbereitungen WHERE jahr = ? AND status IN ('queued','running')").get(jahr);
    if (active) throw new Error(`Für ${jahr} läuft bereits eine Vorbereitung.`);
    const reusable = db.prepare(`SELECT v.id FROM jahrespaket_vorbereitungen v JOIN jahrespakete p ON p.id=v.jahrespaket_id
      WHERE v.jahr=? AND p.status='entwurf' ORDER BY v.created_at DESC LIMIT 1`).get(jahr) as { id: string } | undefined;
    if (reusable) {
      db.prepare("UPDATE jahrespaket_vorbereitungen SET status='queued', schritt='Fortsetzung wartet', fortschritt=0, fehler=NULL, completed_at=NULL, updated_at=? WHERE id=?").run(stamp, reusable.id);
      enqueue(reusable.id, stamp); db.exec("COMMIT"); return holeVorbereitung(reusable.id)!;
    }
    const paketId=crypto.randomUUID(), id=crypto.randomUUID();
    const versionRow=db.prepare("SELECT MAX(version) AS version FROM jahrespakete WHERE jahr=?").get(jahr) as { version:number|null };
    db.prepare(`INSERT INTO jahrespakete (id,jahr,version,status,methodology_version,rules_stamp,content_hash,pruefer_name,freigabe_kommentar,freigegeben_am,is_active,created_at)
      VALUES (?,?,?,'entwurf',?,?,NULL,NULL,NULL,NULL,0,?)`).run(paketId,jahr,(versionRow.version??0)+1,appConfig().methodologyVersion,appConfig().rulesStamp,stamp);
    db.prepare(`INSERT INTO jahrespaket_vorbereitungen (id,jahrespaket_id,jahr,anforderung_version,status,schritt,fortschritt,modell,prompt_version,luecken_json,fehler,created_at,updated_at,completed_at,kostenlimit_usd,kosten_usd)
      VALUES (?,?,?,?,'queued','wartet',0,?,?,'[]',NULL,?,?,NULL,?,0)`).run(id,paketId,jahr,requirements.version,modelName(),requirements.prompt_version,stamp,stamp,requirements.kostenlimit_usd);
    enqueue(id,stamp); db.exec("COMMIT"); return holeVorbereitung(id)!;
  } catch(error) { db.exec("ROLLBACK"); throw error; }
}

function updatePreparation(id:string, patch:{status?:string;schritt?:string;fortschritt?:number;luecken?:string[];fehler?:string|null;completed?:boolean;addCost?:number}) {
  const current=preparationRow(id); if(!current) throw new Error("Die Vorbereitung existiert nicht.");
  getDb().prepare(`UPDATE jahrespaket_vorbereitungen SET status=?,schritt=?,fortschritt=?,luecken_json=?,fehler=?,kosten_usd=?,updated_at=?,completed_at=? WHERE id=?`).run(
    patch.status??current.status,patch.schritt??current.schritt,patch.fortschritt??current.fortschritt,patch.luecken?JSON.stringify(patch.luecken):current.luecken_json,
    patch.fehler===undefined?current.fehler:patch.fehler,current.kosten_usd+(patch.addCost??0),now(),patch.completed?now():current.completed_at,id);
}

function responseSchema() { return { type:"object",additionalProperties:false,required:["quellen","luecken"],properties:{quellen:{type:"array",maxItems:requirements.max_quellen,items:{type:"object",additionalProperties:false,required:["kategorie","titel","url","herausgeber","dokumentstand","zeitbezug","fuerJahrBelegt","gueltigAb","gueltigBis","anwendungStatus"],properties:{kategorie:{type:"string"},titel:{type:"string"},url:{type:"string"},herausgeber:{type:"string"},dokumentstand:{type:["string","null"]},zeitbezug:{type:"string"},fuerJahrBelegt:{type:"boolean"},gueltigAb:{type:["string","null"]},gueltigBis:{type:["string","null"]},anwendungStatus:{type:"string",enum:["belegt","ungeklaert","widerspruch"]}}}},luecken:{type:"array",items:{type:"string"}}} } as const; }
function normalizeUrl(raw:string):string|null { try { const u=new URL(raw);u.hash="";return u.toString().replace(/\/$/,""); } catch{return null;} }
function toolUrls(output:unknown):Set<string>{const out=new Set<string>();const visit=(v:unknown):void=>{if(!v||typeof v!=="object")return;if(Array.isArray(v)){v.forEach(visit);return;}for(const[k,x]of Object.entries(v as Record<string,unknown>)){if(k==="url"&&typeof x==="string"){const n=normalizeUrl(x);if(n)out.add(n);}else visit(x);}};visit(output);return out;}
function webCalls(output:unknown):number { return Array.isArray(output)?output.filter((item)=>item&&typeof item==="object"&&(item as {type?:string}).type==="web_search_call").length:0; }
function estimateCost(response:OpenAI.Responses.Response,followup=false):number { const usage=response.usage;const input=followup?requirements.kostenmodell.nachrecherche_input_usd_pro_million:requirements.kostenmodell.input_usd_pro_million;const output=followup?requirements.kostenmodell.nachrecherche_output_usd_pro_million:requirements.kostenmodell.output_usd_pro_million;return ((usage?.input_tokens??0)/1e6)*input+((usage?.output_tokens??0)/1e6)*output+webCalls(response.output)*requirements.kostenmodell.websuche_usd_pro_aufruf; }
function normalizeStand(value:string|null):string|null { if(!value)return null;const v=value.trim();let m=v.match(/^(0[1-9]|1[0-2])\.(\d{4})$/);if(m)return `${m[2]}-${m[1]}`;m=v.match(/^(\d{4})-(0[1-9]|1[0-2])(?:-([0-3]\d))?$/);return m?v:null; }

async function openAiResearch(jahr:number,auftrag:string,followup=false):Promise<RechercheErgebnis>{
  if(!process.env.OPENAI_API_KEY)throw new Error("OPENAI_API_KEY ist serverseitig nicht konfiguriert.");
  const client=new OpenAI({apiKey:process.env.OPENAI_API_KEY,timeout:followup?45_000:120_000,maxRetries:followup?0:2});
  const request:OpenAI.Responses.ResponseCreateParamsNonStreaming&{max_tool_calls:number}={model:followup?requirements.nachrecherche_modell:modelName(),store:false,max_output_tokens:followup?4000:8000,max_tool_calls:followup?4:6,tools:[{type:"web_search",external_web_access:true,search_context_size:"high",filters:{allowed_domains:requirements.offizielle_domains}}],include:["web_search_call.action.sources"],input:[{role:"system",content:"Recherchiere ausschließlich öffentliche amtliche KSK-Rechtsquellen. Dokumentstand (Publikations-/Fassungsstand) und rechtliche Gültigkeit sind getrennte Angaben. Erfinde weder URL noch Gültigkeit. Monatsstände dürfen MM.YYYY oder YYYY-MM sein."},{role:"user",content:`Kalenderjahr ${jahr}. ${auftrag}`}],text:{format:{type:"json_schema",name:"ksk_jahresquellen",strict:true,schema:responseSchema()}}};
  const response=await client.responses.create(request);const parsed=JSON.parse(response.output_text) as RechercheErgebnis;if(!Array.isArray(parsed.quellen)||!Array.isArray(parsed.luecken))throw new Error("OpenAI lieferte kein gültiges Rechercheergebnis.");
  const proven=toolUrls(response.output);for(const source of parsed.quellen){source.dokumentstand=normalizeStand(source.dokumentstand);const n=normalizeUrl(source.url);if(!n||!proven.has(n)){source.fuerJahrBelegt=false;source.anwendungStatus="ungeklaert";parsed.luecken.push(`${source.titel}: URL nicht durch die ausgeführte Websuche nachgewiesen.`);}}
  parsed.kostenUsd=estimateCost(response,followup);return parsed;
}
export function recherchiereOffizielleQuellen(jahr:number){const scope=requirements.umfang.map((i)=>`- ${i.id}: ${i.label}`).join("\n");return openAiResearch(jahr,`Finde direkt abrufbare amtliche Originalquellen für:\n${scope}`);}
async function targeted(jahr:number,task:NachrechercheStatus){return openAiResearch(jahr,`Gezielte Nachrecherche, nur zu dieser offenen Aufgabe: ${task.suchauftrag}. Kategorie: ${task.kategorie}. Liefere nur neue oder präzisierende amtliche Belege.`,true);}

function privateAddress(address:string):boolean{if(isIP(address)===4){const o=address.split(".").map(Number);return o[0]===10||o[0]===127||o[0]===0||(o[0]===169&&o[1]===254)||(o[0]===172&&o[1]>=16&&o[1]<=31)||(o[0]===192&&o[1]===168);}const n=address.toLowerCase();return n==="::1"||n.startsWith("fe80:")||n.startsWith("fc")||n.startsWith("fd");}
function domainAllowed(host:string){const h=host.toLowerCase().replace(/\.$/,"");return requirements.offizielle_domains.some((d)=>h===d||h.endsWith(`.${d}`));}
async function validateUrl(raw:string){const u=new URL(raw);if(u.protocol!=="https:"||u.username||u.password||!domainAllowed(u.hostname))throw new Error("Quelle liegt nicht auf einer erlaubten offiziellen HTTPS-Domain.");const addresses=await lookup(u.hostname,{all:true});if(!addresses.length||addresses.some((a)=>privateAddress(a.address)))throw new Error("Quelladresse verweist auf ein lokales oder internes Netz.");return u;}
export async function ladeOffizielleQuelle(raw:string):Promise<Download>{let url=await validateUrl(raw);for(let redirect=0;redirect<=5;redirect++){const response=await fetch(url,{redirect:"manual",signal:AbortSignal.timeout(45_000),headers:{"User-Agent":"KSK-SaaS-Quellenarchiv/1.0"}});if(response.status>=300&&response.status<400){const location=response.headers.get("location");if(!location)throw new Error("Weiterleitung ohne Ziel.");url=await validateUrl(new URL(location,url).toString());continue;}if(!response.ok)throw new Error(`Download fehlgeschlagen (HTTP ${response.status}).`);const mime=(response.headers.get("content-type")??"").split(";")[0].toLowerCase();if(!new Set(["application/pdf","text/html","text/plain","application/xhtml+xml"]).has(mime))throw new Error(`Nicht erlaubter Dateityp: ${mime||"unbekannt"}.`);const bytes=new Uint8Array(await response.arrayBuffer());if(!bytes.length||bytes.length>requirements.max_download_bytes)throw new Error("Quelldatei ist leer oder zu groß.");return{bytes,mimeType:mime,filename:decodeURIComponent(path.basename(url.pathname))||`quelle-${crypto.randomUUID()}.${mime==="application/pdf"?"pdf":"html"}`,finalUrl:url.toString()};}throw new Error("Zu viele Weiterleitungen.");}

function upsertFinding(prep:VorbereitungStatus,source:QuellenFund):string{const existing=getDb().prepare("SELECT id FROM jahrespaket_quellenfunde WHERE vorbereitung_id=? AND url=?").get(prep.id,source.url) as {id:string}|undefined;const stand=normalizeStand(source.dokumentstand);const art=stand?.length===7?"monat":stand?"tag":null;const app=source.anwendungStatus??(source.fuerJahrBelegt?"belegt":"ungeklaert");if(existing){getDb().prepare(`UPDATE jahrespaket_quellenfunde SET herausgeber=?,dokumentstand=COALESCE(?,dokumentstand),dokumentstand_art=COALESCE(?,dokumentstand_art),zeitbezug=?,gueltig_ab=?,gueltig_bis=?,anwendung_status=?,updated_at=? WHERE id=?`).run(source.herausgeber||null,stand,art,source.zeitbezug,source.gueltigAb??null,source.gueltigBis??null,app,now(),existing.id);return existing.id;}const id=crypto.randomUUID(),stamp=now();getDb().prepare(`INSERT INTO jahrespaket_quellenfunde (id,vorbereitung_id,jahrespaket_id,kategorie,titel,url,herausgeber,dokumentstand,zeitbezug,status,archiv_quelle_id,fehler,created_at,updated_at,dokumentstand_art,gueltig_ab,gueltig_bis,anwendung_status,luecken_typ,paket_quelle_id) VALUES (?,?,?,?,?,?,?,?,?,'gefunden',NULL,NULL,?,?,?,?,?,?,NULL,NULL)`).run(id,prep.id,prep.jahrespaket_id,source.kategorie,source.titel,source.url,source.herausgeber||null,stand,source.zeitbezug,stamp,stamp,art,source.gueltigAb??null,source.gueltigBis??null,app);return id;}
function task(prepId:string,key:string,kategorie:string,typ:LueckenTyp,auftrag:string){const stamp=now();getDb().prepare(`INSERT OR IGNORE INTO jahrespaket_nachrecherchen (id,vorbereitung_id,aufgabe_key,kategorie,typ,suchauftrag,status,versuche,max_versuche,ergebnis_json,fehler,kosten_usd,created_at,updated_at) VALUES (?,?,?,?,?,?,'offen',0,?,NULL,NULL,0,?,?)`).run(crypto.randomUUID(),prepId,key,kategorie,typ,auftrag,requirements.max_nachrecherche_versuche,stamp,stamp);}

function istKonkreteLuecke(text: string): boolean {
  const value = text.trim();
  if (!value || /noch zukünftig|abschließende Bestätigung.*nicht möglich|bedeutet hier|keine eigenständige Rechtsnorm/i.test(value)) return false;
  return /fehlt|fehlend|nicht (?:abschließend )?(?:ermittelt|verifiziert|belegt|abgerufen)|ungeklärt|widerspruch|Prüfumfang.*nicht näher definiert/i.test(value);
}

function urteilOffen(urteil: DokumentUrteil): string[] {
  const text = `${urteil.fundstelle} ${urteil.aenderungen}`;
  const caveat = /nicht (?:gesondert |abschließend )?(?:verifiziert|geprüft|belegt|nachgewiesen)|darf nicht .* übertragen|offen|ungeklärt/i.test(text)
    ? ["Die Auswertung enthält selbst einen offenen zeitlichen Vorbehalt."] : [];
  return [...urteil.luecken.filter((item) => item.trim()), ...caveat];
}

async function archiveSource(prep:VorbereitungStatus,source:QuellenFund,findingId:string,download:(u:string)=>Promise<Download>):Promise<boolean>{try{const file=await download(source.url);const stand=normalizeStand(source.dokumentstand)??new Date().toISOString().slice(0,7);const archive=archiviereOriginal({bytes:file.bytes,originalName:file.filename,mimeType:file.mimeType,herkunft:file.finalUrl,dokumentstand:stand,abrufdatum:new Date().toISOString().slice(0,10)});const paketQuelleId=ordneArchivquelleZu(prep.jahrespaket_id,archive.id);const ltype=!source.dokumentstand?"metadaten_fehlen":(source.anwendungStatus??(source.fuerJahrBelegt?"belegt":"ungeklaert"))==="widerspruch"?"fachlicher_widerspruch":source.fuerJahrBelegt?null:"zeitliche_anwendung";getDb().prepare("UPDATE jahrespaket_quellenfunde SET url=?,status='archiviert',archiv_quelle_id=?,paket_quelle_id=?,luecken_typ=?,fehler=NULL,updated_at=? WHERE id=?").run(file.finalUrl,archive.id,paketQuelleId,ltype,now(),findingId);if(ltype&&ltype!=="fachlicher_widerspruch")task(prep.id,`${ltype}:${source.kategorie}:${archive.sha256}`,source.kategorie,ltype,ltype==="metadaten_fehlen"?`Ermittle den amtlichen Dokumentstand für ${source.titel}.`:`Kläre die rechtliche Anwendbarkeit von ${source.titel} für ${prep.jahr}.`);return true;}catch(error){const message=error instanceof Error?error.message:"Beschaffung fehlgeschlagen.";getDb().prepare("UPDATE jahrespaket_quellenfunde SET status='fehler',luecken_typ='technische_beschaffung',fehler=?,updated_at=? WHERE id=?").run(message,now(),findingId);task(prep.id,`beschaffung:${source.kategorie}:${normalizeUrl(source.url)}`,source.kategorie,"technische_beschaffung",`Finde eine direkt abrufbare amtliche Ersatzfundstelle für ${source.titel}. Fehler: ${message}`);return false;}}

async function ensureMistral(prep:VorbereitungStatus,deps:Dependencies):Promise<{indexed:number;errors:string[]}>{const create=deps.createLibrary??createRemoteLibrary,upload=deps.upload??uploadReferenceFile,processing=deps.processing??fetchDocumentMeta;let library=getDb().prepare("SELECT mistral_library_id FROM jahrespaket_bibliotheken WHERE jahrespaket_id=?").get(prep.jahrespaket_id) as {mistral_library_id:string}|undefined;if(!library){const id=await create(`KSK ${prep.jahr} ${prep.jahrespaket_id.slice(0,8)}`,`Entwurfs-Library für Jahrespaket ${prep.jahr}`);library={mistral_library_id:ordnePaketBibliothekZu(prep.jahrespaket_id,id).mistral_library_id};}const rows=getDb().prepare(`SELECT q.id paketQuelleId,a.* FROM jahrespaket_quellen q JOIN archiv_quellen a ON a.id=q.archiv_quelle_id WHERE q.jahrespaket_id=?`).all(prep.jahrespaket_id) as Array<{paketQuelleId:string;id:string;dateipfad:string;sha256:string;original_name:string;mime_type:string}>;let indexed=0;const errors:string[]=[];for(const row of rows){const mapped=getDb().prepare(`SELECT id,verarbeitungsstatus FROM jahrespaket_mistral_zuordnungen WHERE jahrespaket_quelle_id=? AND mistral_document_hash=? ORDER BY created_at DESC LIMIT 1`).get(row.paketQuelleId,row.sha256) as {id:string;verarbeitungsstatus:string}|undefined;if(mapped&&mapped.verarbeitungsstatus.toLowerCase()==="completed"){indexed++;continue;}try{const absolute=path.join(dataDir(),row.dateipfad);if(!existsSync(absolute))throw new Error("Archivdatei fehlt.");const remote=await upload({libraryId:library.mistral_library_id,filename:row.original_name,bytes:readFileSync(absolute),mime:row.mime_type});const mapping=protokolliereMistralUpload({paketQuelleId:row.paketQuelleId,mistralLibraryId:library.mistral_library_id,mistralDocumentId:remote.documentId,uploadStatus:"hochgeladen",verarbeitungsstatus:"Running",mistralDocumentHash:row.sha256});let state:"Running"|"Completed"|"Fehler"="Running";for(let i=0;i<(deps.processingPolls??8)&&state==="Running";i++){if(i)await new Promise((resolve)=>setTimeout(resolve,1500));state=(await processing(library.mistral_library_id,remote.documentId)).status;}aktualisiereVerarbeitungsstatus({zuordnungId:mapping.id,status:state,fehler:state==="Completed"?null:"Mistral-Verarbeitung nicht erfolgreich abgeschlossen.",mistralDocumentHash:row.sha256});if(state==="Completed")indexed++;else errors.push(`${row.original_name}: Verarbeitung ${state}`);}catch(error){const message=error instanceof Error?error.message:"Mistral-Upload fehlgeschlagen.";protokolliereMistralUpload({paketQuelleId:row.paketQuelleId,mistralLibraryId:library.mistral_library_id,mistralDocumentId:null,uploadStatus:"fehlgeschlagen",verarbeitungsstatus:"Fehler",mistralDocumentHash:row.sha256,fehler:message});errors.push(`${row.original_name}: ${message}`);}}return{indexed,errors};}

async function runRetries(prep:VorbereitungStatus,deps:Dependencies,download:(u:string)=>Promise<Download>){const research=deps.targetedResearch??targeted;const deadline=Date.now()+requirements.nachrecherche_zeitlimit_ms;for(;;){const current=preparationRow(prep.id)!;if(Date.now()>deadline){getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status='offen_manuell',fehler='Zeitlimit der Nachrecherche erreicht. Bisherige Archive bleiben erhalten.',updated_at=? WHERE vorbereitung_id=? AND status='offen'").run(now(),prep.id);break;}if(current.kosten_usd+requirements.max_kosten_pro_recherche_usd>current.kostenlimit_usd)break;const item=getDb().prepare("SELECT * FROM jahrespaket_nachrecherchen WHERE vorbereitung_id=? AND status='offen' AND versuche<max_versuche ORDER BY created_at LIMIT 1").get(prep.id) as unknown as NachrechercheStatus|undefined;if(!item)break;getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status='laeuft',versuche=versuche+1,updated_at=? WHERE id=?").run(now(),item.id);try{const result=await research(prep.jahr,item);const cost=result.kostenUsd??0;updatePreparation(prep.id,{addCost:cost});let archived=0;for(const source of result.quellen){const id=upsertFinding(prep,source);if(await archiveSource(prep,source,id,download))archived++;}const solved=archived>0;getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status=?,ergebnis_json=?,fehler=?,kosten_usd=kosten_usd+?,updated_at=? WHERE id=?").run(solved?"geloest":item.versuche+1>=item.max_versuche?"offen_manuell":"offen",JSON.stringify(result),solved?null:"Kein neuer archivierbarer Beleg.",cost,now(),item.id);}catch(error){const message=error instanceof Error?error.message:"Nachrecherche fehlgeschlagen.";getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status=CASE WHEN versuche>=max_versuche THEN 'offen_manuell' ELSE 'offen' END,fehler=?,updated_at=? WHERE id=?").run(message,now(),item.id);}}}

async function textAusBytes(bytes: Uint8Array, mime: string): Promise<string> {
  if (mime === "application/pdf") {
    try {
      const { extractText } = await import("unpdf");
      const extracted = await extractText(bytes, { mergePages: true });
      const text = Array.isArray(extracted.text) ? extracted.text.join("\n") : String(extracted.text ?? "");
      return text.slice(0, 8000);
    } catch { return ""; }
  }
  return htmlText(new TextDecoder().decode(bytes)).slice(0, 8000);
}

function datumImText(value: string | null, text: string): string | null {
  if (!value) return null;
  const iso = value.slice(0, 10);
  const [year, month, day] = iso.split("-");
  const forms = [iso, day ? `${day}.${month}.${year}` : "", month ? `${month}.${year}` : ""].filter(Boolean);
  return forms.some((form) => text.includes(form)) ? iso : null;
}

async function holeEinstiegsseiten(): Promise<ErfassteSeite[]> {
  const urls = [requirements.einstiege.mediencenter, requirements.einstiege.ksvg, requirements.einstiege.ksventgv];
  const pages: ErfassteSeite[] = [];
  for (const url of urls) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(30_000), headers: { "User-Agent": "KSK-SaaS-Quellenarchiv/1.0" } });
      pages.push({ url, html: response.ok ? await response.text() : null, error: response.ok ? undefined : `HTTP ${response.status}` });
    } catch (error) {
      pages.push({ url, html: null, error: error instanceof Error ? error.message : "Abruf fehlgeschlagen." });
    }
  }
  return pages;
}

async function werteInhalteAus(jahr: number, dokumente: Array<{ katalogKey: string; titel: string; text: string }>): Promise<AuswertungErgebnis> {
  if (!process.env.OPENAI_API_KEY) throw new Error("OPENAI_API_KEY ist serverseitig nicht konfiguriert.");
  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY, timeout: 90_000, maxRetries: 1 });
  const schema = { type: "object", additionalProperties: false, required: ["urteile", "luecken"], properties: {
    urteile: { type: "array", items: { type: "object", additionalProperties: false, required: ["katalogKey", "anwendungStatus", "gueltigAb", "gueltigBis", "dokumentstand", "fundstelle", "zahlen", "aenderungen", "luecken"], properties: {
      katalogKey: { type: "string" }, anwendungStatus: { type: "string", enum: ["belegt", "ungeklaert", "widerspruch"] },
      gueltigAb: { type: ["string", "null"] }, gueltigBis: { type: ["string", "null"] }, dokumentstand: { type: ["string", "null"] },
      fundstelle: { type: "string" }, zahlen: { type: "array", items: { type: "string" } }, aenderungen: { type: "string" }, luecken: { type: "array", items: { type: "string" } },
    } } },
    luecken: { type: "array", items: { type: "string" } },
  } } as const;
  const stoff = dokumente.map((item) => `### ${item.katalogKey}\nTitel: ${item.titel}\n${item.text || "Kein Text extrahiert."}`).join("\n\n");
  const response = await client.responses.create({
    model: modelName(), store: false, max_output_tokens: 4000,
    input: [
      { role: "system", content: "Du wertest nur die mitgelieferten amtlichen Textauszüge für ein KSK-Jahrespaket aus. Erfinde keine URL, keine Zahl und keinen Gültigkeitszeitraum. Dokumentstand, Änderungsdatum, Inkrafttreten und Abrufdatum bleiben getrennt. Eine aktuelle Gesamtausgabe gilt nicht automatisch für frühere Jahre. Ergebnisse sind Entwürfe." },
      { role: "user", content: `Zieljahr ${jahr}. Prüfumfang: ${requirements.umfang.map((item) => item.label).join("; ")}.\n\n${stoff}` },
    ],
    text: { format: { type: "json_schema", name: "ksk_auswertung", strict: true, schema } },
  });
  const parsed = JSON.parse(response.output_text) as AuswertungErgebnis;
  if (!Array.isArray(parsed.urteile) || !Array.isArray(parsed.luecken)) throw new Error("OpenAI lieferte keine gültige Auswertung.");
  parsed.kostenUsd = estimateCost(response, false);
  return parsed;
}

function speichereAuswertung(sha: string, jahr: number, ergebnis: unknown): void {
  getDb().prepare(`INSERT OR IGNORE INTO quellen_auswertungen (id, sha256, jahr, umfang_version, auswertung_version, ergebnis_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).run(crypto.randomUUID(), sha, jahr, requirements.version, requirements.auswertung_version, JSON.stringify(ergebnis), now());
}

function ladeAuswertung(sha: string, jahr: number): DokumentUrteil | null {
  const row = getDb().prepare(`SELECT ergebnis_json FROM quellen_auswertungen WHERE sha256 = ? AND jahr = ? AND umfang_version = ? AND auswertung_version = ?`)
    .get(sha, jahr, requirements.version, requirements.auswertung_version) as { ergebnis_json: string } | undefined;
  return row ? JSON.parse(row.ergebnis_json) as DokumentUrteil : null;
}

async function erfasseUndWerte(prep: VorbereitungStatus, deps: Dependencies, download: (url: string) => Promise<Download>): Promise<void> {
  const pages = await (deps.capture ?? holeEinstiegsseiten)();
  merkeKatalog(festeEinstiege());
  for (const page of pages) {
    if (!page.html) {
      task(prep.id, `beschaffung:${page.url}`, "technische_beschaffung", "technische_beschaffung", `Einstieg ${page.url} konnte nicht gelesen werden. Fehlende Information: die Dokumentliste. Nächster Schritt: denselben amtlichen Einstieg erneut abrufen. Abschluss: die Seite liefert die bekannte Linkliste. Fehler: ${page.error ?? "leer"}`);
      continue;
    }
    if (page.url === requirements.einstiege.mediencenter) {
      const eintraege = leseLinkliste(page.html, page.url, "Künstlersozialkasse");
      const layout = mediencenterLayout(page.html, eintraege);
      if (!layout.erkannt) {
        task(prep.id, "layout:mediencenter", "technische_beschaffung", "technische_beschaffung", `Fehlende Information: Mediencenter-Inventar. Betroffene Regel: Ausgangsquellen Info 10, 12 und 27. Nächster Schritt: Seitenaufbau prüfen. Abschlusskriterium: Informationsschriften sind wieder als PDF-Links mit Dokumentnummer lesbar. ${layout.fehler}`);
        continue;
      }
      merkeKatalog(eintraege.map((item) => ({ ...item, listenherkunft: "mediencenter" })));
      continue;
    }
    const stamm = festeEinstiege().find((item) => item.url === page.url);
    if (stamm) merkeKatalog(ergaenzeGesetzestexte(page.html, page.url, stamm));
  }
  const ausgewählt = ausgangsquellen();
  const texte = new Map<string, { katalogKey: string; titel: string; text: string; sha: string; stand: ReturnType<typeof standAusText> }>();
  for (const eintrag of ausgewählt) {
    const vorhanden = getDb().prepare("SELECT id, status, archiv_quelle_id FROM jahrespaket_quellenfunde WHERE vorbereitung_id = ? AND url = ?").get(prep.id, eintrag.url) as { id: string; status: string; archiv_quelle_id: string | null } | undefined;
    if (vorhanden?.status === "archiviert" && vorhanden.archiv_quelle_id) continue;
    const findingId = upsertFinding(prep, { kategorie: eintrag.art === "informationsschrift" ? "ksk_informationen" : eintrag.katalogKey.includes("ksvg") ? "ksvg" : eintrag.katalogKey.includes("ksventgv") ? "ksventgv" : "abgabesatz", titel: eintrag.titel, url: eintrag.url, herausgeber: eintrag.herausgeber, dokumentstand: null, zeitbezug: "Zeitbezug wird nach dem Archiv geprüft.", fuerJahrBelegt: false, anwendungStatus: "ungeklaert" });
    try {
      const file = await download(eintrag.url);
      const text = await textAusBytes(file.bytes, file.mimeType);
      const stand = standAusText(text);
      const archivStand = stand.iso ?? new Date().toISOString().slice(0, 10);
      const archive = archiviereOriginal({ bytes: file.bytes, originalName: file.filename, mimeType: file.mimeType, herkunft: file.finalUrl, dokumentstand: archivStand, abrufdatum: new Date().toISOString().slice(0, 10), genauigkeit: stand.genauigkeit });
      const paketQuelleId = ordneArchivquelleZu(prep.jahrespaket_id, archive.id);
      setzeKatalogArchiv(eintrag.katalogKey, archive.id);
      getDb().prepare("UPDATE jahrespaket_quellenfunde SET url=?, status='archiviert', archiv_quelle_id=?, paket_quelle_id=?, dokumentstand=?, dokumentstand_art=?, luecken_typ=?, fehler=NULL, updated_at=? WHERE id=?")
        .run(file.finalUrl, archive.id, paketQuelleId, stand.iso, stand.genauigkeit, stand.genauigkeit === "unbekannt" ? "metadaten_fehlen" : "zeitliche_anwendung", now(), findingId);
      texte.set(eintrag.katalogKey, { katalogKey: eintrag.katalogKey, titel: eintrag.titel, text, sha: archive.sha256, stand });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Beschaffung fehlgeschlagen.";
      getDb().prepare("UPDATE jahrespaket_quellenfunde SET status='fehler', luecken_typ='technische_beschaffung', fehler=?, updated_at=? WHERE id=?").run(message, now(), findingId);
      task(prep.id, `beschaffung:${eintrag.katalogKey}`, eintrag.katalogKey, "technische_beschaffung", `Fehlende Information: Datei zu ${eintrag.titel}. Betroffene Regel: ${eintrag.katalogKey}. Nächster Schritt: denselben amtlichen Link erneut laden. Abschluss: HTTP-Download und Archiv-Hash. Fehler: ${message}`);
    }
  }
  const fehlend = [...texte.values()].filter((item) => !ladeAuswertung(item.sha, prep.jahr));
  const dokumente = fehlend.map((item) => ({ katalogKey: item.katalogKey, titel: item.titel, text: item.text }));
  let ergebnis: AuswertungErgebnis = { urteile: [], luecken: [] };
  try {
    ergebnis = !fehlend.length
      ? ergebnis
      : deps.evaluate
        ? await deps.evaluate({ jahr: prep.jahr, dokumente })
        : await werteInhalteAus(prep.jahr, dokumente);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Auswertung fehlgeschlagen.";
    task(prep.id, "auswertung:openai", "auswertung", "technische_beschaffung", `Fehlende Information: KI-Auswertung der archivierten Texte. Betroffene Regel: gesamter Prüfumfang. Nächster Schritt: OpenAI-Zugang prüfen und dieselbe Auswertung wiederholen. Abschluss: Urteile zu den archivierten Dokumenten. Fehler: ${message}`);
  }
  if (ergebnis.kostenUsd) updatePreparation(prep.id, { addCost: ergebnis.kostenUsd });
  for (const urteil of ergebnis.urteile) {
    const dokument = texte.get(urteil.katalogKey);
    if (!dokument) continue;
    const gueltigAb = datumImText(urteil.gueltigAb, dokument.text);
    const gueltigBis = datumImText(urteil.gueltigBis, dokument.text);
    const gelesen = leseDokumentstand(urteil.dokumentstand) ;
    const stand = gelesen.genauigkeit === "unbekannt" ? dokument.stand : gelesen;
    const offenePunkte = urteilOffen(urteil);
    const anwendung = anwendungFuerJahr({ jahr: prep.jahr, genauigkeit: stand.genauigkeit, iso: stand.iso, gueltigAb, gueltigBis, modell: urteil.anwendungStatus, offenePunkte });
    const ltype: LueckenTyp | null = anwendung === "widerspruch" ? "fachlicher_widerspruch" : anwendung === "ungeklaert" ? "zeitliche_anwendung" : stand.genauigkeit === "unbekannt" ? "metadaten_fehlen" : null;
    getDb().prepare(`UPDATE jahrespaket_quellenfunde SET dokumentstand=?, dokumentstand_art=?, gueltig_ab=?, gueltig_bis=?, anwendung_status=?, zeitbezug=?, luecken_typ=?, updated_at=?
      WHERE vorbereitung_id=? AND archiv_quelle_id=(SELECT id FROM archiv_quellen WHERE sha256=?)`).run(
      stand.iso, stand.genauigkeit, gueltigAb, gueltigBis, anwendung, urteil.fundstelle || urteil.aenderungen || "Auswertung ohne zusätzliche Fundstelle.", ltype, now(), prep.id, dokument.sha,
    );
    speichereAuswertung(dokument.sha, prep.jahr, urteil);
    if (ltype) task(prep.id, `${ltype}:${urteil.katalogKey}:${dokument.sha}:${prep.jahr}`, urteil.katalogKey, ltype, `Fehlende Information: ${ltype} für ${dokument.titel} im Jahr ${prep.jahr}. Betroffene Regel: ${urteil.katalogKey}. Nächster Schritt: Inkrafttreten oder historische Fassung in der Zulassungsliste suchen. Abschluss: ein Beleg, der das Kalenderjahr ${prep.jahr} ausdrücklich trägt. ${offenePunkte.join(" ")}`);
  }
  for (const luecke of ergebnis.luecken.filter(istKonkreteLuecke)) task(prep.id, `auswertung:${luecke.toLowerCase().slice(0, 80)}`, "allgemein", "quelle_fehlt", `Fehlende Information: ${luecke}. Nächster Schritt: eine Quelle innerhalb der Zulassungsliste. Abschluss: archivierter Beleg oder bestätigte Lücke.`);
  if (!katalogNachKey("verordnung:abgabe") && !ausgangsquellen().some((item) => item.art === "verordnung" && /abgabe/i.test(item.titel) && item.katalogKey !== "verordnung:ksventgv")) {
    task(prep.id, "quelle_fehlt:abgabesatz", "abgabesatz", "quelle_fehlt", `Fehlende Information: Jahres-Abgabeverordnung ${prep.jahr}. Betroffene Regel: Abgabesatz. Nächster Schritt: Bekanntmachung auf gesetze-im-internet.de, bundesgesetzblatt.de oder bmas.de. Abschluss: eine amtliche Fundstelle, die den Satz für ${prep.jahr} nennt.`);
  }
}

export async function fuehreVorbereitungAus(preparationId:string,deps:Dependencies={}):Promise<void>{
  const prep=holeVorbereitung(preparationId);if(!prep||terminalProcessing.has(prep.status))return;
  const research=deps.research??recherchiereOffizielleQuellen,download=deps.download??ladeOffizielleQuelle;
  try{
    const existing=(getDb().prepare("SELECT COUNT(*) n FROM jahrespaket_quellenfunde WHERE vorbereitung_id=?").get(prep.id) as {n:number}).n;
    const katalogZuerst = Boolean(deps.capture) || !deps.research;
    updatePreparation(prep.id,{status:"running",schritt:existing?"Bestehenden Entwurf fortsetzen":katalogZuerst?"Offizielle Quellen werden erfasst":"OpenAI recherchiert offizielle Quellen",fortschritt:10,fehler:null});
    if(katalogZuerst){
      await erfasseUndWerte(prep, deps, download);
      updatePreparation(prep.id,{schritt:"Gezielte Nachrecherchen",fortschritt:45});
    } else if(!existing){
      const found=await research(prep.jahr);updatePreparation(prep.id,{schritt:"Quellen werden archiviert",fortschritt:30,addCost:found.kostenUsd??0});const seen=new Set<string>();
      for(const source of found.quellen.slice(0,requirements.max_quellen)){seen.add(source.kategorie);const id=upsertFinding(prep,source);await archiveSource(prep,source,id,download);}
      for(const req of REQUIRED)if(!seen.has(req))task(prep.id,`quelle_fehlt:${req}`,req,"quelle_fehlt",`Finde die fehlende amtliche Quelle für den Prüfumfang ${req} im Jahr ${prep.jahr}.`);
      for(const [i,gap] of found.luecken.entries())if(istKonkreteLuecke(gap))task(prep.id,`gemeldet:${i}:${gap.toLowerCase().slice(0,80)}`,"allgemein","quelle_fehlt",gap);
    }
    updatePreparation(prep.id,{schritt:"Gezielte Nachrecherchen",fortschritt:50});await runRetries(prep,deps,download);
    const budget=preparationRow(prep.id)!;
    if(budget.kosten_usd+requirements.max_kosten_pro_recherche_usd>budget.kostenlimit_usd){
      const reason=`Kostenlimit: ${budget.kosten_usd.toFixed(6)} USD verbraucht + ${requirements.max_kosten_pro_recherche_usd.toFixed(2)} USD Reserve > ${budget.kostenlimit_usd.toFixed(2)} USD Limit.`;
      getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status='kostenlimit',fehler=?,updated_at=? WHERE vorbereitung_id=? AND status='offen'").run(reason,now(),prep.id);
    }
    updatePreparation(prep.id,{schritt:"Archivquellen werden in Mistral indexiert",fortschritt:75});
    const index=await ensureMistral(prep,deps);
    if(index.errors.length===0){
      const library=getDb().prepare("SELECT mistral_library_id FROM jahrespaket_bibliotheken WHERE jahrespaket_id=?").get(prep.jahrespaket_id) as {mistral_library_id:string}|undefined;
      const documents=getDb().prepare(`SELECT q.id paketQuelleId,z.mistral_document_id documentId FROM jahrespaket_quellen q JOIN jahrespaket_mistral_zuordnungen z ON z.id=(SELECT z2.id FROM jahrespaket_mistral_zuordnungen z2 WHERE z2.jahrespaket_quelle_id=q.id ORDER BY z2.created_at DESC LIMIT 1) WHERE q.jahrespaket_id=? AND lower(z.verarbeitungsstatus) IN ('completed','complete','done')`).all(prep.jahrespaket_id) as Array<{paketQuelleId:string;documentId:string}>;
      const currentManifest=getDb().prepare("SELECT id FROM jahrespaket_indexmanifeste WHERE jahrespaket_id=? AND invalidated_at IS NULL ORDER BY created_at DESC LIMIT 1").get(prep.jahrespaket_id) as {id:string}|undefined;
      const manifest=currentManifest??erzeugeIndexmanifest(prep.jahrespaket_id);
      if(deps.ragVerify&&library){
        const proof=await deps.ragVerify({paketId:prep.jahrespaket_id,libraryId:library.mistral_library_id,documents});
        const expected=documents.map((item)=>item.documentId);
        protokolliereRagPruefung({manifestId:manifest.id,art:"positiv",modell:proof.modell,testfrage:"Paketgebundener positiver Abruf",erwarteteDokumentIds:expected,referenzierteDokumentIds:proof.positiveReferenzen,anbieterBestanden:proof.positivBestanden,ergebnis:proof.ergebnis});
        protokolliereRagPruefung({manifestId:manifest.id,art:"trennung",modell:proof.modell,testfrage:"Negative Pakettrennung",erwarteteDokumentIds:[],referenzierteDokumentIds:proof.trennungReferenzen,anbieterBestanden:proof.trennungBestanden,ergebnis:proof.ergebnis});
      }else{
        task(prep.id,"rag:abruf-und-trennung","rag_pruefung","technische_beschaffung","Fehlende Information: positiver paketgebundener RAG-Abruf und negative Trennungsprüfung. Nächster Schritt: beide Prüfungen gegen das aktuelle Indexmanifest ausführen. Abschluss: zwei gespeicherte bestandene RAG-Prüfprotokolle.");
        getDb().prepare("UPDATE jahrespaket_nachrecherchen SET status='offen_manuell',fehler='Mistral Completed belegt nur Verarbeitung, nicht RAG-Abruf oder Pakettrennung.',updated_at=? WHERE vorbereitung_id=? AND aufgabe_key='rag:abruf-und-trennung'").run(now(),prep.id);
      }
    }
    const tasks=getDb().prepare("SELECT typ,status,suchauftrag,fehler FROM jahrespaket_nachrecherchen WHERE vorbereitung_id=? AND status!='geloest'").all(prep.id) as Array<{typ:string;status:string;suchauftrag:string;fehler:string|null}>;
    const gaps=[...tasks.map((t)=>`${t.typ}: ${t.suchauftrag}${t.fehler?` (${t.fehler})`:""}`),...index.errors.map((e)=>`technische_beschaffung: ${e}`)];
    const archived=(getDb().prepare("SELECT COUNT(*) n FROM jahrespaket_quellenfunde WHERE vorbereitung_id=? AND status='archiviert'").get(prep.id) as {n:number}).n;
    updatePreparation(prep.id,{status:archived?"completed":"failed",schritt:`Entwurf fortgesetzt: ${archived} archiviert, ${index.indexed} indexiert`,fortschritt:100,luecken:gaps,fehler:archived?null:"Keine Quelle konnte archiviert werden.",completed:true});
  }catch(error){updatePreparation(prep.id,{status:"failed",schritt:"Vorbereitung fehlgeschlagen",fortschritt:100,fehler:error instanceof Error?error.message:"Unbekannter Fehler",completed:true});throw error;}
}

export function claimVorbereitungsJob(){const db=getDb();const row=db.prepare("SELECT id,payload_json FROM jobs WHERE status='queued' AND type='jahrespaket_vorbereitung' ORDER BY created_at LIMIT 1").get() as {id:string;payload_json:string}|undefined;if(!row)return null;const changed=db.prepare("UPDATE jobs SET status='running',locked_at=?,attempts=attempts+1 WHERE id=? AND status='queued'").run(now(),row.id);if(Number(changed.changes)!==1)return null;return{jobId:row.id,preparationId:(JSON.parse(row.payload_json) as {preparationId:string}).preparationId};}
export function finishVorbereitungsJob(jobId:string,error:string|null){getDb().prepare("UPDATE jobs SET status=?,error=?,finished_at=? WHERE id=?").run(error?"failed":"done",error,now(),jobId);}
export const quellenAnforderungen=requirements;
export const aktiveVorbereitungsstatus=ACTIVE;
