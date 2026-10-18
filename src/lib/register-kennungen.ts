export const ABGABESATZ = "abgabesatz";
export const ABGABEGRENZE = "abgabepflichtgrenze_veranstalter";
export const BEREICH_ABGABESATZ = "Künstlersozialabgabe für das Kalenderjahr";
export const BEREICH_GRENZE = "§ 24 Abs. 2 KSVG";

const BERECHNUNG = [ABGABESATZ, ABGABEGRENZE] as const;

export type Berechnungskennung = (typeof BERECHNUNG)[number];

export function istBerechnungskennung(kennung: string): kennung is Berechnungskennung {
  return (BERECHNUNG as readonly string[]).includes(kennung);
}

export type RegisterSnapshot = {
  id: string;
  kennung: string;
  anwendungsbereich: string | null;
  wertExakt: string | null;
  wertCent: number | null;
  wertBps: number | null;
  einheit: string;
  gueltigAb: string;
  gueltigBis: string | null;
  quelle: string;
  fundstelle: string | null;
  dokumentstand: string | null;
  freigabe: string;
};
