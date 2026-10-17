"""Konsistenzprüfung für Regelkatalog, Testfälle und Quellenverweise.
Aufruf (im Repo-Hauptordner):  python tests/pruefe_regelwerk.py
Prüft: eindeutige IDs, Pflichtfelder, Regelverweise der Testfälle, existierende Quelldateien.
Prüft NICHT die inhaltliche Richtigkeit (das macht der Steuerberater)."""
import re, sys, pathlib, openpyxl
root = pathlib.Path(__file__).resolve().parent.parent
fehler = []
rk = openpyxl.load_workbook(root/'regelwerk/Regelkatalog_24_KSVG_Entwurf.xlsx').worksheets[0]
hdr = [c.value for c in rk[1]]
regeln = {}
for r in rk.iter_rows(min_row=2, values_only=True):
    if not r[0]: continue
    if r[0] in regeln: fehler.append(f'Doppelte Regel-ID {r[0]}')
    regeln[r[0]] = dict(zip(hdr, r))
    for pflicht in ('Gruppe','Norm','Rechtsfolge','Fundstelle','Quelldatei(en)','Prüfstatus'):
        if not regeln[r[0]].get(pflicht): fehler.append(f'{r[0]}: Feld {pflicht} leer')
    for pfad in re.findall(r'quellen/[\w\-./ÄÖÜäöüß]+?\.(?:pdf|txt|csv)', str(regeln[r[0]].get('Quelldatei(en)',''))):
        if not (root/pfad).exists(): fehler.append(f'{r[0]}: Quelldatei fehlt: {pfad}')
tw = openpyxl.load_workbook(root/'regelwerk/Testfaelle_BSG_Urteile.xlsx')['Testfälle']
ids = set()
for r in tw.iter_rows(min_row=2, values_only=True):
    if not r[0]: continue
    if r[0] in ids: fehler.append(f'Doppelte Test-ID {r[0]}')
    ids.add(r[0])
    for i,n in enumerate(['ID','Gruppe','Beschreibung','Jahr','Eingaben','Erwartetes Ergebnis','Begründung','Fundstelle','Vorbehalt','Prüfstatus']):
        if i == 3: continue
        if not r[i] and r[0] != 'S-04': fehler.append(f'{r[0]}: {n} leer')
    for m in re.findall(r'R-\d+', str(r[7])):
        if m not in regeln: fehler.append(f'{r[0]}: verweist auf unbekannte Regel {m}')
fk = openpyxl.load_workbook(root/'regelwerk/Fragenkatalog_Chatbot_Entwurf.xlsx').worksheets[0]
fids, luecken, nfr = set(), 0, 0
for r in fk.iter_rows(min_row=2, values_only=True):
    if not r[0]: continue
    nfr += 1
    if r[0] in fids: fehler.append(f'Doppelte Frage-ID {r[0]}')
    fids.add(r[0])
    refs = re.findall(r'R-\d+', str(r[3]))
    for m in refs:
        if m not in regeln: fehler.append(f'{r[0]}: verweist auf unbekannte Regel {m}')
    if not refs:
        luecken += 1
        if 'fehlt' not in str(r[5]): fehler.append(f'{r[0]}: ohne Regel, aber nicht als Lücke markiert')
    elif 'fehlt' in str(r[5]): fehler.append(f'{r[0]}: mit Regel, aber als Lücke markiert')
print(f'{nfr} Fragen im Fragenkatalog, davon {luecken} sichtbare Lücken.')
print(f'{len(regeln)} Regeln, {len(ids)} Testfälle geprüft.')
if fehler:
    print('FEHLER:'); [print(' -', f) for f in fehler]; sys.exit(1)
print('Keine formalen Fehler.')
