"""Regression: getrennte PDF-Textobjekte in einer visuellen Rechnungszeile."""
import io
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from app.dokument_lesen import lese, formularvorschlaege, textpositionen


def layout_pdf():
    w = PdfWriter()
    p = w.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                            NameObject('/Subtype'): NameObject('/Type1'),
                            NameObject('/BaseFont'): NameObject('/Helvetica')})
    p[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): font})})
    texte = [(40,750,'RECHNUNGSEMPFAENGER'),(350,750,'RECHNUNGSSTELLERIN'),
             (40,725,'Baeckerei Test GmbH'),(350,725,'Anna Beispiel'),
             (40,680,'Rechnungsdatum: 01.10.2026'),
             (40,600,'1'),(100,600,'Logo-Gestaltung'),(440,600,'1.500,00 EUR'),
             (40,550,'Umsatzsteuer 19 %'),(440,550,'285,00 EUR'),
             (40,520,'Gesamtbetrag'),(440,520,'1.785,00 EUR')]
    stream = DecodedStreamObject()
    stream.set_data('\n'.join(f'BT /F1 10 Tf {x} {y} Td 12 TL ({s}) Tj T* ET' for x,y,s in texte).encode())
    p[NameObject('/Contents')] = w._add_object(stream)
    b = io.BytesIO(); w.write(b); return b.getvalue()


class LayoutImport(unittest.TestCase):
    def test_spalten_pdf_fuellt_position_und_empfaenger(self):
        raw = layout_pdf()
        # Belegt die Ursache: Standardextraktion hat Beschreibung und Betrag auf getrennten Zeilen.
        self.assertIn('Logo-Gestaltung\n', PdfReader(io.BytesIO(raw)).pages[0].extract_text())
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'rechnung.pdf'; p.write_bytes(raw)
            r = lese(p,'.pdf')
        self.assertEqual([(x['bezeichnung'],x['betrag']) for x in r['positionen']],
                         [('Logo-Gestaltung','1500.00')])
        self.assertEqual(r['formularvorschlaege']['unternehmensart']['wert'],'Baeckerei Test GmbH')
        self.assertNotIn('jahr',r['formularvorschlaege'])
        self.assertNotIn('auftragnehmer_typ',r['positionen'][0])
        self.assertIn('Seite 1',r['positionen'][0]['beleg'])

    def test_widersprechende_empfaenger_nicht_vorbelegen(self):
        self.assertEqual(formularvorschlaege('Auftraggeber: Firma A\nAuftraggeber: Firma B'),{})

    def test_absender_nicht_als_empfaenger(self):
        self.assertEqual(formularvorschlaege('Rechnungsstellerin: Anna Beispiel'),{})
        self.assertEqual(formularvorschlaege('RECHNUNGSEMPFÄNGER\nRECHNUNGSSTELLERIN\nAnna Beispiel'),{})

    def test_unklare_spalten_nicht_verknuepfen(self):
        self.assertEqual(formularvorschlaege('RECHNUNGSEMPFÄNGER    RECHNUNGSSTELLERIN\nFirma A'),{})

    def test_menge_und_zwei_preisspalten_nicht_addieren(self):
        self.assertEqual(textpositionen('2  Logo  750,00 EUR  1.500,00 EUR','Seite 1'),[])

    def test_rechnungsdatum_und_zahlungsziel_sind_keine_zahlung(self):
        self.assertEqual(formularvorschlaege('Rechnungsdatum: 01.10.2026\nZahlungsziel: 15.10.2026'),{})


if __name__ == '__main__':
    unittest.main()
