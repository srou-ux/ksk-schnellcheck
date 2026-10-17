# Chatbot – Musterdialoge (Entwurf)

Status: Entwurf – vom Steuerberater zu prüfen. Die Dialoge zeigen Ton und Schema. Inhalte stützen sich nur auf Regeln/Testfälle im Repo (E-01, E-02, E-05, B-03). Sie sind zugleich Abnahmetests für den Bot: Ergebnisklasse und Fundstellen müssen stimmen.

## Dialog 1 – Eigenwerbung, alte Rechtslage (Test E-01)
**StB:** Mandant Kanzlei, 2017 einmalig Website, 1.750 € netto an einen freien Webdesigner. Abgabepflichtig?

**Bot:**
- **Ergebnis (Vorschlag):** Nicht abgabepflichtig.
- **Norm:** § 24 Abs. 1 Satz 2, Abs. 3 Satz 1 KSVG a. F. (Fassung bis 31.12.2022).
- **Subsumtion:** Die Überschreitung von 450 € allein genügt nicht. Erforderlich sind zusätzlich eine gewisse Regelmäßigkeit/Dauerhaftigkeit und ein nicht unerhebliches wirtschaftliches Ausmaß. Bei einem einzelnen Auftrag (zwei Zahlungen) ohne bekannte weitere Aufträge fehlt beides nach dem festgestellten Sachverhalt.
- **Rechtsprechung:** BSG 01.06.2022, B 3 KS 3/21 R, Rn. 14, 15, 18, 25.
- **Gegenansicht/Risiko:** Gibt es weitere Aufträge an Künstler oder Publizisten in 2017, kann die Wertung kippen. Bitte prüfen.
- **Rückfrage:** Gab es 2017 weitere Aufträge, auch an andere Künstler?
- *Entwurf – vom Steuerberater zu prüfen.*

## Dialog 2 – derselbe Fall in 2024 (Test E-02)
**StB:** Derselbe Fall, aber 2024.

**Bot:**
- **Ergebnis (Vorschlag):** Abgabepflichtig.
- **Norm:** § 24 Abs. 2 Satz 1 Nr. 1, Satz 2 KSVG (Fassung ab 01.01.2023, Eigenwerbung): Summe der Entgelte für einen oder mehrere Aufträge übersteigt 450 €.
- **Hinweis zur Rechtsprechung:** Das Urteil BSG 01.06.2022, B 3 KS 3/21 R bezieht sich auf die alte Fassung („nicht nur gelegentlich“) und trägt für 2024 kein „nicht abgabepflichtig“. Es dient nur zur Abgrenzung der alten Rechtslage (Rn. 15).
- **Vorbehalt:** Der Fassungswechsel (8. SGB IV-ÄndG) ist im Repo nur als Webarchiv-Textauszug belegt, nicht als natives PDF.
- *Entwurf – vom Steuerberater zu prüfen.*

## Dialog 3 – Grenzfall (Test E-05)
**StB:** Einmalige Kampagne, 5.000 €, Jahr 2017, Historie unbekannt.

**Bot:**
- **Ergebnis (Vorschlag):** Grenzfall → Steuerberater entscheidet.
- **Begründung:** Das Urteil verlangt für Eigenwerber eine Würdigung aller Umstände. Ein einmaliger Auftrag ist nicht automatisch regelmäßig; ob das wirtschaftliche Ausmaß genügt, kann ich nicht entscheiden.
- **Fundstelle:** BSG 01.06.2022, B 3 KS 3/21 R, Rn. 24, 25.
- **Rückfragen:** Frühere/spätere Aufträge? Wiederholungsabsicht?
- *Entwurf – vom Steuerberater zu prüfen.*

## Dialog 4 – Bemessungsgrundlage, Reisekosten (Test B-03)
**StB:** 2025, Designer 3.000 € Honorar, 80 € Bahnfahrt nachgewiesen erstattet. Was ist die Bemessungsgrundlage?

**Bot:**
- **Ergebnis (Vorschlag):** 3.000 €; die nachgewiesenen Reisekosten zählen nicht mit, soweit sie innerhalb der steuerlichen Grenze liegen.
- **Fundstelle:** KSVEntgV § 1 Nr. 1; KSK-Info 10, Abschn. 2–3. Kennzeichnung: Auslegung der KSK (Verwaltungspraxis), kein Gesetz.
- *Entwurf – vom Steuerberater zu prüfen.*

## Dialog 5 – Urteil nicht in der Basis
**StB:** Gibt es ein LSG-Urteil zu Podcast-Produktionen?

**Bot:**
- **Ergebnis:** Nicht abgedeckt (Quelle fehlt).
- Ein solches Urteil liegt nicht in meiner Quellenbasis. Ich nenne kein Aktenzeichen aus dem Gedächtnis. Bitte in juris/openJur recherchieren. Ihre Frage wird (anonymisiert) im Lückenprotokoll vermerkt.
- *Entwurf – vom Steuerberater zu prüfen.*
