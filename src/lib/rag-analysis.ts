import { readFileSync } from "node:fs";
import path from "node:path";
import type { Mistral } from "@mistralai/mistralai";
import { dokumentZahlen, ergaenzeZahlen, fehlendeBetragszeilen, grenzenAusAntwort, nenntKeineZahlen, parseAbschnitte, zahlenAusNachfrage } from "@/lib/mistral/abschnitte";
import { betraegeImText, chunkZeile, dokumentbasisWarnung, stellenBlock, type ChunkBeleg } from "@/lib/mistral/chunks";
import { prozentWerte, pruefeAntwort, type RagPruefung } from "@/lib/mistral/rag-pruefung";
import { bezugsjahr, f05Hinweis, klassifiziereProzent, ladeZahlenWerte, mitZeitabweichung, nurGueltigeBetraege, relevanteBetraege, zeitErgebnis, zeitHinweisEintraege, type ProzentZeile, type ZeitCheck } from "@/lib/mistral/zahlen-werte";
import { konsensVergleich, laufSchluessel, vergleicheLaeufe, type KonsensErgebnis, type PrueferSicht } from "@/lib/model-consensus";
import { ragUserPrompt } from "@/lib/rag-system-prompt";
import { askOneModel, client, ergaenzeBetragsstellen, explainMistralError, findLibrary, hybridZiele } from "@/lib/rag-retrieval";

type PrueferConfig = { id: string; label: string; modell: string };

export type PrueferErgebnis = {
  id: string;
  label: string;
  modell: string;
  ok: boolean;
  answer: string;
  gezeigt: boolean;
  nutzerangaben: string;
  hinweise: string[];
  chunks: string;
};

function loadPrueferConfig(): { pruefer: PrueferConfig[]; angezeigt: string } {
  const file = path.join(/*turbopackIgnore: true*/ process.cwd(), "config", "rag-pruefer.json");
  const parsed = JSON.parse(readFileSync(file, "utf8")) as { pruefer?: PrueferConfig[]; angezeigte_antwort?: string };
  const pruefer = parsed.pruefer ?? [];
  if (pruefer.length !== 2) throw new Error("Die Prüfer-Konfiguration braucht genau zwei Modelle.");
  return { pruefer, angezeigt: parsed.angezeigte_antwort || pruefer[1].id };
}

async function assertPrueferModels(api: Mistral, models: string[]): Promise<void> {
  const listed = await api.models.list();
  const available = new Set((listed.data ?? []).flatMap((item) => "id" in item && typeof item.id === "string" ? [item.id] : []));
  const missing = models.filter((model) => !available.has(model));
  if (missing.length > 0) {
    throw new Error(`Diese Prüfer-Modelle sind unter diesem Schlüssel nicht verfügbar: ${missing.join(", ")}. Die Prüfung wird nicht auf weniger Modelle verkürzt.`);
  }
}

function nachfragePrompt(frage: string, zeilen: string[]): string {
  return [
    `Frage: ${frage}`,
    "",
    "Diese Beträge stehen wörtlich in den abgerufenen Dokumentstellen:",
    ...zeilen.map((zeile) => `- ${zeile}`),
    "",
    "Schreibe nur diesen Abschnitt:",
    "ZAHLEN:",
    "- <Betrag> | <Dokumentname>",
    "Nimm jeden Betrag aus der Liste auf, dessen Dokument die Frage beantwortet.",
  ].join("\n");
}

export type RagAntwort = {
  answer: string;
  sources: string[];
  pruefung: RagPruefung | null;
  konsens: KonsensErgebnis;
  pruefer: PrueferErgebnis[];
  zeit: ZeitCheck;
  prozent: ProzentZeile[];
  listeHinweise: string[];
  basis: string | null;
};

function laufAus(zeilen: PrueferSicht[], konsens: KonsensErgebnis): { signatur: string; einig: boolean; kurz: string } {
  const basis = laufSchluessel(zeilen);
  const einig = konsens.status === "konsens" || konsens.status === "hinweis";
  return { signatur: `${konsens.status}|${basis.signatur}`, einig, kurz: konsens.detail ?? konsens.line };
}

async function frageEinmal(question: string, libraryId: string): Promise<{ ergebnis: RagAntwort; lauf: { signatur: string; einig: boolean; kurz: string } }> {
  const trimmed = question.trim();
  if (!trimmed) throw new Error("Die Frage fehlt.");
  const liste = ladeZahlenWerte();
  const bezug = bezugsjahr(trimmed);
  const userPrompt = ragUserPrompt(trimmed, bezug.jahr);
  const api = client();
  const { pruefer, angezeigt } = loadPrueferConfig();
  await assertPrueferModels(api, pruefer.map((item) => item.modell));
  const listedDocuments = await api.beta.libraries.documents.list({ libraryId, pageSize: 100 });
  const documentNames = listedDocuments.data.map((document) => document.name).filter(Boolean);
  let gemeinsame: ChunkBeleg[] = [];
  try {
    const suche = await askOneModel(api, pruefer[0].modell, userPrompt, libraryId);
    gemeinsame = suche.chunks.filter((chunk) => chunk.text.trim());
  } catch {
    gemeinsame = [];
  }
  gemeinsame = await ergaenzeBetragsstellen(
    api,
    libraryId,
    gemeinsame,
    listedDocuments.data.map((document) => ({ id: document.id, name: document.name })),
    hybridZiele(trimmed, liste),
  );
  const prompt = gemeinsame.length > 0 ? `${userPrompt}\n\n${stellenBlock(gemeinsame)}` : userPrompt;
  const settled = await Promise.all(pruefer.map(async (item) => {
    try {
      const result = await askOneModel(api, item.modell, prompt, gemeinsame.length > 0 ? null : libraryId);
      if (gemeinsame.length > 0) {
        result.chunks = gemeinsame;
        result.passages = gemeinsame.map((chunk) => chunk.text);
        result.citationsField = true;
      }
      return { item, ok: true as const, result };
    } catch (error) {
      return { item, ok: false as const, error: explainMistralError(error) };
    }
  }));
  if (settled.every((item) => !item.ok)) {
    const first = settled.find((item) => !item.ok);
    throw new Error(`Die Frage ist fehlgeschlagen, weil ${first && !first.ok ? first.error : "kein Prüfer geantwortet hat."}`);
  }
  const nachgefragt = new Set<string>();
  if (gemeinsame.length > 0) {
    const relevante = relevanteBetraege(trimmed, liste, bezug.jahr)
      .filter((item) => item.unit === "euro")
      .map((item) => item.value);
    const zeilen = betraegeImText(gemeinsame);
    await Promise.all(settled.map(async (entry) => {
      if (!entry.ok) return;
      const fehlend = fehlendeBetragszeilen(entry.result.answer, zeilen, relevante);
      if (fehlend.length === 0) return;
      try {
        const retry = await askOneModel(
          api,
          entry.item.modell,
          nachfragePrompt(trimmed, fehlend),
          null,
          "Du schreibst nur den Abschnitt ZAHLEN. Übernimm jeden Betrag aus der Liste, dessen Dokument die Frage beantwortet. Nenne den Dokumentnamen, keine Kennung.",
        );
        const zusatz = zahlenAusNachfrage(retry.answer, fehlend);
        if (!zusatz) return;
        entry.result.answer = ergaenzeZahlen(entry.result.answer, zusatz);
        nachgefragt.add(entry.item.id);
      } catch {
        // Die erste Antwort bleibt stehen.
      }
    }));
  }
  const ausgewertet = settled.map((entry) => {
    if (!entry.ok) {
      return {
        id: entry.item.id,
        label: entry.item.label,
        modell: entry.item.modell,
        ok: false as const,
        answer: "",
        sources: [] as string[],
        passages: [] as string[],
        citationsField: false,
        chunks: [] as ChunkBeleg[],
        dok: null,
      };
    }
    return {
      id: entry.item.id,
      label: entry.item.label,
      modell: entry.item.modell,
      ok: true as const,
      answer: entry.result.answer,
      sources: entry.result.sources,
      passages: entry.result.passages,
      citationsField: entry.result.citationsField,
      chunks: entry.result.chunks,
      dok: dokumentZahlen({
        answer: entry.result.answer,
        corpus: entry.result.passages.join("\n"),
        documentNames,
        prueferLabel: entry.item.label,
        liste,
      }),
    };
  });
  const zeitEintraege = ausgewertet.flatMap((entry) => zeitHinweisEintraege(
    entry.ok ? grenzenAusAntwort(entry.answer) : [],
    liste,
    bezug.jahr,
    entry.label,
  ));
  const zeit = zeitErgebnis({ jahr: bezug.jahr, angenommen: bezug.angenommen, hinweise: zeitEintraege.map((eintrag) => eintrag.text) });
  const prozent = ausgewertet.flatMap((entry) => {
    if (!entry.ok) return [];
    const sections = parseAbschnitte(entry.answer);
    const text = [sections.zahlen, sections.nutzerangaben].filter(Boolean).join("\n") || entry.answer;
    const gesehen = new Set<string>();
    const zeilen: ProzentZeile[] = [];
    for (const wert of prozentWerte(text)) {
      const key = wert.value.toFixed(2);
      if (gesehen.has(key)) continue;
      gesehen.add(key);
      zeilen.push({
        pruefer: entry.label.match(/Prüfer\s+\d+/)?.[0] ?? entry.label,
        label: wert.label,
        status: klassifiziereProzent(wert.value, trimmed, liste),
      });
    }
    return zeilen;
  });
  const listeHinweise = ausgewertet.flatMap((entry) => {
    if (!entry.ok) return [];
    const hinweis = f05Hinweis({
      nenntKeine: nenntKeineZahlen(entry.answer),
      frage: trimmed,
      jahr: bezug.jahr,
      liste,
      prueferLabel: entry.label,
    });
    return hinweis ? [hinweis] : [];
  });
  const basis = dokumentbasisWarnung(ausgewertet.map((entry) => ({ label: entry.label, chunks: entry.chunks })));
  const konsensZeilen = ausgewertet.map((entry) => {
    const gueltig = nurGueltigeBetraege(entry.dok?.keys ?? [], entry.dok?.labels ?? [], liste, bezug.jahr);
    return {
      id: entry.id,
      label: entry.label,
      ok: entry.ok,
      answer: entry.answer,
      documents: entry.dok?.documents ?? [],
      amountKeys: gueltig.keys,
      amountLabels: gueltig.labels,
    };
  });
  const konsens = mitZeitabweichung(
    konsensVergleich(konsensZeilen),
    zeitEintraege,
    konsensZeilen.some((entry) => entry.ok && entry.amountKeys.length > 0),
  );
  const shown = ausgewertet.find((entry) => entry.id === angezeigt) ?? ausgewertet[ausgewertet.length - 1];
  const prueferErgebnis: PrueferErgebnis[] = ausgewertet.map((entry) => ({
    id: entry.id,
    label: entry.label,
    modell: entry.modell,
    ok: entry.ok,
    answer: entry.answer,
    gezeigt: entry.id === angezeigt,
    nutzerangaben: entry.dok?.nutzerangaben ?? "",
    hinweise: [
      ...(entry.dok?.hinweise ?? []),
      ...(nachgefragt.has(entry.id) ? ["Nachfrage: im Text stehende Beträge waren in der ersten Antwort nicht genannt."] : []),
    ],
    chunks: chunkZeile(entry.chunks),
  }));
  const lauf = laufAus(konsensZeilen, konsens);
  if (!shown.ok) {
    return { ergebnis: { answer: "", sources: [], pruefung: null, konsens, pruefer: prueferErgebnis, zeit, prozent, listeHinweise, basis }, lauf };
  }
  const sections = parseAbschnitte(shown.answer);
  const zahlText = sections.vollstaendig
    ? [sections.kernaussagen, sections.zahlen, sections.fundstellen, sections.luecken].join("\n")
    : shown.answer;
  const pruefung = pruefeAntwort({
    answer: shown.answer,
    zahlText,
    documentNames,
    citationsField: shown.citationsField,
    passages: shown.passages,
    citationLabels: shown.sources,
  });
  return {
    ergebnis: {
      answer: shown.answer,
      sources: shown.sources,
      pruefung,
      konsens,
      pruefer: prueferErgebnis,
      zeit,
      prozent,
      listeHinweise,
      basis,
    },
    lauf,
  };
}

export async function pruefeRagFrage(question: string, libraryId: string): Promise<RagAntwort> {
  const erster = await frageEinmal(question, libraryId);
  if (erster.ergebnis.konsens.status !== "abweichung" && erster.ergebnis.konsens.status !== "keiner") return erster.ergebnis;
  const [zweit, dritt] = await Promise.all([frageEinmal(question, libraryId), frageEinmal(question, libraryId)]);
  const vergleich = vergleicheLaeufe([erster.lauf, zweit.lauf, dritt.lauf]);
  const gewaehlt = vergleich.status === "konsens" ? erster : dritt;
  return { ...gewaehlt.ergebnis, konsens: vergleich };
}

export async function askLibrary(question: string): Promise<RagAntwort> {
  const library = await findLibrary(client());
  if (!library) throw new Error("Die Library KSK-Referenzen gibt es nicht. Lege sie zuerst an.");
  return pruefeRagFrage(question, library.id);
}
