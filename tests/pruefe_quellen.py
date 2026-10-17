"""Prüft den Quellenbestand: Inhaltsgleiche Dateien (SHA-256) müssen in quellen/DUPLIKATE.md dokumentiert sein,
alle Einträge in quellen/index.csv müssen auf vorhandene Dateien zeigen, und PDFs müssen mit %PDF beginnen.
Aufruf (im Repo-Hauptordner):  python tests/pruefe_quellen.py
Ändert keine Quelldatei."""
import csv, hashlib, pathlib, sys, collections
root = pathlib.Path(__file__).resolve().parent.parent
q = root/'quellen'
fehler = []
hashes = collections.defaultdict(list)
for f in sorted(q.rglob('*')):
    if not f.is_file() or f.name in ('index.csv', 'archivnachweise.csv', 'PRUEFSUMMEN.csv') or f.suffix == '.md':
        continue
    data = f.read_bytes()
    if f.suffix.lower() == '.pdf' and not data.startswith(b'%PDF'):
        fehler.append(f'{f.relative_to(q)}: keine gültige PDF-Datei (Fehlerseite oder Abbruch?)')
    hashes[hashlib.sha256(data).hexdigest()].append(str(f.relative_to(q)).replace('\\', '/'))
dup_doc = (q/'DUPLIKATE.md').read_text(encoding='utf-8') if (q/'DUPLIKATE.md').exists() else ''
gruppen = [g for g in hashes.values() if len(g) > 1]
for g in gruppen:
    for name in g:
        if name not in dup_doc:
            fehler.append(f'Inhaltsgleiche Datei nicht in DUPLIKATE.md dokumentiert: {name}')
idx = list(csv.reader(open(q/'index.csv', encoding='utf-8', newline='')))[1:]
indexiert = set()
for r in idx:
    if not r or not r[0]: continue
    indexiert.add(r[0])
    if not (q/r[0]).exists():
        fehler.append(f'index.csv verweist auf fehlende Datei: {r[0]}')
alle = {n for g in hashes.values() for n in g}
for n in sorted(alle - indexiert):
    fehler.append(f'Datei ohne Eintrag in index.csv: {n}')
print(f'{len(alle)} Quelldateien, {len(hashes)} verschiedene Inhalte, {len(gruppen)} Gruppen inhaltsgleicher Dateien, {len(idx)} Indexeinträge.')
if fehler:
    print('FEHLER:'); [print(' -', x) for x in fehler]; sys.exit(1)
print('Keine Fehler im Quellenbestand.')
