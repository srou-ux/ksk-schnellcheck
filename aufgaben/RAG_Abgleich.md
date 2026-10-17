# RAG – Abgleich Register ↔ Quelle

Erzeugt von `python -m app.rag.abgleich`. Geprüft wird nur, ob der eingetragene Wert im Text der genannten Fundstelle vorkommt; kein Wert wird aus Texten übernommen. Die Ergebnisse sind Hinweise für die menschliche Prüfung, keine Freigabe.

| Ergebnis | Anzahl |
|---|---|
| ABWEICHUNG | 1 |
| Fundstelle fehlt | 2 |
| nur im Dokument | 3 |
| bestätigt | 49 |
| nicht prüfbar | 20 |

| Ergebnis | Blatt | Schlüssel | Jahr | Wert | Fundstelle |
|---|---|---|---|---|---|
| ABWEICHUNG | Regelregister | musikverein.schueler_grenze (Schüler) | 2015 | 60 | KSK-Info 12, Abschn. 2 (Stand 08.2025) |
| Fundstelle fehlt | Regelregister | verpflegung.pauschale_klein (EUR) | 2014 | 12 | KSK-Info 10, Abschn. 3; EStG-Text für das Jahr nicht einzeln geprüft |
| Fundstelle fehlt | Regelregister | verpflegung.pauschale_gross (EUR) | 2014 | 24 | KSK-Info 10, Abschn. 3 |
| nur im Dokument | Regelregister | aufbewahrung.jahre (Jahre) | 2015 | 5 | KSVG § 28 S. 3; KSK-Info 17 Abschn. 3 |
| nur im Dokument | Regelregister | veranstaltungen.ausnahme_max (Veranstaltungen) | 2023 | 3 | KSVG § 24 Abs. 2 S. 3 Nr. 1 |
| nur im Dokument | Schwellen nach Jahr | Schwelle | 2022 | 450 € nur als Geringfügigkeitsgrenze, zusätzlich Regelmäßigk | KSVG § 24 Abs. 1 Satz 2, Abs. 3 a. F.; Ende der Fassung A: Art. 34 Abs. 1 des 8. SGB IV-ÄndG (01.01.2023) |
| bestätigt | Abgabesätze | Abgabesatz | 2015 | 5.2 | KSK-Info 01, Abschn. 4, S. 8 (Stand 01.2026) |
| bestätigt | Abgabesätze | Abgabesatz | 2016 | 5.2 | KSK-Info 01, Abschn. 4, S. 8 |
| bestätigt | Abgabesätze | Abgabesatz | 2017 | 4.8 | KSK-Info 01, Abschn. 4, S. 8 |
| bestätigt | Abgabesätze | Abgabesatz | 2018 | 4.2 | KSK-Info 01, Abschn. 4, S. 8 |
| bestätigt | Abgabesätze | Abgabesatz | 2019 | 4.2 | Künstlersozialabgabe-Verordnung 2019, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2020 | 4.2 | Künstlersozialabgabe-Verordnung 2020, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2021 | 4.2 | Künstlersozialabgabe-Verordnung 2021, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2022 | 4.2 | Künstlersozialabgabe-Verordnung 2022, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2023 | 5 | Künstlersozialabgabe-Verordnung 2023, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2024 | 5 | Künstlersozialabgabe-Verordnung 2024, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2025 | 5 | Künstlersozialabgabe-Verordnung 2025, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2026 | 4.9 | Künstlersozialabgabe-Verordnung 2026, § 1 |
| bestätigt | Abgabesätze | Abgabesatz | 2027 | 5 | Verordnung zur Künstlersozialabgabe 2027, Art. 1 § 1 (BGBl. 2026 I Nr. 262) |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2013 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2014 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2015 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2016 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2017 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2018 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2019 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2020 | 2400 | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2021 | 3000 | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2022 | 3000 | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2023 | 3000 | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2024 | 3000 | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2025 | 3000 | KSK-Info 24, 24a (Stand 01.2026); Info 01 Abschn. 3 |
| bestätigt | Pauschalen nach Jahr | Ehrenamtspauschale | 2025 | 840 | KSK-Info 24, 24a (Stand 01.2026); Info 01 Abschn. 3 |
| bestätigt | Pauschalen nach Jahr | Übungsleiterpauschale | 2026 | 3300 | KSK-Info 24, 24a (Stand 01.2026); Info 01 Abschn. 3 |
| bestätigt | Pauschalen nach Jahr | Ehrenamtspauschale | 2026 | 960 | KSK-Info 24, 24a (Stand 01.2026); Info 01 Abschn. 3 |
| bestätigt | Regelregister | verpflegung.stunden_grenze (Stunden) | 2014 | 8 | EStG § 9 Abs. 4a S. 3 Nr. 3; KSK-Info 10 Abschn. 3 (Info schreibt „8 bis 24“, Abweichung beachten) |
| bestätigt | Regelregister | verpflegung.stunden_ganztag (Stunden) | 2014 | 24 | EStG § 9 Abs. 4a S. 3 Nr. 1 |
| bestätigt | Regelregister | vorauszahlung.untergrenze (EUR) | 2015 | 40 | KSVG § 27 Abs. 3 S. 3 |
| bestätigt | Regelregister | vorauszahlung.monate (Monate) | 2015 | 12 | KSVG § 27 Abs. 3; KSK-Info 01 Abschn. 4 |
| bestätigt | Regelregister | saeumnis.stufe (EUR) | 2015 | 50 | SGB IV § 24 Abs. 1 S. 1; KSVG § 30 Abs. 1 |
| bestätigt | Regelregister | saeumnis.satz_prozent (Prozent je Monat) | 2015 | 1 | SGB IV § 24 Abs. 1 S. 1; KSVG § 30 Abs. 1 |
| bestätigt | Regelregister | saeumnis.bagatell_gesondert (EUR) | 2015 | 150 | SGB IV § 24 Abs. 1 S. 3 |
| bestätigt | Regelregister | meldefrist.monat (Monat) | 2015 | 3 | KSVG § 27 Abs. 1 |
| bestätigt | Regelregister | meldefrist.tag (Tag) | 2015 | 31 | KSVG § 27 Abs. 1 |
| bestätigt | Regelregister | verpflegung.pauschale_klein (EUR) | 2020 | 14 | EStG § 9 Abs. 4a S. 3 Nr. 2, 3 (Momentaufnahme); KSK-Info 10 |
| bestätigt | Regelregister | verpflegung.pauschale_gross (EUR) | 2020 | 28 | EStG § 9 Abs. 4a S. 3 Nr. 1 (Momentaufnahme); KSK-Info 10 |
| bestätigt | Regelregister | schaetzung.ausland_prozent (Prozent der Bruttoeinnahmen) | 2025 | 25 | KSK-Info 04 (Stand 08.2025), Abschn. 4b; Checkliste Veranstalter S. 2 (Auslegung der KSK, kein Gesetz) |
| bestätigt | Schwellen nach Jahr | Schwelle | 2019 | 450 € nur als Geringfügigkeitsgrenze, zusätzlich Regelmäßigk | KSVG § 24 Abs. 3 a. F.; BSG B 3 KS 3/21 R Rn. 18 |
| bestätigt | Schwellen nach Jahr | Schwelle | 2020 | 450 € nur als Geringfügigkeitsgrenze, zusätzlich Regelmäßigk | KSVG § 24 Abs. 3 a. F.; BSG B 3 KS 3/21 R Rn. 18 |
| bestätigt | Schwellen nach Jahr | Schwelle | 2021 | 450 € nur als Geringfügigkeitsgrenze, zusätzlich Regelmäßigk | KSVG § 24 Abs. 3 a. F.; BSG B 3 KS 3/21 R Rn. 18 |
| bestätigt | Schwellen nach Jahr | Schwelle | 2023 | 450 € | KSVG § 24 Abs. 2 Satz 2 (Kopien 2023-05-13, 2024-05-21) |
| bestätigt | Schwellen nach Jahr | Schwelle | 2024 | 450 € | KSVG § 24 Abs. 2 Satz 2 (Kopien 2023-05-13, 2024-05-21) |
| bestätigt | Schwellen nach Jahr | Schwelle | 2025 | 700 € | KSVG § 54: 'Abweichend von § 24 Absatz 2 Satz 2 beträgt die Entgeltsumme 700 Euro im Kalenderjahr 2025' |
| bestätigt | Schwellen nach Jahr | Schwelle | 2026 | 1.000 € | KSVG § 24 Abs. 2 Satz 2 (aktuell) |
| bestätigt | Schwellen nach Jahr | Schwelle | 2027 | 1.000 € (nach aktuellem Text) | KSVG § 24 Abs. 2 Satz 2 (aktuell) |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2013 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2014 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2015 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2016 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2017 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2018 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2019 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2020 | – | KSK-Info 01 (Archiv 2022-01-20), Abschn. 3; Info 10/12 (Archiv): „seit 2013 max. 2.400 €“ |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2021 | laut KSK-Info nicht relevant | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2022 | laut KSK-Info nicht relevant | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2023 | laut KSK-Info nicht relevant | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| nicht prüfbar | Pauschalen nach Jahr | Ehrenamtspauschale | 2024 | laut KSK-Info nicht relevant | KSK-Info 01 (Archiv), „ab 2021 max. 3.000 €“; KSK-Info 24a, S. 3 |
| nicht prüfbar | Regelregister | schwelle.operator (Vergleich) | 2015 | > | KSVG § 24 Abs. 2 S. 2 („übersteigt“) |
| nicht prüfbar | Regelregister | rechtsform.kein_entgelt (Rechtsform) | 2015 | gmbh | KSK-FAQ Unternehmen und Verwerter, Frage 12 |
| nicht prüfbar | Regelregister | rechtsform.kein_entgelt (Rechtsform) | 2015 | kg | BSG 12.08.2010, B 3 KS 2/09 R; BSG 02.04.2014, B 3 KS 3/12 R |
| nicht prüfbar | Regelregister | rechtsform.kein_entgelt (Rechtsform) | 2015 | ohg | BSG 16.07.2014, B 3 KS 3/13 R |
| nicht prüfbar | Regelregister | rechtsform.kein_entgelt (Rechtsform) | 2015 | ug | Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH |
| nicht prüfbar | Regelregister | rechtsform.kein_entgelt (Rechtsform) | 2015 | ag | Ableitung; KSK-FAQ Frage 12 nennt nur die GmbH |
| nicht prüfbar | Regelregister | saeumnis.addition_vor_abrundung (Ja/Nein) | 2015 | ja | BSG 07.07.2020, B 12 R 28/18 R; SGB IV § 24 Abs. 1 (Fassung bis 2022) |
| nicht prüfbar | Regelregister | saeumnis.addition_vor_abrundung (Ja/Nein) | 2023 | nein | SGB IV § 24 Abs. 1 (Fassung ab 2023) |
