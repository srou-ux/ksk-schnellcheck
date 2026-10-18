# Prüfmethodik v12

Stand der Methodik: 2026-10-05. Kennung: `v12`.
Quellenstempel der Normen: Q-KSVG@2026-10-05, Q-KSVENTGV@2026-10-05.
Diese Fassung ist eingefroren. Eine Änderung ist eine neue Version mit neuem Rücktest. Bestehende Berichte behalten `v12`. IDs werden nicht still umgedeutet.

Die verbindliche Einordnung trifft der Code, der diese Datei abbildet (`src/lib/domain/evaluate.ts`), gegen `rules/saetze.json` und `rules/szenarien.json`. Ein Sprachmodell darf Beträge nicht verändern, keine Fundstelle erfinden und keine Einordnung gegen den Code setzen. Widerspricht der Prüfer-Call dem Code, endet der Lauf ohne Bericht.

## Grundsatz

Unlesbar bleibt unlesbar. Drei Ablesungen ohne Gleichlaut ergeben UNGEKLÄRT, nach drei Versuchen ebenfalls. UNGEKLÄRT ist ein Ergebnis und braucht eine Begründung in Alltagssprache. Eine ehrliche Verweigerung ist besser als eine falsche Analyse.

Formularwerte führen. Ein abweichender Fließtext wird genannt, ersetzt den Formularwert aber nicht.

Alle Beträge sind Ganzzahl-Cent. Rundung der Abgabe: siehe `saetze.json` (`half_up_integer_cents`).

## Was eine einzelne Rechnung leisten kann

Die Künstlersozialabgabe trifft den zur Abgabe verpflichteten Unternehmer, nicht die Rechnung als solche. Eine Rechnung kann die Entgelte zeigen. Ob der Auftraggeber überhaupt zum Personenkreis des § 24 KSVG gehört und ob im Kalenderjahr weitere Entgelte hinzukommen, steht oft nicht auf dem Blatt. Was die Rechnung nicht trägt, wird UNGEKLÄRT.

## Personenkreis

- Typischer Verwerter, § 24 Abs. 1 KSVG: keine Jahresgrenze.
- Eigenwerbung, § 24 Abs. 2 Satz 1 Nummer 1 KSVG: Jahresgrenze.
- Generalklausel, § 24 Abs. 2 Satz 1 Nummer 2 KSVG: Jahresgrenze.
- Rolle nicht erkennbar: UNGEKLÄRT. Keine stillschweigende Einordnung als Verwerter und keine stillschweigende Freistellung.

Die Jahresgrenze steht jahrweise in `saetze.json`. 2025: 700 Euro (§ 54 KSVG). 2026: 1.000 Euro (§ 24 Abs. 2 Satz 2 KSVG). „Übersteigen“ heißt: größer als die Grenze, nicht gleich. Genau die Grenze ist noch keine Abgabepflicht nach Absatz 2, wenn die Jahressumme bestätigt ist (Rücktest S3a).

Ist die Jahressumme nicht bestätigt, entscheidet eine einzelne Rechnung unterhalb oder auf der Grenze nichts. Ergebnis: UNGEKLÄRT (Rücktest 390-Euro-Fall). Liegt die bestätigte Jahressumme über der Grenze, gehört die gesamte Summe zur Bemessungsgrundlage, nicht nur der übersteigende Teil.

Fehlt ein Jahr in `saetze.json`, ist das ein sichtbarer Konfigurationsfehler. 2027 ist eine solche Lücke. Es wird kein Satz angenommen.

## Entgelt

§ 25 Abs. 2 Satz 1 KSVG: Entgelt ist alles, was aufgewendet wird, um das Werk oder die Leistung zu erhalten oder zu nutzen, ohne gesondert ausgewiesene Umsatzsteuer.

Gesondert ausgewiesene Umsatzsteuer ist nicht Bemessungsgrundlage.

Honorar, Material, sonstige Auslagen, Reise, Bewirtung, gemischte Zeilen und weiterberechnete Drittleistungen bleiben in der Bemessungsgrundlage, solange keine belegte Ausnahme aus der hinterlegten Regel greift. Die Pipeline nimmt nichts vorweg aus der Bemessungsgrundlage. Ein Hinweis ist kein Abzug.

Gesellschaft als Vertragspartnerin: nach der hinterlegten FAQ-Regel nicht Bemessungsgrundlage. Ist der Empfänger nicht eindeutig eine Gesellschaft, bleibt er UNGEKLÄRT.

## Klärungshinweise

Nur bei abgabepflichtiger Einordnung und nur mit einem Grund aus `szenarien.json`.

- Reise: unselbstständig. Nachweis wirkt nur für Kosten in der Person des Künstlers oder Publizisten innerhalb § 3 Nr. 16 EStG und § 1 Nr. 1 KSVEntgV.
- Bewirtung: unselbstständig. § 1 Nr. 2 KSVEntgV, übliche Bewirtung des Künstlers oder Publizisten.
- Gemischte Zeile: nur ein belegter Ausnahmeanteil kann ausscheiden. Der Arbeitsanteil bleibt. Ohne Aufteilung gilt der Gesamtbetrag. Material allein ist keine Ausnahme.
- Drittleistung: eigenständig. Ein Beleg wirkt nur auf diese Position. Weiterberechnete Reisekosten Dritter sind keine Ausnahme nach § 1 Nr. 1 KSVEntgV.

Ein Nachweis beweist einen realen Vorgang. Er erschafft ihn nicht. Der Hinweis ändert die Einordnung nie. Nur ein voll validierter neuer Lauf könnte das, und der ist in Phase 1 nicht gebaut.

## Nicht verwenden

Die häufig genannte Fundstelle „Werklieferung § 23 Abs. 1 Satz 2 KSVG“ steht so nicht in Q-KSVG@2026-10-05. § 23 KSVG ist dort ein Absatz ohne Satz 2 zur Werklieferung. Diese Fundstelle darf nicht zitiert werden. Ohne belastbare Norm bleibt ein Werklieferungs-Ausschluss UNGEKLÄRT und wird nicht als Abzug vorgeschlagen.

## Kategorien im Bericht

Wort, Bildende Kunst, Musik, Darstellende Kunst. Nicht erkennbare Kategorie bleibt UNGEKLÄRT und wird nicht in einen Topf geschoben. Seit 2000 gibt es einen einheitlichen Abgabesatz; die Kategorien strukturieren den Bericht, sie ändern den Satz nicht.

## Meldefrist

§ 27 Abs. 1 KSVG: Meldung der Jahressumme bis zum 31. März des Folgejahres.

## Tore

Dreistimmigkeit der Zahlen, Form-Konsens, Mathematik, Dreistimmigkeit der Inhalte, Validator V01–V06. Kein Bericht, wenn ein Tor scheitert. Ein Summenwiderspruch ist ein Scheitern (Rücktest Summenfehler). Ein 5,0-Prozent-Fall auf 10.000,00 Euro netto im Jahr 2025 bei typischem Verwerter und natürlicher Person ergibt 500,00 Euro Abgabe (Rücktest).

## Sprachmodell

Ablesen: drei konfigurierte Modelle, bis zu drei Versuche. Bewerten und Prüfen dürfen nur bestätigte Werte der Vorstufe sehen. Der Chat zitiert Bericht und aktive Library. Er bewertet nicht neu, rechnet nicht selbst und löst keine Hinweise auf.
