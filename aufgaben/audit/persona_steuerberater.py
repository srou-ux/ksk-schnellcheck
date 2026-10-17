import sys; sys.path.insert(0,'.')
from app import router, bestaetigung
from app.llm.fake import FakeLLM
FRAGEN = [
 "Mandant ist eine Werbeagentur. 2025 hat sie an einen Grafiker 2.400 € gezahlt. Ist das abgabepflichtig?",
 "Ein Verein hat 2026 einen Webdesigner mit 900 € beauftragt. Müssen wir KSA zahlen?",
 "Wie hoch ist die monatliche Vorauszahlung 2026, wenn die Bemessungsgrundlage im Vorjahr 31.500 € war?",
 "Bis wann muss die Jahresmeldung für 2025 abgegeben werden?",
 "Welche Tätigkeiten gelten als künstlerisch oder publizistisch?",
 "Wie lange müssen wir die Aufzeichnungen aufbewahren?",
 "Unser Mandant hat 2024 einen Fotografen mit 1.800 € bezahlt, davon 300 € nachgewiesene Fahrtkosten. Bemessungsgrundlage?",
 "Was sagt das BSG zur Abgrenzung bei Werbeagenturen?",
 "Der Mandant hat 2025 vier Veranstaltungen gemacht und dafür Künstler mit insgesamt 3.500 € bezahlt.",
 "Wie hoch war der Abgabesatz 2024?",
 "Wir haben eine GmbH als Dienstleister, 5.000 € 2025. Abgabepflichtig?",
 "Wir haben die Meldung zu spät abgegeben, Rückstand 2.000 €, 4 Monate, 2025. Säumniszuschlag?",
]
for f in FRAGEN:
    llm=FakeLLM()
    try:
        a=router.bearbeite_frage(f,llm)
        if a.sitzungskennung and a.fakten_hash:
            bestaetigung.SPEICHER.bestaetige(a.sitzungskennung,a.fakten_hash)
            a2=router.fuehre_nach_bestaetigung_aus(a.sitzungskennung,llm); kl=a2.ergebnisklasse; txt=a2.antwort
            stufe="bestätigt"
        else: kl=a.ergebnisklasse; txt=a.antwort; stufe="direkt"
    except Exception as e:
        kl="FEHLER"; txt=f"{type(e).__name__}: {e}"; stufe="-"
    print("FRAGE:",f); print("  ->",stufe,"|",kl); print("  ",txt.replace("\n"," ")[:330]); print()
