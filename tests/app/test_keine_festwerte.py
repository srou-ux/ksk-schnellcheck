"""Hard-Coding-Wächter für app/ (RAG-Auftrag, 'Keine Festwerte im Code'; CLAUDE.md Regel 2).

Durchsucht alle Python-Dateien unter app/ nach Jahreszahlen 19xx/20xx (als Zahl oder in Texten),
Euro- und Prozentbeträgen, '§ '-Verweisen, 'BSG' und 'B 12' -- außerhalb von Kommentaren und
Docstrings. Jeder Treffer ist ein Testfehler, außer er steht in der kleinen, begründeten
Ausnahmeliste unten. Rechtswerte gehören in regelwerk/ (Excel) bzw. kern/parameter.json,
Fundstellen in die Quellen und den Regelkatalog."""
from __future__ import annotations

import io
import re
import tokenize
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"

MUSTER = {
    "Jahreszahl": re.compile(r"(?<!\d)(19|20)\d\d(?!\d)"),
    "Eurobetrag": re.compile(r"\d[\d.,]*\s*(?:€|EUR\b|Euro\b)"),
    "Prozentsatz": re.compile(r"\d[\d.,]*\s*(?:%|Prozent\b)"),
    "Paragraf": re.compile(r"§ "),
    "BSG": re.compile(r"\bBSG\b"),
    "B 12": re.compile(r"\bB 12\b"),
}

# (Datei relativ zu app/, Art, Textstück) -> Begründung. Klein halten; jede Zeile begründen.
AUSNAHMEN = {
    ("llm/mistral.py", "Eurobetrag", "900 statt 1.200 Euro"):
        "Beispielsatz im Extraktions-Prompt (wie ein Nutzer eine Korrektur schreibt), kein Rechtswert",
    ("llm/mistral.py", "Eurobetrag", "zu je 200 Euro"):
        "Beispielsatz im Extraktions-Prompt (Mengenangabe), kein Rechtswert",
    ("llm/mistral.py", "Eurobetrag", "Rechnungen mit enthaltenen Teilbetra"):
        "Beispielsatz im Extraktions-Prompt ('davon'), kein Rechtswert",
    ("llm/mistral.py", "BSG", "Gerichts-/Urteilswoerter"):
        "Verbotsliste im Prompt: das Modell darf diese Wörter NICHT schreiben",
    ("schema.py", "Jahreszahl", "1980"):
        "technische Plausibilitätsgrenze des Eingabefelds Jahr (bewusst so, aufgaben/FUNDE_Chatbot.md), kein Rechtsjahr",
}


def _treffer() -> list[tuple[str, int, str, str]]:
    erg = []
    for pfad in sorted(APP.rglob("*.py")):
        rel = pfad.relative_to(APP).as_posix()
        quelltext = pfad.read_text(encoding="utf-8")
        vorher = None
        # Ab Python 3.12 zerlegt tokenize f-Strings in FSTRING_START/MIDDLE/END; bis 3.11 ist ein
        # f-String ein einziges STRING-Token. Beide Fälle gleich prüfen (sonst findet der Wächter
        # unter 3.13 weniger als unter 3.11, gesehen am 13.10.2026).
        fstring_mitte = getattr(tokenize, "FSTRING_MIDDLE", None)
        for tok in tokenize.generate_tokens(io.StringIO(quelltext).readline):
            if fstring_mitte is not None and tok.type == fstring_mitte:
                for art, m in MUSTER.items():
                    if m.search(tok.string):
                        erg.append((rel, tok.start[0], art, tok.string))
            elif tok.type == tokenize.STRING:
                ist_docstring = vorher in (None, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.NL)
                if not ist_docstring:
                    for art, m in MUSTER.items():
                        if m.search(tok.string):
                            erg.append((rel, tok.start[0], art, tok.string))
            elif tok.type == tokenize.NUMBER and MUSTER["Jahreszahl"].fullmatch(tok.string):
                erg.append((rel, tok.start[0], "Jahreszahl", tok.string))
            if tok.type not in (tokenize.COMMENT, tokenize.NL):
                vorher = tok.type
    return erg


def _erlaubt(rel: str, art: str, text: str) -> bool:
    return any(rel == d and art == a and stueck in text for (d, a, stueck) in AUSNAHMEN)


class KeineFestwerteInApp(unittest.TestCase):
    def test_keine_festwerte_ausser_begruendeten_ausnahmen(self):
        verstoesse = [f"{rel}:{zeile} {art}: {text[:90]}" for rel, zeile, art, text in _treffer()
                      if not _erlaubt(rel, art, text)]
        self.assertEqual(verstoesse, [], "Festwerte im Code gefunden:\n" + "\n".join(verstoesse))

    def test_waechter_findet_einen_eingebauten_festwert(self):
        probe = 'SATZ = "Der Abgabesatz 2026 beträgt 4,9 % (KSVG § 26)"'
        gefunden = {art for art, m in MUSTER.items() if m.search(probe)}
        self.assertTrue({"Jahreszahl", "Prozentsatz", "Paragraf"} <= gefunden)

    def test_ausnahmen_werden_noch_gebraucht(self):
        treffer = _treffer()
        unbenutzt = [k for k in AUSNAHMEN if not any(rel == k[0] and art == k[1] and k[2] in t for rel, _, art, t in treffer)]
        self.assertEqual(unbenutzt, [], "Ausnahme ohne Treffer -- bitte aus der Liste streichen")


if __name__ == "__main__":
    unittest.main(verbosity=2)
