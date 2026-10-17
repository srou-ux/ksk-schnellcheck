"""Einordnung des Auftraggebers aus Fakten mit Herkunft (16.10.2026, Umbau Schritt 1).

Auftrag des Nutzers: Die KI erkennt die Angaben aus dem Text, ein fester Regelkern prüft sie, der Nutzer bestätigt
die FAKTEN – er soll die rechtliche Kategorie nicht selbst wählen müssen. Bedingungen (Nutzer, 16.10.2026):
1. keine reine Branchenzuordnung ('Verlag', 'Agentur' sind Hinweise, die der Nutzer bestätigt);
2. keine starre Entweder-oder-Kette: Tätigkeit des Auftraggebers und Zweck des Auftrags werden getrennt erfasst,
   mehrere Tatbestände können nebeneinander bestehen (`tatbestaende`);
3. Herkunft jeder Angabe schon jetzt: Text (mit Zitat), Knopf, Sprachmodell oder System;
4. `Fakten.verwerterart` (die alte Kategorie) wird NUR noch hier abgeleitet – keine zweite Wahrheit;
5. ein Knopf darf eine ausdrückliche Angabe im Text nicht still überschreiben: dann gezielte Widerspruchsfrage.

Die getrennten Fakten:
- `unternehmensart`: was der Auftraggeber macht (frei, z. B. 'Bäckerei', 'Buchverlag'), vom Modell gelesen;
- `katalog_taetigkeit`: betreibt der Auftraggeber eine Tätigkeit aus dem Katalog der typischen Verwerter?
  (True/False/None) – aus dem Text, per Knopf oder vom Modell;
- `auftragszweck`: wofür ist DIESER Auftrag? eigene Werbung, für Kunden/Dritte, Veranstaltung, privat.
Welche Wörter worauf hinweisen, steht in app/verwerterart_begriffe.json und app/privat_begriffe.json (keine Wortlisten
hier). Die rechtliche Prüfung selbst (Schwelle, Veranstaltungen, Einnahmeabsicht) macht wie bisher kern/rechnen.py."""
from __future__ import annotations

import re
from typing import Any, Optional

from app.schema import VERWERTERART_LESBAR, Fakten, Herkunft, Widerspruch

ZWECK_LESBAR: dict[str, str] = {
    "eigene_werbung": "Werbung oder Öffentlichkeitsarbeit für das eigene Unternehmen",
    # Schritt 2 (17.10.2026): 'für Kunden' heißt hier nur Werbung/Öffentlichkeitsarbeit für Dritte (Katalog des
    # KSVG § 24 Abs. 1 Satz 1 Nr. 7), nicht jede beliebige Leistung für Kunden.
    "fuer_kunden": "Werbung oder Öffentlichkeitsarbeit für Kunden (Dritte)",
    "veranstaltung": "Veranstaltung(en) mit Künstlern",
    "privat": "privater Auftrag (kein Unternehmen)",
}
# Schritt 2 (17.10.2026, Auftrag „Rückfragen nach Tatsachen“): Knöpfe der Rückfrage FRAGE_ZWECK in Alltagssprache.
# Der Nutzer wählt eine TATSACHE (wofür war der Auftrag?), nie eine rechtliche Kategorie; die Einordnung macht
# leite_ab. Die Liste ist nicht vollständig: passt nichts, schreibt der Nutzer frei oder wählt „Noch unbekannt“.
ZWECK_KNOPF: dict[str, str] = {
    "Werbung für mein eigenes Unternehmen": "eigene_werbung",
    "Werbung oder Öffentlichkeitsarbeit für Kunden": "fuer_kunden",
    "Eine Veranstaltung mit Künstlern": "veranstaltung",
    "Ein privater Auftrag": "privat",
}
HERKUNFT_LESBAR = {
    "text": "laut Ihrer Nachricht",
    "knopf": "von Ihnen ausgewählt",
    "modell": "vom Sprachmodell gelesen – bitte prüfen",
    "system": "vom System aus Ihren Angaben abgeleitet – bitte prüfen",
}
# Alte Kategorie -> getrennte Fakten (nur zum Übernehmen einer alten Angabe, nie umgekehrt gespeichert).
_AUS_KATEGORIE: dict[str, dict[str, Any]] = {
    "eigenwerber": {"auftragszweck": "eigene_werbung"},
    "typischer_verwerter": {"katalog_taetigkeit": True},
    "generalklausel": {"auftragszweck": "veranstaltung"},
    "privat": {"auftragszweck": "privat"},
}
EINORDNUNG_FELDER = ("auftragszweck", "katalog_taetigkeit")
# Nur für Testläufer und gespeicherte Testfälle aus der Zeit vor Schritt 2 (Knopf mit der alten Kategorie): welcher
# Zweck-Knopf zur selben Einordnung führt (leite_ab). Die Testfälle selbst bleiben unverändert (nur ergänzen).
KATEGORIE_ZU_ZWECK: dict[str, str] = {"eigenwerber": "eigene_werbung", "typischer_verwerter": "fuer_kunden",
                                      "generalklausel": "veranstaltung", "privat": "privat"}


def zweck_knopf_fuer_alten_knopf(kategorie_oder_text: str) -> Optional[str]:
    """'Eigenwerbung' oder 'eigenwerber' -> 'Werbung für mein eigenes Unternehmen' (Beschriftung des Zweck-Knopfs)."""
    kategorie = next((k for k, t in VERWERTERART_LESBAR.items() if kategorie_oder_text in (k, t)), None)
    zweck = KATEGORIE_ZU_ZWECK.get(kategorie or "")
    return next((b for b, z in ZWECK_KNOPF.items() if z == zweck), None)


def _anzahl_veranstaltungen_muster() -> Optional[re.Pattern]:
    """'vier Konzerte', '2 Lesungen', 'eine Veranstaltung' (app/verwerterart_begriffe.json, '_zweck_veranstaltung')."""
    import json
    from pathlib import Path

    wurzel = Path(__file__).resolve().parent
    regel = json.loads((wurzel / "verwerterart_begriffe.json").read_text(encoding="utf-8")).get("_zweck_veranstaltung")
    if not regel:
        return None
    zahlen = json.loads((wurzel / "anzahl_begriffe.json").read_text(encoding="utf-8"))["zahlwoerter"] + regel["zahlwoerter"]
    return re.compile(r"(?<![0-9a-z])(?:\d+|" + "|".join(re.escape(z) for z in zahlen) + r")\s+(?:"
                      + "|".join(re.escape(b) for b in regel["begriffe"]) + r")(?![a-z])")


_ANZAHL_VERANSTALTUNGEN = _anzahl_veranstaltungen_muster()


def nennt_anzahl_veranstaltungen(text: str) -> bool:
    from app import zuordnung

    return bool(_ANZAHL_VERANSTALTUNGEN and _ANZAHL_VERANSTALTUNGEN.search(zuordnung._vereinheitliche(text)))


def _treffer(text: str, begriffe: list[str]) -> Optional[str]:
    """Der erste Begriff, der als Wort im Text steht, im Wortlaut des Textes (für das Zitat)."""
    for b in begriffe:
        m = re.search(r"(?<![0-9a-zäöüß])" + re.escape(b.lower()) + r"(?![a-zäöüß])", text.lower())
        if m:
            return text[m.start():m.end()]
    return None


def belege_im_text(text: str) -> dict[str, tuple[Any, str]]:
    """Ausdrückliche Angaben im Nutzertext: Feld -> (Wert, Zitat). Gleiche Begriffslisten wie die Prüfungen in
    app/zuordnung.py (absichere_verwerterart): Namen in Anführungszeichen zählen nicht ('Galerie Hoffmann')."""
    from app import zuordnung

    sauber = zuordnung._ohne_namen(text)
    erg: dict[str, tuple[Any, str]] = {}
    katalog = _treffer(sauber, zuordnung.VERWERTERART_BEGRIFFE.get("typischer_verwerter", []))
    if katalog:
        erg["katalog_taetigkeit"] = (True, katalog)
    eigen = _treffer(sauber, zuordnung.VERWERTERART_BEGRIFFE.get("eigenwerber", [])) or zuordnung.eigenwerbung_muster(sauber)
    if eigen:
        erg["auftragszweck"] = ("eigene_werbung", eigen)
    elif zuordnung.privater_auftraggeber(text):
        satz = next((s for s in re.split(r"(?<=[.!?])\s+|\n", text) if zuordnung.privater_auftraggeber(s)), "")
        erg["auftragszweck"] = ("privat", satz.strip()[:120])
    else:
        gk = _treffer(sauber, zuordnung.VERWERTERART_BEGRIFFE.get("generalklausel", []))
        if gk:
            erg["auftragszweck"] = ("veranstaltung", gk)
    return erg


def leite_ab(fakten: Fakten) -> Fakten:
    """Die alte Kategorie `verwerterart` aus den getrennten Fakten (Bedingung 4: nur hier gesetzt).
    - Katalog-Tätigkeit des Auftraggebers -> typischer Verwerter, auch bei eigener Werbung (ein Verlag, der für sich
      selbst wirbt, bleibt typischer Verwerter);
    - Auftrag für Kunden (Werbung/Öffentlichkeitsarbeit für Dritte) -> typischer Verwerter (Katalog: Werbung für
      Dritte); ist die Katalog-Tätigkeit ausdrücklich verneint, bleibt es offen (Widerspruch, siehe pruefe);
    - privater Auftrag -> privat (nur ohne Katalog-Tätigkeit);
    - eigene Werbung -> Eigenwerbung; Veranstaltung -> Generalklausel;
    - sonst offen (None): app/pflichtangaben.py fragt nach dem ZWECK."""
    zweck, katalog = fakten.auftragszweck, fakten.katalog_taetigkeit
    if katalog is True:
        wert = "typischer_verwerter"
    elif zweck == "fuer_kunden" and katalog is not False:
        wert = "typischer_verwerter"
    elif zweck == "privat":
        wert = "privat"
    elif zweck == "eigene_werbung":
        wert = "eigenwerber"
    elif zweck == "veranstaltung":
        wert = "generalklausel"
    else:
        wert = None
    if fakten.widersprueche and any(w.feld in (*EINORDNUNG_FELDER, "verwerterart") for w in fakten.widersprueche):
        wert = None  # offener Widerspruch: keine Einordnung, bis er geklärt ist
    return fakten if fakten.verwerterart == wert else fakten.model_copy(update={"verwerterart": wert})


def tatbestaende(fakten: Fakten) -> list[str]:
    """Alle Tatbestände, auf die die Fakten hinweisen (Bedingung 2: nebeneinander, nicht entweder-oder) – für die
    Anzeige in der Bestätigung. Maßgeblich für die Rechnung ist `leite_ab`; die anderen werden genannt."""
    erg = []
    if fakten.katalog_taetigkeit:
        erg.append("typischer_verwerter")
    if fakten.auftragszweck == "fuer_kunden" and "typischer_verwerter" not in erg:
        erg.append("typischer_verwerter")
    if fakten.auftragszweck == "eigene_werbung":
        erg.append("eigenwerber")
    if fakten.auftragszweck == "veranstaltung" or fakten.veranstaltungszahl:
        erg.append("generalklausel")
    if fakten.auftragszweck == "privat":
        erg.append("privat")
    return erg


def _mit_herkunft(fakten: Fakten, feld: str, wert: Any, herkunft: Herkunft) -> Fakten:
    return fakten.model_copy(update={feld: wert, "herkunft": {**fakten.herkunft, feld: herkunft}})


def erfasse(text: str, fakten: Fakten, bisher: Optional[Fakten] = None, modell_kategorie: Optional[str] = "?") -> Fakten:
    """Nach dem Lesen einer Nachricht (app/router.py, nach allen Prüfungen): die getrennten Fakten mit Herkunft setzen
    und die Kategorie ableiten.
    Reihenfolge der Belege: (1) ausdrückliche Angabe im Text (mit Zitat) – nie durch eine Lesart des Modells
    überschrieben; (2) eine schon gespeicherte Angabe (Knopf, früherer Text) bleibt, solange die neue Nachricht
    nichts dazu sagt; (3) die Lesart des Modells (`auftragszweck` oder die alte Kategorie `verwerterart`, wie sie die
    Prüfungen in app/zuordnung.py stehen gelassen haben) – sichtbar als 'bitte prüfen'. Hat eine Prüfung in
    app/zuordnung.py die Kategorie gesetzt (anders als das Modell, `modell_kategorie`), ist die Herkunft 'system'."""
    alt_herkunft = dict(bisher.herkunft) if bisher is not None else {}
    fakten = fakten.model_copy(update={"herkunft": {**alt_herkunft, **fakten.herkunft}})
    belege = belege_im_text(text)
    # Lesart des Modells / der bisherigen Prüfungen aus der alten Kategorie (nur, wo die neuen Felder leer sind).
    lesart = dict(_AUS_KATEGORIE.get(fakten.verwerterart or "", {}))
    for feld in EINORDNUNG_FELDER:
        if feld in belege:
            wert, zitat = belege[feld]
            alt = fakten.herkunft.get(feld)
            # Ein früher per Knopf geklärter Widerspruch bleibt geklärt (der Text der ersten Nachricht steht weiter im
            # Verlauf); eine NEUE ausdrückliche Angabe gilt.
            if alt is not None and alt.art == "knopf" and getattr(bisher, feld, None) is not None and alt.beleg == "geklärt":
                continue
            # Schritt 2: eine Auswahl per Knopf und eine ANDERE ausdrückliche Angabe im Text -- nicht still
            # überschreiben, sondern gezielt fragen (dieselbe Widerspruchsfrage wie beim Knopf).
            knopf_wert = getattr(bisher, feld, None) if bisher is not None else None
            if (feld == "auftragszweck" and alt is not None and alt.art == "knopf" and knopf_wert is not None
                    and knopf_wert != wert):
                if not any(w.feld == feld for w in fakten.widersprueche):
                    fakten = fakten.model_copy(update={"auftragszweck": knopf_wert, "widersprueche": [
                        *fakten.widersprueche, _zweck_widerspruch(zitat, wert, knopf_wert, "geschrieben_danach")]})
                continue
            fakten = _mit_herkunft(fakten, feld, wert, Herkunft(art="text", beleg=zitat))
            # Schritt 2: eine spätere ausdrückliche Angabe beendet 'noch unbekannt' (auch unter dem alten Namen).
            if feld == "auftragszweck" and any(k in fakten.unbekannt for k in (feld, "verwerterart")):
                fakten = fakten.model_copy(update={"unbekannt": [k for k in fakten.unbekannt
                                                                 if k not in (feld, "verwerterart")]})
        elif (bisher is not None and alt_herkunft.get(feld) is not None and alt_herkunft[feld].art == "knopf"
              and getattr(bisher, feld) is not None and getattr(fakten, feld) != getattr(bisher, feld)):
            # Schritt 2 (17.10.2026): eine Auswahl des Nutzers ändert das Modell nicht -- ohne neue ausdrückliche
            # Angabe im Text bleibt der gewählte Wert (Herkunft 'knopf').
            fakten = _mit_herkunft(fakten, feld, getattr(bisher, feld), alt_herkunft[feld])
        elif getattr(fakten, feld) is not None:
            if feld not in fakten.herkunft:
                fakten = _mit_herkunft(fakten, feld, getattr(fakten, feld), Herkunft(art="modell"))
        elif feld in lesart and fakten.verwerterart is not None:
            art = "system" if modell_kategorie != "?" and modell_kategorie != fakten.verwerterart else "modell"
            # Testarchiv mit mistral-small-latest (17.10.2026: AT-2026-010 Sportverein, AT-2026-033 Fotostudio, P-16
            # Hobbyorchester-Verein): das Modell RIET 'typischer Verwerter' ohne jeden Begriff dafür im Text; daraus wurde
            # die Katalog-Tätigkeit -> abgabepflichtig ohne Schwelle (FALSCH). Bedingung 4 (Umbau Schritt 1): keine Fakten
            # aus der bloßen Kategorie des Modells erfinden. Die Katalog-Tätigkeit braucht einen Beleg im Text, eine
            # frühere Angabe oder einen Knopf, wenn das Modell SELBST einen anderen Zweck gelesen hat (eigene Werbung,
            # Veranstaltung, privat) – dann widerspricht sich die Lesart des Modells, und der konkrete Zweck gilt.
            # Ohne gelesenen Zweck bleibt es bei der früheren Regel M4 (die Kategorie des Modells gilt, sichtbar als
            # 'bitte prüfen').
            if (feld == "katalog_taetigkeit" and lesart[feld] is True and art == "modell"
                    and fakten.auftragszweck in ("eigene_werbung", "veranstaltung", "privat")):
                continue
            fakten = _mit_herkunft(fakten, feld, lesart[feld], Herkunft(art=art))
    # Entscheidung des Nutzers (17.10.2026, „Geratenen Zweck immer nachfragen“): steht der Zweck nicht im Text, darf das
    # Modell ihn nicht annehmen. Ein Zweck, den NUR das Modell gelesen hat (Herkunft 'modell': kein Wort dafür im Text,
    # keine Auswahl, keine feste Prüfung), gilt nicht; app/pflichtangaben.py fragt dann „Wofür war dieser Auftrag
    # gedacht?“, und der Nutzer bestätigt per Knopf. Anlass: Testarchiv mit Small (AT-2026-004 '30-Jahr-Feier …
    # Firmenveranstaltung' -> Veranstaltung geraten, A-999, AT-2026-007, P-12). Kostet einen Klick, nie ein Ergebnis.
    hz = fakten.herkunft.get("auftragszweck")
    if (fakten.auftragszweck is not None and hz is not None and hz.art == "modell"
            and not (fakten.auftragszweck == "veranstaltung" and nennt_anzahl_veranstaltungen(text))):
        fakten = fakten.model_copy(update={
            "auftragszweck": None, "herkunft": {k: v for k, v in fakten.herkunft.items() if k != "auftragszweck"}})
    # Zweck 'eigene Werbung' aus dem Text und eine Katalog-Tätigkeit nur vom Modell: die Tätigkeit ist nicht belegt.
    h = fakten.herkunft.get("katalog_taetigkeit")
    if fakten.katalog_taetigkeit and h is not None and h.art == "modell" and "auftragszweck" in belege:
        fakten = fakten.model_copy(update={"katalog_taetigkeit": None,
                                           "herkunft": {k: v for k, v in fakten.herkunft.items() if k != "katalog_taetigkeit"}})
    return leite_ab(fakten)


def knopf(fakten: Fakten, kategorie: str) -> Fakten:
    """Knopf 'Art des Auftraggebers' (alte Kategorie) oder ein Knopf zur Klärung eines Widerspruchs. Bedingung 5:
    widerspricht die Auswahl einer AUSDRÜCKLICHEN Angabe im Text, wird nichts überschrieben, sondern gezielt gefragt
    (Widerspruch mit zwei Knöpfen). Ein Knopf, der einen offenen Widerspruch beantwortet, entscheidet."""
    offen = [w for w in fakten.widersprueche if w.feld == "verwerterart"]
    neu = dict(_AUS_KATEGORIE.get(kategorie, {}))
    if not neu:
        raise ValueError(f"unbekannte Art des Auftraggebers {kategorie!r}")
    if not offen:
        for feld, wert in neu.items():
            h = fakten.herkunft.get(feld)
            alt = getattr(fakten, feld)
            text_wert_anders = h is not None and h.art == "text" and alt is not None and alt != wert
            # Eigene Werbung im Text, gewählt 'typischer Verwerter': ebenfalls ein Widerspruch zum Zweck.
            zweck_text = fakten.herkunft.get("auftragszweck")
            eigen_vs_katalog = (feld == "katalog_taetigkeit" and zweck_text is not None and zweck_text.art == "text"
                                and fakten.auftragszweck in ("eigene_werbung", "privat", "veranstaltung"))
            # Katalog-Tätigkeit im Text ('Wir sind ein Verlag'), gewählt eine andere Art: ebenfalls ein Widerspruch.
            kat_text = fakten.herkunft.get("katalog_taetigkeit")
            katalog_vs_anders = (kategorie != "typischer_verwerter" and fakten.katalog_taetigkeit is True
                                 and kat_text is not None and kat_text.art == "text")
            if text_wert_anders or eigen_vs_katalog or katalog_vs_anders:
                h = h if text_wert_anders else (kat_text if katalog_vs_anders else zweck_text)
                bisher_kat = leite_ab(fakten).verwerterart or kategorie
                if bisher_kat == kategorie:
                    break
                zitat = h.beleg
                hinweis = (f"Sie hatten geschrieben: „{zitat}“ ({VERWERTERART_LESBAR.get(bisher_kat, bisher_kat)}). "
                           f"Jetzt haben Sie „{VERWERTERART_LESBAR.get(kategorie, kategorie)}“ gewählt. Welche Angabe stimmt?")
                return fakten.model_copy(update={
                    "verwerterart": None,
                    "widersprueche": [*fakten.widersprueche,
                                      Widerspruch(feld="verwerterart", werte=[bisher_kat, kategorie], hinweis=hinweis)]})
    # Übernehmen: die gewählte Kategorie setzt die getrennten Fakten (der andere Teil wird geleert, damit keine alte
    # Angabe die Wahl wieder umstößt).
    daten: dict[str, Any] = {"auftragszweck": None, "katalog_taetigkeit": None, **neu}
    if kategorie == "eigenwerber":
        daten["katalog_taetigkeit"] = False
    herkunft = {k: v for k, v in fakten.herkunft.items() if k not in EINORDNUNG_FELDER}
    for feld in neu:
        herkunft[feld] = Herkunft(art="knopf", beleg="geklärt" if offen else None)
    if kategorie == "eigenwerber":
        herkunft["katalog_taetigkeit"] = Herkunft(art="knopf", beleg="geklärt" if offen else None)
    fakten = fakten.model_copy(update={**daten, "herkunft": herkunft,
                                       "widersprueche": [w for w in fakten.widersprueche if w.feld != "verwerterart"]})
    return leite_ab(fakten)


def _zweck_widerspruch(zitat: Optional[str], text_wert: str, knopf_wert: str, reihenfolge: str) -> Widerspruch:
    """Gezielte Frage, wenn Text und Auswahl beim Zweck verschieden sind (Bedingung 5). Knöpfe: beide Werte."""
    t, k = ZWECK_LESBAR.get(text_wert, text_wert), ZWECK_LESBAR.get(knopf_wert, knopf_wert)
    zitat_text = f"„{zitat}“ ({t})" if zitat else f"„{t}“"
    if reihenfolge == "geschrieben_danach":
        hinweis = f"Sie hatten „{k}“ gewählt und danach geschrieben: {zitat_text}. Welche Angabe stimmt?"
    else:
        hinweis = f"Sie hatten geschrieben: {zitat_text}. Jetzt haben Sie „{k}“ gewählt. Welche Angabe stimmt?"
    return Widerspruch(feld="auftragszweck", werte=[text_wert, knopf_wert], hinweis=hinweis)


def zweck_knopf(fakten: Fakten, zweck: str) -> Fakten:
    """Schritt 2 (17.10.2026): Antwort auf FRAGE_ZWECK per Knopf (oder exakt abgetipptem Knopftext).
    - Setzt NUR den Zweck dieses Auftrags (Herkunft 'knopf'); die Tätigkeit des Auftraggebers bleibt
      (`unternehmensart`, eine im Text belegte Katalog-Tätigkeit: ein Verlag mit eigener Werbung bleibt Verlag).
    - Eine Katalog-Tätigkeit, die nur das Modell oder das System vermutet hat, gilt nach der Auswahl eines anderen
      Zwecks nicht mehr (wie in erfasse: keine Fakten aus einer bloßen Vermutung).
    - Widerspricht die Auswahl einer ausdrücklichen Angabe im Text, wird nichts überschrieben: gezielte Frage.
    - Ein Knopf, der einen offenen Widerspruch zum Zweck beantwortet, entscheidet.
    Die rechtliche Einordnung macht wie immer leite_ab."""
    if zweck not in ZWECK_LESBAR:
        raise ValueError(f"unbekannter Zweck {zweck!r}")
    offen = [w for w in fakten.widersprueche if w.feld == "auftragszweck"]
    h = fakten.herkunft.get("auftragszweck")
    if not offen and h is not None and h.art == "text" and fakten.auftragszweck not in (None, zweck):
        return leite_ab(fakten.model_copy(update={"widersprueche": [
            *fakten.widersprueche, _zweck_widerspruch(h.beleg, fakten.auftragszweck, zweck, "gewaehlt_danach")]}))
    herkunft = {**fakten.herkunft, "auftragszweck": Herkunft(art="knopf", beleg="geklärt" if offen else None)}
    update: dict[str, Any] = {"auftragszweck": zweck,
                              "widersprueche": [w for w in fakten.widersprueche if w.feld != "auftragszweck"]}
    kat = fakten.herkunft.get("katalog_taetigkeit")
    if fakten.katalog_taetigkeit and (kat is None or kat.art in ("modell", "system")) and zweck != "fuer_kunden":
        update["katalog_taetigkeit"] = None
        herkunft.pop("katalog_taetigkeit", None)
    return leite_ab(fakten.model_copy(update={**update, "herkunft": herkunft}))


def zeilen_fuer_bestaetigung(fakten: Fakten) -> list[str]:
    """Die Einordnung in Sätzen für die Faktenbestätigung (Nutzer bestätigt Fakten, nicht Kategorien)."""
    zeilen = []
    if fakten.unternehmensart:
        zeilen.append(f"Ihr Unternehmen (Tätigkeit): {fakten.unternehmensart}")
    if fakten.auftragszweck:
        h = fakten.herkunft.get("auftragszweck")
        zusatz = _herkunft_text(h)
        zeilen.append(f"Zweck dieses Auftrags: {ZWECK_LESBAR[fakten.auftragszweck]}{zusatz}")
    if fakten.katalog_taetigkeit is not None:
        h = fakten.herkunft.get("katalog_taetigkeit")
        text = ("Ihr Unternehmen gehört zu den typischen Verwertern (z. B. Verlag, Agentur, Galerie, Theater)"
                if fakten.katalog_taetigkeit else "Ihr Unternehmen ist kein typischer Verwerter")
        zeilen.append(f"{text}{_herkunft_text(h)}")
    return zeilen


def _herkunft_text(h: Optional[Herkunft]) -> str:
    if h is None:
        return ""
    if h.art == "text" and h.beleg:
        return f" ({HERKUNFT_LESBAR['text']}: „{h.beleg}“)"
    return f" ({HERKUNFT_LESBAR.get(h.art, h.art)})"
