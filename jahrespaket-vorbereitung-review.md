# Review: automatische Vorbereitung eines Jahrespakets

Stand: 7. Oktober 2026

## Umgesetzter Ablauf

Auf der Admin-Seite kann ein Jahr eingegeben und mit **„Mit KI vorbereiten“** gestartet werden. Die Anwendung legt transaktional eine neue, ungeprüfte und inaktive Paketversion sowie einen Hintergrundjob an. Der Job übergibt ausschließlich das Jahr und den fest konfigurierten öffentlichen Quellenumfang an OpenAI. Kundenfälle, Kundendokumente und Chats werden nicht gelesen oder übertragen.

OpenAI recherchiert mit dem Responses-Web-Search-Tool nur auf der Domain-Allowlist. Eine Fundstelle wird nur weiterverarbeitet, wenn ihre URL auch im tatsächlichen Quellenoutput des Web-Suchtools vorkommt. Das Backend validiert anschließend HTTPS-Ziel, Domain und DNS-Adressen bei jedem Redirect, begrenzt Dateityp, Größe und Laufzeit und archiviert das heruntergeladene Original über die vorhandene unveränderliche Archivfunktion. Zeitlich nicht belegte Funde, Downloadfehler und fehlende Anforderungsbereiche bleiben als Lücken sichtbar.

Es gibt keine Freigabe, Aktivierung, Mistral-Umschaltung oder Verarbeitung von Kundenunterlagen in diesem Schritt.

## Persistenz und Migration

Migration `006-jahrespaket-vorbereitung` in `src/lib/db.ts` ergänzt:

- `jahrespaket_vorbereitungen`: Paketbezug, Jahr, Anforderungs-/Promptversion, Status, Schritt, Fortschritt, Modell, Lücken, Fehler und Zeitpunkte.
- `jahrespaket_quellenfunde`: recherchierte Quelle, Kategorie, URL, Herausgeber, Dokumentstand, Zeitbezug, Verarbeitungsstatus, Archivquellen-ID und konkreter Fehler.
- Partieller Unique-Index verhindert zwei gleichzeitig aktive Vorbereitungen für dasselbe Jahr.
- Der bestehende `jobs`-Bestand wird mit dem neuen Typ `jahrespaket_vorbereitung` weiterverwendet. Der bestehende Kundenfall-Worker beansprucht ausdrücklich nur `pipeline`-Jobs.
- Das bestehende Archiv `archiv_quellen` und `jahrespaket_quellen` werden unverändert weiterverwendet; bestehende Daten werden nicht gelöscht oder umgeschrieben.

## Geänderter Code

- `src/lib/jahrespaket-vorbereitung.ts`: Entwurf/Job anlegen, OpenAI-Recherche, Suchquellennachweis, abgesicherter Download, Archivierung, Lücken- und Fortschrittsprotokoll.
- `src/lib/jahrespaket-vorbereitung-queue.ts`: eigener serieller Worker für Vorbereitungsjobs.
- `src/app/api/admin/jahrespakete/vorbereiten/route.ts`: Start und Übersicht.
- `src/app/api/admin/jahrespakete/vorbereiten/[id]/route.ts`: Polling eines konkreten Laufs.
- `src/app/admin/jahrespaket-vorbereitung-panel.tsx` und `src/app/admin/page.tsx`: Jahreingabe, Start, Fortschritt, Quellenstatus, Fehler und Lücken.
- `config/ksk-quellenanforderungen-v1.json`: versionierter fachlicher Mindestumfang, amtliche Domain-Allowlist und Downloadgrenze.
- `.env.example`: nur die Variablennamen `OPENAI_API_KEY` und `OPENAI_RESEARCH_MODEL`, keine Schlüssel.
- `package.json` / `package-lock.json`: offizielles Paket `openai` 7.30.0.

## Tests und tatsächliche Ergebnisse

- `tests/jahrespaket-vorbereitung.test.ts`: Entwurf/Job, keine Pipeline-Verwechslung, Parallelstartsperre, Erhalt bestehender Falldaten, Archivzuordnung, sichtbare Zeitlücke und Downloadfehler.
- `e2e/jahrespaket-vorbereitung.spec.ts`: sichtbarer Admin-Einstieg und ausdrücklicher Hinweis auf den ungeprüften/inaktiven Entwurf.
- TypeScript: `npx tsc --noEmit` — **bestanden**.
- Gesamte Vitest-Suite: `npm test` — **13 Dateien, 77 Tests bestanden**.
- Gezielter ESLint-Lauf für alle neuen/geänderten Ablaufdateien: **bestanden**. Der projektweite Lauf bleibt wegen fünf bereits vorhandener Fehler in `library-panel.tsx`, `werte-panel.tsx`, `admin-console.tsx` und `case-workspace.tsx` rot.
- Next.js-Produktions-Build: `npm run build` — **bestanden**.
- Echter OpenAI-Aufruf: **nicht ausgeführt**, weil kein Schlüssel gesetzt wurde. Der Ablauf ist über injizierte Recherche- und Download-Doubles geprüft; dies ist kein Ersatz für den späteren kontrollierten Live-Test.
- Browserprüfung: **offen**. Der neue Abnahmetest wurde gestartet, lief in dieser Ausführungsumgebung aber nach 181 Sekunden ohne Testausgabe in das Zeitlimit; Playwright Chromium ist dort nicht installiert. Der Test wird ausdrücklich nicht als bestanden gewertet. Sobald der Browser verfügbar ist, erneut ausführen: `npm run test:e2e -- e2e/jahrespaket-vorbereitung.spec.ts`.

## Lokale Befehle

Falls Node nicht im `PATH` liegt:

```powershell
$env:Path = 'C:\Program Files\nodejs;' + $env:Path
npm test
npx tsc --noEmit
npm run test:e2e -- e2e/jahrespaket-vorbereitung.spec.ts
```

Für den kontrollierten Live-Ablauf den Schlüssel nur lokal serverseitig in `.env.local` als `OPENAI_API_KEY` setzen, Entwicklungsserver starten und ein einzelnes Jahr über `/admin` vorbereiten. `.env.local`, Schlüssel und heruntergeladene Inhalte gehören nicht in einen Reviewexport.
