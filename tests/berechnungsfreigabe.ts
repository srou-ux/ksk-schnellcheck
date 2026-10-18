import { ABGABEGRENZE, ABGABESATZ, BEREICH_ABGABESATZ, BEREICH_GRENZE } from "../src/lib/register-kennungen";
import { gebeFrei } from "../src/lib/zahlen-register";

const beleg = {
  fundstelle: "Testbeleg für die Berechnung, keine fachliche Produktfreigabe",
  dokumentstand: "2026-10-05",
};

export function stelleTestSaetzeFrei(): void {
  gebeFrei({
    gruppe: ABGABESATZ,
    beschreibung: "Künstlersozialabgabe, Abgabesatz",
    betrag: "5",
    einheit: "prozent",
    gueltigAb: "2025-01-01",
    gueltigBis: "2025-12-31",
    anwendungsbereich: BEREICH_ABGABESATZ,
    quelle: "Künstlersozialkasse, Abgabesatz für 2025: 5,0 Prozent",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABESATZ,
    beschreibung: "Künstlersozialabgabe, Abgabesatz",
    betrag: "4,9",
    einheit: "prozent",
    gueltigAb: "2026-01-01",
    gueltigBis: "2026-12-31",
    anwendungsbereich: BEREICH_ABGABESATZ,
    quelle: "Künstlersozialkasse, Abgabesatz für 2026: 4,9 Prozent",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABEGRENZE,
    beschreibung: "Jährliche Entgeltgrenze für nicht-kommerzielle Veranstalter",
    betrag: "700",
    einheit: "euro",
    gueltigAb: "2025-01-01",
    gueltigBis: "2025-12-31",
    anwendungsbereich: BEREICH_GRENZE,
    quelle: "§ 54 KSVG: Entgeltsumme im Kalenderjahr 2025 700 Euro",
    ...beleg,
  });
  gebeFrei({
    gruppe: ABGABEGRENZE,
    beschreibung: "Jährliche Entgeltgrenze für nicht-kommerzielle Veranstalter",
    betrag: "1000",
    einheit: "euro",
    gueltigAb: "2026-01-01",
    gueltigBis: "2026-12-31",
    anwendungsbereich: BEREICH_GRENZE,
    quelle: "§ 24 Abs. 2 Satz 2 KSVG: 1.000 Euro",
    ...beleg,
  });
}
