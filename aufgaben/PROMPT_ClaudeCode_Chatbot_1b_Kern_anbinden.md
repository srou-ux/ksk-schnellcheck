# Auftrag an Claude Code – Chatbot Teil 1b: echten Kern anbinden

Befund 1 und 2 aus `aufgaben/FUNDE_Chatbot.md` sind behoben: `kern/`, `scripts/start_codespace.sh` und `.devcontainer/` waren wegen der `.gitignore` nie im Repo und sind jetzt hochgeladen. Der Kern ist ein Teil des Repos und kein Testdoppel mehr.

1. `git pull`. Die Kern-Tests müssen laufen: `python tests/test_kern.py` (24 Tests), `python tests/lauf_testfaelle.py`.
2. `app/router.py`: Import von `kern.rechnen` nicht mehr defensiv. Die Abschnitte "Kern fehlt" aus Router, Test (`TestOhneKern`) und Doku entfernen. Der Router ruft den echten Kern auf. Das Testdoppel `tests/app/kern_testdouble.py` wird nur noch dort gebraucht, wo ein Kernfehler simuliert werden soll; sonst entfernen.
3. Die Aufrufe müssen zur echten Schnittstelle passen: Das Jahr ist Pflicht (keine Standardjahre). `musikverein_schueler(jahr, schueler, …)`, `summe_positionen(positionen, jahr)`, `schaetzung_ausland(brutto, jahr)`. Zahlen und Schwellen stehen im Regelregister der Excel, nicht im Code; im `app/` keine Festwerte.
4. Verdrahten, was der Kern kann: Eigenwerbung, typische Verwerter, Positionen/Bemessung, Veranstaltungen, Vorauszahlung, Säumniszuschlag, Verpflegung, Übungsleiter, Kommission, Schätzung Ausland, Rechnungsanalyse (`analysiere_rechnung`). Dialog 4 (Reisekosten-Position) wird damit anbindbar.
5. Abnahmetests gegen den echten Kern: Dialoge 1–5 und die Fälle aus `regelwerk/testfaelle_maschinenlesbar.json` über die ganze Kette (FakeLLM gibt die Fakten vor). Ergebnisklasse und Zahlen müssen mit dem Kern übereinstimmen; 2017 bleibt "Nicht abgedeckt" (weiter als Befund melden, nicht anpassen).
6. Befund 6 (Jahr-Frage bei reinen Rechtsprechungsfragen): so lösen, dass eine Frage ohne Rechnung (nur Rechtsprechung/Auslegung) ohne Jahr beantwortet werden darf, aber nie mit einer Zahl.
7. `aufgaben/FUNDE_Chatbot.md` aktualisieren (behobene Befunde markieren). Vor dem Push `pip install -r app/requirements.txt` und `python -m unittest discover -s tests/app` — alle Tests, auch `test_main`. Dann `git pull --rebase origin main && git push origin main`.

Antwort nur: Dateien, Testergebnis (Anzahl), offene Befunde, was nicht geht.
