# Statusmodell für Regeln, Testfälle und Pakete (Entwurf)

Aus dem externen Prüfbericht (Statusbegriffe) übernommen. Grundsatz: **Technischer Zustand und fachlicher Zustand sind getrennt.** Ein bestandener technischer Test ersetzt nie die fachliche Freigabe. Kein Paket wird allein wegen erfolgreicher Uploads aktiv.

## Zustände
| Zustand | Bedeutung | Wer setzt ihn |
|---|---|---|
| Entwurf | Regel oder Test mit Fundstelle angelegt, noch nicht geprüft | Ersteller (Claude/Mensch) |
| technisch geprüft | Formale Prüfung bestanden (`tests/pruefe_regelwerk.py`, `tests/pruefe_quellen.py`), Fundstelle und Quelldatei vorhanden, unabhängiger Audit ohne offenen Befund | Automatik + Prüfer |
| fachlich zu klären | Inhalt hängt an einer offenen Sachfrage (z. B. Datum unbestätigt, Widerspruch zwischen Quellen, Ableitung ohne Urteil) | Prüfer |
| fachlich freigegeben | Steuerberater oder Fachanwalt hat die Regel inhaltlich bestätigt | Fachperson (Name, Datum) |
| aktiv | Technisch geprüft **und** fachlich freigegeben, in einem Paket mit Version | Admin |
| gesperrt | Widerspruch, Quellenverlust oder Fehler entdeckt; darf nicht verwendet werden | Admin / Prüfer |

## Regeln für Übergänge
1. Neue oder geänderte Regeln beginnen immer bei „Entwurf“; Änderungen an freigegebenen oder aktiven Regeln erzeugen eine **neue Version** (alte bleibt reproduzierbar).
2. „aktiv“ nur, wenn technisch geprüft **und** fachlich freigegeben. Ohne belegte Quelle kein Übergang über „Entwurf“.
3. Offene Sachfragen werden als „fachlich zu klären“ geführt und im Blatt „Offene Punkte“ beschrieben.
4. Beim Quellenverlust oder Widerspruch zu einer neueren Quelle: „gesperrt“, bis geklärt.
5. Laufende und abgeschlossene Fälle behalten ihre Paket- und Regelversion.

## Stand im Repo (09.10.2026)
- Spalte „Prüfstatus“ im Regelkatalog und in den Testfällen: „Entwurf – vom Steuerberater zu prüfen“.
- Abweichend „Entwurf – fachlich zu klären“: R-10 bis R-15, R-24 und R-150 (Inkrafttretensdatum der Fassung B am Original unbestätigt, Befund B4).
- Noch nicht gesetzt: „technisch geprüft“ (es gibt Audits, aber keine Markierung je Regel), „fachlich freigegeben“, „aktiv“, „gesperrt“.
- Anzeige im Bot: Immer „Entwurf – vom Steuerberater zu prüfen“, bis eine Regel fachlich freigegeben ist.
