# Register-Lücken, 18.10.2026

Entwurf – vom Steuerberater zu prüfen. Eingetragen wurde nur, was in den PDFs unter `quellen/` wörtlich steht. Keine Regel ohne Fundstelle.

## Messung

- Suite-100: 100/100
- Erfahrungs-Suite: 120/120
- In diesem Durchgang hat sich keine Erwartung geändert (keine Zeile OFFEN → entschieden).
- `tests/test_kern.py`: 42 Tests, Wächter grün, `parameter.json` passt zur Excel
- Korpus neu gemessen (`scripts/lauf_offline.py`): 1.822 Fälle, 1.782 richtig, 40 nachgefragt, 0 falsch. Die 40 sind F09 ohne Beleg (Grenzfall). Einzelheiten in `aufgaben/audit/alltag999_auswertung.md`.

## Bestandskorrektur (zweiter Durchgang)

`regeln/saetze.json` hatte nur 2025 und 2026. Jetzt stehen 2015–2026 darin, Sätze und Fundstellen aus `kern/parameter.json`. 2015–2018 haben einen Satz und keine Schwelle (`thresholdCents` null); eine 450-Euro-Grenze für diese Jahre steht im Register nicht und wurde nicht erfunden. 2019–2022 haben 450 Euro als Geringfügigkeitsgrenze der Fassung A, mit dem Hinweis auf die zusätzliche Regelmäßigkeit, nicht als harte Grenze nach § 24 Abs. 2. 2023–2024 haben dieselben 450 Euro als Fassung B. 2027 bleibt in `saetze.json` leer: der Rücktest verlangt, dass ein fehlender Satz dort ein sichtbarer Konfigurationsfehler ist. Der Satz 2027 steht im Regelregister und in `daten/zahlen-werte.json`. Die Next-Rechnung rechnet weiter nur freigegebene Sätze; die JSON-Datei erteilt keine Freigabe. Der Python-Kern rechnet die Sätze 2015–2027 schon aus `parameter.json`.

`daten/zahlen-werte.json`: Ehrenamtspauschale zeigt auf KSK-Info 24, 24a (vorher fälschlich Info 10). Die 450-Euro-Zeile 2019–2024 ist geteilt: 2019–2022 Fassung A (BSG B 3 KS 3/21 R Rn. 18) und 2023–2024 Fassung B (§ 24 Abs. 2 Satz 2). Der Chat-Kontext nimmt die Fundstelle der einzelnen Zeile. Abgabesätze 2015–2024 und 2027 stehen jahrweise mit der Fundstelle aus dem Regelregister; 2026 endet am 31.12.2026, damit 4,9 Prozent nicht still in 2027 weitergilt.

`taetigkeit.synonym` „eigenwerbung“ ist umgezogen auf `szenarien.eigenwerbung` (KSVG § 24 Abs. 2 Satz 1 Nummer 1). `pruefe_eigenwerbung` bleibt. Ein Text, der nur „Eigenwerbung“ nennt, ist keine bekannte Tätigkeit.

`offen.waehrung`: Fremdwährung ohne Umrechnungsnachweis bleibt Rückfrage. Text und Fundstelle (Testfall L-23, keine Umrechnungsregel in der Quellenbasis) stehen im Register. T-048 und E-009 bleiben OFFEN.

Zusätzlich, weil die kürzeren Wörter schon trafen und die Suiten gleich blieben: `verpflegungsmehraufwand` unter `auslage.mit_beleg_ausgenommen` (KSVEntgV § 1 Nr. 1), `plakatrahmen` unter `auslage.gehoert_zum_entgelt` (Info 10, S. 1).

Die Datei `aufgaben/audit/vorschlag_begriffe_excel_2026-10-18.md` gibt es nicht. Der Begriffs-Fix Konzert/Musik steht schon in der Excel (T-07) und in `app/taetigkeiten.py`.

## Weiter bewusst nicht automatisiert

Die Liste unten gilt unverändert. Insbesondere nicht nachgetragen, weil die Quelle es nicht hergibt:

- Stadt, Landkreis, Gemeinde, Amt, Behörde nicht unter `rechtsform.kein_entgelt`. Info 11, S. 1: sie können abgabepflichtig sein.
- Programmierung und Softwareentwicklung nicht ausgeschlossen. Info 06 nennt sie nicht.
- Logo und Briefkopf nicht als künstlerisch. In Info 02 und Info 06 nicht wörtlich. Das Aktenzeichen BSG B 3 KR 37/04 R liegt nicht unter `quellen/`.
- `lizenz.auffuehrungsmaterial` nicht ausgenommen. § 25 Abs. 2 Nr. 1 nimmt Verwertungsgesellschaften aus, nicht Aufführungsmaterial eines Verlags.
- Stämme wie Kabarett, Comedy, Malerei, Zauberei nicht zusätzlich zu den wörtlichen Berufsformen.

## Erwartungen, die sich geändert haben

| ID | vorher | nachher | Warum |
| --- | --- | --- | --- |
| T-093 | OFFEN | ZAEHLT | Webdesign ist der Katalogberuf Web-Designer (KSK-Info 06, S. 3) und Webdesigner (KSK-Info 12, S. 2). 1.500 Euro übersteigen die Schwelle 2026. |
| E-017 | OFFEN | ZAEHLT | Dieselbe Quelle. |
| E-024 | OFFEN | ZAEHLT | Maskenbildner steht in KSK-Info 06, S. 2, und in Info 09, S. 4, Fußnote 6 für Bühne/Film. Der Text nennt ein Theaterstück. 400 Euro übersteigen die Schwelle 2026 nicht; die Suite nennt beide entschiedenen Klassen ZAEHLT. |

## Bewusst nicht automatisiert

- Übersetzung, Übersetzerin, Kunstunterricht, Gesangsunterricht, Stimmcoaching, Lektorat: Rückfrage. Info 06 setzt beim Übersetzer die Fußnote „Besonderheit“. Unterricht ist im Katalog das Lehren, nicht die einzelne Stunde.
- Softwareentwicklung und Programmierung: Info 06 schließt sie nicht aus und nennt sie nicht. Bleibt nicht abgedeckt. Kein stiller Ausschluss.
- Logo, Briefkopfgestaltung: in Info 02 und Info 06 nicht wörtlich. E-022 und T-098 bleiben OFFEN. Corporate-Design steht wörtlich in Info 02 und ist eingetragen.
- Comedy, Kabarett, Puppenspiel, Zauberei: die PDFs nennen Comedian, Kabarettist, Puppenspieler, Zauberer. Nur diese Formen sind Synonyme.
- Fotolabor, Vertrieb, Handel, Galeriehandel, Unterricht als Ausschluss: in Info 09 nicht als Ausschluss der Abgabe formuliert. Nicht eingetragen.
- Dolmetscher: Info 09, S. 4, Fußnote 1, im Regelfall kein Künstler/Publizist. E-023 bleibt OFFEN, kein Automatismus.
- Stadt, Landkreis, Gemeinde: Info 11, S. 1, sie können abgabepflichtig sein. Deshalb keine Zeile unter `rechtsform.kein_entgelt`. Schlüssel `auftraggeber.kommune` hält das fest.
- Gemeinnützigkeit: Info 23, keine Befreiung und kein Automatismus in die andere Richtung. Der Schlüssel ändert keine Klasse.
- Gesellschafter einer GmbH: Merkblatt S. 1–2, Rückfrage, sobald das Wort Gesellschafter als eigenes Wort steht.
- Ausland: Info 22, die Abgabe entfällt nicht schon wegen des Auslands. Rückfrage zum Status nach deutschem Recht.
- Verlag allgemein: KSVG § 25 Abs. 2 Nr. 1 nimmt Verwertungsgesellschaften aus, nicht jeden Verlag. Aufführungsmaterial als Analogie wurde nicht eingetragen. Musikverlag mit dem Wort Verwertung bleibt die bisherige Ausnahme (T-026).
- Info 20 (Kunstvereine) enthält die Schülerstaffel nicht. Die 20 und die Mitte bis unter 61 stehen aus Info 12, S. 2, Punkt 1 und 2. Die 60 bleibt `musikverein.schueler_grenze`.
- BSG 07.07.2005, B 3 KR 37/04 R, liegt nicht unter `quellen/ergaenzend/urteile`. Webdesign stützt sich auf Info 06 und Info 12, nicht auf dieses Urteil.

## Neue Zeilen

| Schluessel | Wert | Regel | Fundstelle |
| --- | --- | --- | --- |
| taetigkeit.synonym | clown | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: clown |
| taetigkeit.synonym | comedian | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: comedian |
| taetigkeit.synonym | kabarettist | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: kabarettist |
| taetigkeit.synonym | komiker | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: komiker |
| taetigkeit.synonym | illustrator | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: illustrator |
| taetigkeit.synonym | journalist | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: journalist |
| taetigkeit.synonym | kostümbildner | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: kostümbildner |
| taetigkeit.synonym | grafiker | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: grafiker |
| taetigkeit.synonym | bildhauer | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: bildhauer |
| taetigkeit.synonym | choreograph | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: choreograph |
| taetigkeit.synonym | fotograf | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: fotograf |
| taetigkeit.synonym | maler | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: maler |
| taetigkeit.synonym | maskenbilder | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: maskenbilder |
| taetigkeit.synonym | redakteur | Info-06 | KSK-Info 06, Stand 09.2025, S. 2, Katalog künstlerische/publizistische Tätigkeiten: redakteur |
| taetigkeit.synonym | musiker | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: musiker |
| taetigkeit.synonym | sänger | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: sänger |
| taetigkeit.synonym | schriftsteller | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: schriftsteller |
| taetigkeit.synonym | sprecher | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: sprecher |
| taetigkeit.synonym | synchronsprecher | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: synchronsprecher |
| taetigkeit.synonym | puppenspieler | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: puppenspieler |
| taetigkeit.synonym | marionettenspieler | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: marionettenspieler |
| taetigkeit.synonym | pantomime | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: pantomime |
| taetigkeit.synonym | zauberer | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: zauberer |
| taetigkeit.synonym | visagist | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: visagist |
| taetigkeit.synonym | instrumentalsolist | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: instrumentalsolist |
| taetigkeit.synonym | webdesigner | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: webdesigner |
| taetigkeit.synonym | web-designer | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: web-designer |
| taetigkeit.synonym | webdesign | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: webdesign |
| taetigkeit.synonym | maskenbildner | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: maskenbildner |
| taetigkeit.synonym | publizist | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: publizist |
| taetigkeit.synonym | reporter | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: reporter |
| taetigkeit.synonym | kritiker | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: kritiker |
| taetigkeit.synonym | herausgeber | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: herausgeber |
| taetigkeit.synonym | liedermacher | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: liedermacher |
| taetigkeit.synonym | songwriter | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: songwriter |
| taetigkeit.synonym | texter | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: texter |
| taetigkeit.synonym | layouter | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: layouter |
| taetigkeit.synonym | comiczeichner | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: comiczeichner |
| taetigkeit.synonym | karikaturist | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: karikaturist |
| taetigkeit.synonym | rezitator | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: rezitator |
| taetigkeit.synonym | drehbuchautor | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: drehbuchautor |
| taetigkeit.synonym | filmemacher | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: filmemacher |
| taetigkeit.synonym | regisseur | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: regisseur |
| taetigkeit.synonym | komponist | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: komponist |
| taetigkeit.synonym | autor | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: autor |
| taetigkeit.synonym | pressefotograf | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: pressefotograf |
| taetigkeit.synonym | werbefotograf | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: werbefotograf |
| taetigkeit.synonym | game-designer | Info-06 | KSK-Info 06, Stand 09.2025, S. 3, Katalog künstlerische/publizistische Tätigkeiten: game-designer |
| taetigkeit.synonym | corporate-design | Info-02 | KSK-Info 02, S. 1, Abschnitt 4: Corporate-Design ist eine Design-Leistung, die vom KSVG erfasst ist. |
| taetigkeit.offen | übersetzung | Info-06-Offen | KSK-Info 06, S. 3: Übersetzer/Bearbeiter mit Fussnote * (Besonderheiten, schriftlich bei der KSK anfragen). Literarisch oder Fachübersetzung entscheidet der Einzelfall. |
| taetigkeit.offen | übersetzer | Info-06-Offen | KSK-Info 06, S. 3: Übersetzer/Bearbeiter mit Fussnote *. Keine stille Wahl zwischen literarisch und Fachübersetzung. |
| taetigkeit.offen | übersetzerin | Info-06-Offen | KSK-Info 06, S. 3: Übersetzer/Bearbeiter mit Fussnote *. Keine stille Wahl zwischen literarisch und Fachübersetzung. |
| taetigkeit.offen | uebersetzung | Info-06-Offen | KSK-Info 06, S. 3: Übersetzer/Bearbeiter mit Fussnote *. Keine stille Wahl zwischen literarisch und Fachübersetzung. |
| taetigkeit.offen | uebersetzer | Info-06-Offen | KSK-Info 06, S. 3: Übersetzer/Bearbeiter mit Fussnote *. Keine stille Wahl zwischen literarisch und Fachübersetzung. |
| taetigkeit.offen | kunstunterricht | Info-06-Offen | KSK-Info 06, S. 1: Künstler ist auch, wer Kunst lehrt; S. 2 nennt Lehrer für künstlerische Tätigkeiten. Ob die konkrete Stunde nur Unterricht ist, sagt der Katalog nicht. |
| taetigkeit.offen | gesangsunterricht | Info-06-Offen | KSK-Info 06, S. 3 nennt Musiklehrer, nicht die einzelne Gesangsstunde. Darbietung oder pädagogische Vermittlung bleibt Einzelfall. |
| taetigkeit.offen | stimmcoaching | Info-06-Offen | KSK-Info 06 nennt Sprecherzieher und Musiklehrer, nicht Stimmcoaching. Pädagogische Vermittlung oder Darbietung ist nicht entschieden. |
| taetigkeit.offen | lektor | Info-06-Offen | KSK-Info 06, S. 2 führt Lektor auf. Info 09, S. 4, Abschnitt 3.2: bei mehreren Leistungsanteilen entscheidet der überwiegende Teil. Kein Automatismus. |
| taetigkeit.offen | lektorat | Info-06-Offen | KSK-Info 06, S. 2 führt Lektor auf. Info 09, S. 4, Abschnitt 3.2: bei mehreren Leistungsanteilen entscheidet der überwiegende Teil. Kein Automatismus. |
| ausland.kuenstler | ausländisch | Info-22 | KSK-Info 22, Stand 10.2025, S. 1-2, Abschn. 2 und 6: Abgabe auf selbständige ausländische Künstler ja, abhängige Beschäftigung und A1-Bescheinigung nein. Status nach deutschem Recht ist zu klären. |
| ausland.kuenstler | auslaendisch | Info-22 | KSK-Info 22, Stand 10.2025, S. 1-2, Abschn. 6: Die KSK prüft selbständige oder abhängige Tätigkeit nach deutschem Recht. Bescheinigungen des Auslands sind kein Nachweis. |
| ausland.kuenstler | auslandssachverhalt | Info-22 | KSK-Info 22, Stand 10.2025, S. 1 Abschn. 2: Auslandsbezug hebt die Abgabe nicht auf. Ob ein abhängiges Beschäftigungsverhältnis vorliegt, ist zu klären. |
| gemeinnuetzig | gemeinnützig | Info-23 | KSK-Info 23, Stand 01.2026, S. 1 Abschn. 2: Gemeinnützigkeit befreit nicht und begründet die Abgabe nicht allein. Befreiungstatbestände sind nicht vorgesehen. |
| gemeinnuetzig | gemeinnuetzig | Info-23 | KSK-Info 23, Stand 01.2026, S. 1 Abschn. 2: Gemeinnützigkeit befreit nicht und begründet die Abgabe nicht allein. |
| auftraggeber.kommune | stadt | Info-11 | KSK-Info 11, Stand der Datei, S. 1 Abschn. 1-2: Städte, Landkreise und Gemeinden können abgabepflichtig sein. Das ist kein Ausschluss wie eine Zahlung an eine öffentliche Körperschaft als Empfänger. |
| auftraggeber.kommune | landkreis | Info-11 | KSK-Info 11, Stand der Datei, S. 1 Abschn. 1-2: Städte, Landkreise und Gemeinden können abgabepflichtig sein. Das ist kein Ausschluss wie eine Zahlung an eine öffentliche Körperschaft als Empfänger. |
| auftraggeber.kommune | gemeinde | Info-11 | KSK-Info 11, Stand der Datei, S. 1 Abschn. 1-2: Städte, Landkreise und Gemeinden können abgabepflichtig sein. Das ist kein Ausschluss wie eine Zahlung an eine öffentliche Körperschaft als Empfänger. |
| gesellschafter.gmbh | gesellschafter | Gesellschafter | KSK-Merkblatt Gesellschafter einer GmbH, S. 1-2: Mitarbeitender Gesellschafter ist nur bei maßgeblichem Einfluss selbständig. Künstlerischer Anteil und Oberleitung prüft die KSK. BSG 16.04.1998, B 3 KR 7/97 R, im Merkblatt zitiert. |
| musikverein.schueler_unter | 20 | Info-12-P1 | KSK-Info 12, Stand 01.2026, S. 2 Punkt 1: nicht mehr als 20 Schüler, dem Grunde nach keine Abgabepflicht nach § 24 Abs. 1 Nr. 9 KSVG. |
| musikverein.schueler_mitte | vermutung | Info-12-P2 | KSK-Info 12, Stand 01.2026, S. 2 Punkt 2: mehr als 20 und weniger als 61 Schüler, Vermutung keine Abgabepflicht nach § 24 Abs. 1 Nr. 9, wenn kein Ausbilder über der Übungsleiterpauschale liegt. |
| entgelt.ausgenommen | gema | KSVG-25 | KSVG § 25 Abs. 2: Entgelte für Nutzungsrechte an Verwertungsgesellschaften sind ausgenommen (Gesetzestext im Repo, Seite 9). |
| entgelt.ausgenommen | verwertungsgesellschaft | KSVG-25 | KSVG § 25 Abs. 2 Nr. 1: Entgelte an Verwertungsgesellschaften für urheberrechtliche Nutzungsrechte gehören nicht zum Entgelt. |
| entgelt.ausgenommen | verwertung | KSVG-25 | KSVG § 25 Abs. 2 Nr. 1: Zahlung wegen Verwertung an eine Verwertungsgesellschaft, nicht schon jede Verlagsleistung. |
| entgelt.ausgenommen | musikverlag | KSVG-25 | KSK-Checkliste Verlage und KSVG § 25 Abs. 2 Nr. 1: Lizenzzahlung, die als Verwertung ausgewiesen ist. Ein Verlag ist nicht schon deshalb eine Verwertungsgesellschaft. |
| auslage.mit_beleg_ausgenommen | reise | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | fahrt | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | hotel | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | übernachtung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | uebernachtung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | verpflegung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1: nachgewiesene Reisekosten innerhalb der Grenzen des § 3 Nr. 16 EStG zählen nicht. KSK-Info 10, S. 2. |
| auslage.mit_beleg_ausgenommen | bewirtung | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.mit_beleg_ausgenommen | auslage | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.mit_beleg_ausgenommen | materialkosten | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.mit_beleg_ausgenommen | notenmappe | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.mit_beleg_ausgenommen | notenkauf | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.mit_beleg_ausgenommen | kostenübernahme | KSVEntgV-1 | KSVEntgV § 1 und KSK-Info 10: nur die dort genannten nachgewiesenen Nebenleistungen fallen aus der Bemessung. Beleg erforderlich. |
| auslage.auch_ohne_beleg_ausgenommen | notenkauf | KSVEntgV-1 | Weiterberechnete Auslage Noten oder Kostenübernahme, wie bisher im Register auslage.nachgewiesen geführt. |
| auslage.auch_ohne_beleg_ausgenommen | kostenübernahme | KSVEntgV-1 | Weiterberechnete Auslage Noten oder Kostenübernahme, wie bisher im Register auslage.nachgewiesen geführt. |
| auslage.auch_ohne_beleg_ausgenommen | notenmappe | KSVEntgV-1 | Weiterberechnete Auslage Noten oder Kostenübernahme, wie bisher im Register auslage.nachgewiesen geführt. |
| auslage.ohne_beleg_offen | auslage | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | materialkosten | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | reise | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | fahrt | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | hotel | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | übernachtung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | uebernachtung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.ohne_beleg_offen | verpflegung | KSVEntgV-1 | KSVEntgV § 1 Nr. 1 und Info 10: ohne Nachweis keine Ausnahme. Verpflegung zusätzlich an verpflegung.stunden_grenze und verpflegung.stunden_ganztag im Register gebunden. |
| auslage.gehoert_zum_entgelt | porto | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | versand | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | kopierkosten | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | rahmen | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | plakat | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | scanner-miete | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
| auslage.gehoert_zum_entgelt | notenmaterial | Info-10 | KSK-Info 10, S. 1: Auslagen und Nebenkosten, die dem Künstler vergütet werden, gehören zum Entgelt. Ausnahme nur Umsatzsteuer, Verwertungsgesellschaft, Reise und übliche Bewirtung. |
