# Auswertung Tätigkeitskatalog (200 Tätigkeiten, 15.10.2026)

Entwurf – vom Steuerberater zu prüfen. Erfundener Rahmen: typischer Verwerter, Einzelperson, 2.000 € (künstlerisch = 98,00 €). Die Soll-Kategorien sind ein KI-gestützter Entwurf des Nutzers, nicht geprüft. Katalog: `aufgaben/audit/taetigkeitskatalog_200.json`. Für den Steuerberater: `regelwerk/Pruefliste_Taetigkeiten_Nachtrag_1_Entwurf.xlsx` (alle 200, Abweichungen und Lücken zuerst).

## Messung

1. **Excel-Blatt „Tätigkeitsabgrenzung“ (feste Erkennung, ohne Modell):** 64 Treffer, 96 Lücken (nicht im Blatt), 40 Abweichungen.
2. **Ganzes System im Demo-Modus** (Rahmensatz, Knöpfe 'typischer Verwerter' und 'natürliche Person'):

| Entwurf | abgabepflichtig | nicht abgabepflichtig | Grenzfall | Rückfrage |
|---|---|---|---|---|
| künstlerisch | 47 | 0 | 2 | 14 |
| nicht künstlerisch | 0 | 4 | 5 | 38 |
| Grenzfall | 36 | 2 | 20 | 32 |

Die Rückfragen im Demo-Modus sind Tätigkeiten, die das Blatt nicht kennt: der Demo-Modus nennt dann keine Leistung, das System fragt (ehrlich, keine Schleife). Live ordnet das Modell ein; ein Ausschluss 'nicht künstlerisch' allein durch das Modell gilt seit 15.10.2026 als Grenzfall.

## Gefunden und behoben (neue Zeilen im Blatt, alte Zeilen unverändert)

Vorher ergaben 5 Tätigkeiten mit Entwurf 'nicht künstlerisch' still 98,00 € und 9 mit Entwurf 'Grenzfall' still 0 €:

| Neu | Tätigkeit | Gruppe | Vorher | Grundlage |
|---|---|---|---|---|
| T-70 | reine Textkorrektur | nicht künstlerisch | 'Lektor (nur Textkorrektur)' = Lektorat (T-09) | R-194 (Checkliste Verlage) |
| T-71 | Unterricht/Coaching in Musik, darstellender, bildender Kunst | Grenzfall | Schauspiel-Coach, Dirigenten-Workshop, Pantomimen-Lehrer u. a. = Coaching (T-34), still N | KSVG § 2 ('lehrt') gegen R-183 |
| T-72 | technische Zeichnung | Grenzfall | 'technischer Zeichner' = Zeichnung (T-08), still A | R-137 |
| T-73 | Playlist/Musikauswahl | Grenzfall | 'Musikdaten-Kurator' = Musik (T-07), still A | R-137 |
| T-74 | Fotogrammetrie/Vermessung | Grenzfall | als Fotografie gerechnet | R-137 |
| T-75 | Sync-Agent (Rechtevermittlung) | Grenzfall | als Musik gerechnet | R-219 |

Außerdem (Code, keine neue Fachaussage): verneint der Text einen Begriff der gewählten Zeile ('Plakatierung, keine Gestaltung'), ist die Einordnung nicht eindeutig (AT-036).

Nachher: 0 Tätigkeiten 'nicht künstlerisch' → abgabepflichtig. 2 mit Entwurf 'Grenzfall' → nicht abgabepflichtig, beide mit Fundstelle im Blatt: SEO-Berater (T-31, R-182) und Schreib-Coach (T-34, R-183; § 2 KSVG nennt 'lehrt' nur beim Künstler, nicht beim Publizisten).

## Abweichungen Entwurf ↔ Blatt (Frage Q-35)

| Nr. | Tätigkeit | Entwurf | Blatt | System |
|---|---|---|---|---|
| A-10 | Zeichner (architektonische Zeichnung als Kunstwerk) | Grenzfall | T-08 (kuenstlerisch) | abgabepflichtig |
| A-11 | technischer Zeichner (Bauzeichnung) | nicht künstlerisch | T-72 (unsicher) | Grenzfall |
| A-20 | Restaurator (Gemaelde) | Grenzfall | T-16 (kuenstlerisch) | abgabepflichtig |
| B-24 | DJ (Musik mixt live) | Grenzfall | T-07 (kuenstlerisch) | abgabepflichtig |
| B-27 | Arrangeur | Grenzfall | T-07 (kuenstlerisch) | abgabepflichtig |
| B-28 | Musikproduzent (nur Tonstudio) | Grenzfall | T-07 (kuenstlerisch) | abgabepflichtig |
| B-29 | Tonmeister (Tontechnik) | nicht künstlerisch | T-64 (unsicher) | Grenzfall |
| B-32 | Chorleiter (regelmassig, Musikverein) | Grenzfall | T-07 (kuenstlerisch) | abgabepflichtig |
| C-43 | Taenzer (Musikvideo) | künstlerisch | widerspruch (unsicher) | Grenzfall |
| C-50 | Moderator (nur durchs Interview leiten) | Grenzfall | T-12 (kuenstlerisch) | abgabepflichtig |
| D-68 | Werbetexter (Slogan) | Grenzfall | T-03 (kuenstlerisch) | abgabepflichtig |
| D-69 | Pressetext-Schreiber | Grenzfall | T-03 (kuenstlerisch) | abgabepflichtig |
| D-75 | Illustrator-Texter (Kombirechnung) | Grenzfall | T-03 (kuenstlerisch) | abgabepflichtig |
| E-86 | Food-Fotograf | Grenzfall | T-04 (kuenstlerisch) | abgabepflichtig |
| E-89 | Kameramann (reine Industrie-Doku) | Grenzfall | T-13 (kuenstlerisch) | abgabepflichtig |
| E-91 | Cutter (Schnitt nach Regieanweisung) | Grenzfall | T-13 (kuenstlerisch) | abgabepflichtig |
| E-96 | Skript-Autor (Doku) | Grenzfall | T-19 (kuenstlerisch) | abgabepflichtig |
| F-102 | UX/UI-Designer | Grenzfall | T-01 (kuenstlerisch) | abgabepflichtig |
| F-107 | Schuh-Designer | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| F-109 | Interior-Designer (Raumkonzept) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| F-111 | SEO-Berater | Grenzfall | T-31 (nicht_kuenstlerisch) | nicht abgabepflichtig |
| F-114 | Newsletter-Layout (nur Umsetzung) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| F-117 | Influencer (Product-Placement) | Grenzfall | T-14 (kuenstlerisch) | abgabepflichtig |
| F-120 | KI-Prompt-Designer (Midjourney-Grafiken) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| G-125 | Maskenbildner (Film) | künstlerisch | T-66 (unsicher) | Grenzfall |
| G-133 | Schmuck-Designer (Unikat) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| H-144 | Schreib-Coach | Grenzfall | T-34 (nicht_kuenstlerisch) | nicht abgabepflichtig |
| H-154 | Escape-Room-Designer | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| I-163 | Social-Media-Redakteur (Texte nach Vorgabe) | Grenzfall | T-03 (kuenstlerisch) | abgabepflichtig |
| I-166 | Sprecher-Demo (Sprachnachricht-Produktion) | Grenzfall | T-05 (kuenstlerisch) | abgabepflichtig |
| I-167 | Moderator (Firmenevent, nur durch Programm fuehren) | Grenzfall | T-12 (kuenstlerisch) | abgabepflichtig |
| J-181 | Game-Artist (Charakterdesign) | Grenzfall | T-15 (kuenstlerisch) | abgabepflichtig |
| J-182 | Sound-Designer (Games) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| J-184 | Stream-Grafik-Designer (Overlays) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| J-185 | VTuber-Model-Designer | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| J-187 | AR-Filter-Designer | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| J-188 | VR-Erlebnis-Designer (Museum) | Grenzfall | T-02 (kuenstlerisch) | abgabepflichtig |
| J-191 | Musikdaten-Kurator (Playlist) | nicht künstlerisch | T-73 (unsicher) | Grenzfall |
| J-192 | Filmmusik-Sync-Agent (Vermittlung) | nicht künstlerisch | T-75 (unsicher) | Grenzfall |
| J-199 | Fotogrammetrie (Vermessung) | nicht künstlerisch | T-74 (unsicher) | Grenzfall |

## Lücken: nicht im Blatt (Frage Q-34)

**Entwurf künstlerisch (21):** A-01 Maler (Oelgemaelde fuer Firmensitz); A-07 Graffiti-Kuenstler (Fassadenwerk); A-08 Airbrush-Kuenstler; A-09 Radierer/Lithograph; A-14 Kalligraf; B-22 Band (GbR); B-34 Strassenmusiker (gebucht fuer Event); B-35 Rapper (Feature); C-53 Filmschauspieler (Kurzfilm); C-56 Performer (Flashmob fuer Marke); C-59 Bauchredner; C-60 Poesie-Slammer (Firmenevent); D-64 Freier Reporter (Firma-Reportage); D-65 Kolumnist; D-77 Pressefotograf (Presse-Termin); E-81 Kunstfotograf (Ausstellungswerk); E-83 Werbefotograf (Produktkampagne); E-84 Hochzeitsfotograf (privat); E-87 Modeschöpfer/Modefotograf (Editorial); G-135 Glaskuenstler; J-200 Kuenstlerische Lichtinstallation.

**Entwurf nicht künstlerisch (38):** A-16 Siebdrucker (nur Ausfuehrung); A-18 Goldschmied (Serienware); A-19 Museums-Gaestefuehrer; B-30 Livemischer (Mischpult); B-39 Klavierstimmer; C-55 Statist; D-73 Dolmetscher (Verhandlung); E-92 Videoproduzent (nur Produktion/Orga); E-95 Lichttechniker; F-112 SEA-Manager; F-115 Social-Media-Manager (Community); G-121 Tapezierer (Raumausstattung); G-122 Florist (Gestecke); G-123 Friseur (Frisur fuer Shoot); G-129 Schreiner (Moebel nach Entwurf); G-131 Drucker (Auflage); G-137 Schneider (Massanfertigung); G-139 Modellbauer (Architekturmodell); H-145 Yoga-Lehrer; H-150 Sprachlehrer; H-151 Nachhilfelehrer; H-153 Trainer (MS-Office); I-161 Pressesprecher (fuer die Firma); I-162 PR-Berater (Strategie); I-168 Zeremonienmeister; I-170 Auktionator; I-172 Museumspaedagoge (Werkstatt); I-173 Kunstscout (Sammlungsberatung); I-174 Kunstversicherungs-Gutachter; I-175 Kunstspediteur; I-176 Rahmenbauer; I-177 Kunsttransport (Aufbau); I-178 Galerist (Vermittlung fuer uns); I-179 Kunsthändler; I-180 Kunstauktionshaus-Berater; J-193 Orchester-Manager; J-194 Buehnen-Techniker; J-195 Pyrotechniker.

**Entwurf Grenzfall (37):** A-13 Photoshop-Retuscheur (reine Retusche); A-15 Typograf (Schriftgestaltung); A-17 Kunsthandwerker (Unikat-Schmuck entworfen); B-36 Beatproduzent (Beats verkaufen); B-40 Notensetzer (nur Notensatz); D-67 Ghostwriter (Rede fuer CEO); D-70 Blogger (Gesponserte Posts); D-71 Fachautor (Sachbuch); D-74 Synchronautor (Untertitel); D-79 Interviewer (Fuer Podcast-Format); E-100 3D-Visualisierer (Produktfilm); E-82 Portraetfotograf (Firmenportraets); E-85 Architekturfotograf (Gebaeude-Report); E-93 Drone-Operator (Luftaufnahmen); E-94 Steadicam-Operator; E-98 Farbist (Colorgrading); F-108 Industriedesigner (Möbel); F-116 Content-Creator (Instagram-Reels); F-118 Podcast-Produzent (eigener Podcast); F-119 NFT-Kuenstler ( digitale Serie); G-128 Requisitenbauer (nach Entwurf); G-130 Schreiner (eigener kuenstlerischer Entwurf); G-132 Buchbinder (Unikat-Kuenstlerbindung); G-134 Keramiker (Kunstkera mik Unikat); G-136 Goldschmied (kunsthandwerkliche Unikate); G-138 Schneider (Kostuem nach eigenem Entwurf); G-140 Schildermaler (Handlettering-Unikat); H-155 Quizmaster (eigenes Format); I-164 Copywriter (Website-Texte); I-165 Speechwriter (poln. Rede); I-169 Trauredner (freie Zeremonie); I-171 Ausstellungskurator (eigenes Konzept); J-186 Avatar-Ersteller; J-189 Datenjournalist (Visualisierung); J-190 Infografiker; J-196 Requisiteur (Auswahl nach Regie); J-197 Kamera-Drohnen-Pilot (künstlerische Flugaufnahmen).

## Noch offen

- Nach der Entscheidung des Steuerberaters: neue Zeilen im Blatt, dann die 200 als feste Testkategorie ins Testarchiv (Soll-Kategorie je Fall).

## Nachtrag: 20 Stichproben live (Lauf 38689077130, Stand 031309a, je 6 Läufe, Mistral EU)

Rohe Modellfakten: `aufgaben/audit/modellfehler_fakten_{mit,ohne}_38689077130.jsonl`.

| Tätigkeit | Entwurf | Blatt | Ergebnis (6 Läufe) | Einordnung |
|---|---|---|---|---|
| Maler (Ölgemälde) | K | – | 6 richtig | Modell ordnet ein |
| Sänger | K | T-07 | 6 richtig | |
| Journalist | K | T-03 | 6 richtig | |
| Kunstfotograf | K | – | 6 richtig | Modell ordnet ein |
| Webdesigner | K | T-01 | 6 richtig | |
| Tänzer (Musikvideo) | K | Widerspruch | 6 nachgefragt | Blatt: 'Tänzer' Grenzfall (T-64) – Q-35 |
| Lektor (nur Textkorrektur) | N | T-70 | 6 richtig | neue Zeile wirkt |
| Hosting-Administrator | N | T-30 | 6 richtig | |
| Florist | N | – | 6 nachgefragt | Lücke (Q-34) |
| MS-Office-Trainer | N | – | 4 richtig, 2 nachgefragt | Lücke (Q-34) |
| Pressesprecher | N | – | 3 nachgefragt, **3 abgabepflichtig** | Lücke: das Modell stuft ihn als publizistisch ein (Q-34) |
| Fotogrammetrie | N | T-74 | 6 nachgefragt | neue Zeile wirkt (vorher still abgabepflichtig) |
| technischer Zeichner | N | T-72 | 6 nachgefragt | neue Zeile wirkt (vorher still abgabepflichtig) |
| Playlist-Kurator | N | T-73 | 6 nachgefragt | neue Zeile wirkt (vorher still abgabepflichtig) |
| DJ | G | T-07 | 6 abgabepflichtig | Blatt (KSK-Info 06) gegen Entwurf – Q-35 |
| Moderator (Interview) | G | T-12 | 6 abgabepflichtig | Blatt gegen Entwurf – Q-35 |
| SEO-Berater | G | T-31 | 6 nicht abgabepflichtig | Blatt (R-182) gegen Entwurf – Q-35 |
| Influencer | G | T-14 | 6 abgabepflichtig | Blatt gegen Entwurf – Q-35 |
| Visagist | G | T-66 | 6 richtig (Grenzfall) | |
| Schauspiel-Coach | G | T-71 | 6 richtig (Grenzfall) | neue Zeile wirkt (vorher still nicht abgabepflichtig) |

Ergebnis: Wo das Blatt eine Zeile hat, entscheidet das System in allen 6 Läufen gleich (stabil). Abweichungen vom Entwurf sind Abweichungen zwischen Blatt und Entwurf, keine Zufallsfehler – sie stehen in der Prüfliste. Einziger schwankender Fall: Pressesprecher (nicht im Blatt; Modell entscheidet).
