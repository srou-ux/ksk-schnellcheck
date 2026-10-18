# Jahrespakete — Prüfexport

Stand: 7. Oktober 2026

Dieser Export enthält ausschließlich den ersten persistenten Jahrespaket-Schritt. Nicht enthalten sind Schlüssel, Umgebungsdateien, SQLite-Inhalte, Kundenunterlagen und Falldaten.

## Geprüfte Anforderungen

| Anforderung | Absicherung |
|---|---|
| Eindeutige Versionen pro Jahr | Transaktion `BEGIN IMMEDIATE`, Ermittlung der nächsten Version innerhalb der Schreibtransaktion und eindeutiger Index auf `(jahr, version)`. |
| Neue Entwürfe nicht freigegeben und inaktiv | Der Insert setzt fest `status = 'entwurf'` und `is_active = 0`; diese Werte sind keine Eingabeparameter. |
| Aktive Pakete müssen freigegeben sein | Insert- und Update-Trigger brechen jeden Zustand `is_active = 1` mit einem anderen Status als `freigegeben` ab. |
| Keine doppelte Version bei gleichzeitiger Anlage | `BEGIN IMMEDIATE` serialisiert konkurrierende SQLite-Schreiber vor `MAX(version) + 1`; der eindeutige Index ist die zweite Sicherung. |
| Bestehende Falldaten bleiben erhalten | Die Migration legt Tabelle, Indizes und Trigger ausschließlich mit `IF NOT EXISTS` an. Ein Test legt einen Fall an, erzeugt danach ein Paket und vergleicht den Fall unverändert. |
| Leere Entwürfe sichtbar unvollständig | Solange kein `content_hash` existiert, zeigt das Panel ausdrücklich `unvollständig`. |

Freigabe und Aktivierung sind in diesem Schritt noch keine verfügbaren Aktionen. Die Felder und Invarianten bereiten ihre spätere getrennte Implementierung vor.

## Vollständige Migration für Jahrespakete

Aus `src/lib/db.ts`:

```sql
CREATE TABLE IF NOT EXISTS jahrespakete (
  id TEXT PRIMARY KEY,
  jahr INTEGER NOT NULL,
  version INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'entwurf',
  methodology_version TEXT NOT NULL,
  rules_stamp TEXT NOT NULL,
  content_hash TEXT,
  pruefer_name TEXT,
  freigabe_kommentar TEXT,
  freigegeben_am TEXT,
  is_active INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS jahrespakete_jahr_version
  ON jahrespakete (jahr, version);

CREATE UNIQUE INDEX IF NOT EXISTS jahrespakete_aktive_version
  ON jahrespakete (jahr) WHERE is_active = 1;

CREATE TRIGGER IF NOT EXISTS jahrespakete_aktiv_nur_freigegeben_insert
  BEFORE INSERT ON jahrespakete
  WHEN NEW.is_active = 1 AND NEW.status != 'freigegeben'
  BEGIN
    SELECT RAISE(ABORT, 'Ein aktives Jahrespaket muss freigegeben sein.');
  END;

CREATE TRIGGER IF NOT EXISTS jahrespakete_aktiv_nur_freigegeben_update
  BEFORE UPDATE OF is_active, status ON jahrespakete
  WHEN NEW.is_active = 1 AND NEW.status != 'freigegeben'
  BEGIN
    SELECT RAISE(ABORT, 'Ein aktives Jahrespaket muss freigegeben sein.');
  END;

INSERT OR IGNORE INTO schema_migrations (id, applied_at)
  VALUES ('004-jahrespakete', :aktueller_zeitpunkt);
```

Die tatsächliche Implementierung verwendet für den Migrationseintrag das vorhandene vorbereitete Statement `note.run("004-jahrespakete", stamp)`.

## Vollständige Typen und neue Datenbankfunktionen

Aus `src/lib/db.ts`:

```ts
export type JahrespaketStatus = "entwurf" | "zur_freigabe" | "freigegeben" | "ersetzt" | "zurueckgezogen";

export interface JahrespaketRow {
  id: string;
  jahr: number;
  version: number;
  status: JahrespaketStatus;
  methodology_version: string;
  rules_stamp: string;
  content_hash: string | null;
  pruefer_name: string | null;
  freigabe_kommentar: string | null;
  freigegeben_am: string | null;
  is_active: number;
  created_at: string;
}

export function listJahrespakete(): JahrespaketRow[] {
  return getDb().prepare("SELECT * FROM jahrespakete ORDER BY jahr DESC, version DESC").all() as unknown as JahrespaketRow[];
}

export function legeJahrespaketEntwurfAn(input: { jahr: number; methodologyVersion: string; rulesStamp: string }): JahrespaketRow {
  if (!Number.isSafeInteger(input.jahr) || input.jahr < 1900 || input.jahr > 2200) {
    throw new Error("Das Paketjahr ist ungültig.");
  }
  const methodologyVersion = input.methodologyVersion.trim();
  const rulesStamp = input.rulesStamp.trim();
  if (!methodologyVersion || !rulesStamp) throw new Error("Methodikversion und Regelstand werden benötigt.");
  const database = getDb();
  const id = crypto.randomUUID();
  database.exec("BEGIN IMMEDIATE");
  try {
    const row = database.prepare("SELECT MAX(version) AS version FROM jahrespakete WHERE jahr = ?").get(input.jahr) as { version: number | null };
    const version = (row.version ?? 0) + 1;
    database.prepare(`INSERT INTO jahrespakete (
        id, jahr, version, status, methodology_version, rules_stamp, content_hash,
        pruefer_name, freigabe_kommentar, freigegeben_am, is_active, created_at
      ) VALUES (?, ?, ?, 'entwurf', ?, ?, NULL, NULL, NULL, NULL, 0, ?)`).run(
      id,
      input.jahr,
      version,
      methodologyVersion,
      rulesStamp,
      now(),
    );
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
  return database.prepare("SELECT * FROM jahrespakete WHERE id = ?").get(id) as unknown as JahrespaketRow;
}
```

Testläufe lesen keine lokale Secret-Datei. Die vorhandene Initialisierung lautet jetzt:

```ts
export function getDb(): DatabaseSync {
  if (process.env.NODE_ENV !== "test") loadSecrets();
  if (!db) {
    const dir = dataDir();
    mkdirSync(dir, { recursive: true });
    db = new DatabaseSync(path.join(dir, "ksk.sqlite"), { timeout: 10000 });
    db.exec("PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;");
    migrate(db);
  }
  return db;
}
```

## Vollständiges Jahrespaket-Panel

`src/app/admin/jahrespakete-panel.tsx`:

```tsx
import { listJahrespakete } from "@/lib/db";

function statusText(status: string): string {
  return status.replaceAll("_", " ");
}

export function JahrespaketePanel() {
  const pakete = listJahrespakete();

  return (
    <section className="space-y-4 rounded-xl border border-line bg-card p-4">
      <div>
        <h2 className="text-2xl">Jahrespakete</h2>
        <p className="mt-1 text-sm text-ink/70">
          Persistente Paketversionen je Jahr. Freigabe und Aktivierung werden getrennte, ausdrücklich bestätigte Aktionen.
        </p>
      </div>
      {pakete.length === 0 ? (
        <p className="rounded-md bg-paper px-4 py-3 text-sm">
          Noch keine Paketversion angelegt. Dieser erste Schritt stellt Datenmodell und Übersicht bereit; der geführte Paketaufbau folgt als nächster Admin-Schritt.
        </p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line">
              <th className="py-2 pr-3">Jahr</th>
              <th className="py-2 pr-3">Version</th>
              <th className="py-2 pr-3">Status</th>
              <th className="py-2 pr-3">Methodik</th>
              <th className="py-2 pr-3">Regelstand</th>
              <th className="py-2 pr-3">Vollständigkeit</th>
              <th className="py-2">Aktiv</th>
            </tr>
          </thead>
          <tbody>
            {pakete.map((paket) => (
              <tr key={paket.id} className="border-b border-line/60" data-testid="jahrespaket-zeile">
                <td className="py-2 pr-3">{paket.jahr}</td>
                <td className="py-2 pr-3">v{paket.version}</td>
                <td className="py-2 pr-3">{statusText(paket.status)}</td>
                <td className="py-2 pr-3">{paket.methodology_version}</td>
                <td className="py-2 pr-3">{paket.rules_stamp}</td>
                <td className="py-2 pr-3 font-semibold text-unclear" data-testid="jahrespaket-vollstaendigkeit">
                  {paket.content_hash ? "Inhalt erfasst" : "unvollständig"}
                </td>
                <td className="py-2">{paket.is_active ? "ja" : "nein"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
```

## Vollständige Einbindung

`src/app/admin/page.tsx`:

```tsx
import { LibraryPanel } from "./library-panel";
import { WertePanel } from "./werte-panel";
import { JahrespaketePanel } from "./jahrespakete-panel";

export const dynamic = "force-dynamic";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <p className="rounded-md bg-amber-50 px-4 py-3 text-sm font-semibold text-unclear">Testmodus — nicht produktiv</p>
      <JahrespaketePanel />
      <LibraryPanel />
      <WertePanel />
    </div>
  );
}
```

## Vollständige Tests

`tests/jahrespakete.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { createCase, getCase, getDb, legeJahrespaketEntwurfAn, listJahrespakete } from "../src/lib/db";

describe("Jahrespakete", () => {
  it("vergibt je Jahr eigenständige fortlaufende Versionen", () => {
    const erstes = legeJahrespaketEntwurfAn({ jahr: 2041, methodologyVersion: "v12", rulesStamp: "2040-10-01" });
    const zweites = legeJahrespaketEntwurfAn({ jahr: 2041, methodologyVersion: "v13", rulesStamp: "2040-11-15" });
    const anderesJahr = legeJahrespaketEntwurfAn({ jahr: 2042, methodologyVersion: "v13", rulesStamp: "2041-10-01" });

    expect([erstes.version, zweites.version, anderesJahr.version]).toEqual([1, 2, 1]);
    expect([erstes.status, zweites.status, anderesJahr.status]).toEqual(["entwurf", "entwurf", "entwurf"]);
    expect([erstes.is_active, zweites.is_active, anderesJahr.is_active]).toEqual([0, 0, 0]);
    expect(listJahrespakete()).toEqual(expect.arrayContaining([
      expect.objectContaining({ jahr: 2041, version: 1 }),
      expect.objectContaining({ jahr: 2041, version: 2 }),
      expect.objectContaining({ jahr: 2042, version: 1 }),
    ]));
  });

  it("weist ungültige Jahre und unvollständige technische Metadaten zurück", () => {
    expect(() => legeJahrespaketEntwurfAn({ jahr: 0, methodologyVersion: "v12", rulesStamp: "2026-10-05" })).toThrow(/Paketjahr/);
    expect(() => legeJahrespaketEntwurfAn({ jahr: 2043, methodologyVersion: "", rulesStamp: "2026-10-05" })).toThrow(/Methodikversion/);
  });

  it("verhindert doppelte Jahresversionen auch auf Datenbankebene", () => {
    const paket = legeJahrespaketEntwurfAn({ jahr: 2044, methodologyVersion: "v12", rulesStamp: "2043-10-01" });
    expect(() => getDb().prepare(`INSERT INTO jahrespakete (
        id, jahr, version, status, methodology_version, rules_stamp, is_active, created_at
      ) VALUES (?, ?, ?, 'entwurf', ?, ?, 0, ?)`).run(
      crypto.randomUUID(), paket.jahr, paket.version, "v12", "2043-10-01", new Date().toISOString(),
    )).toThrow();
  });

  it("erlaubt keine Aktivierung eines nicht freigegebenen Pakets", () => {
    const paket = legeJahrespaketEntwurfAn({ jahr: 2045, methodologyVersion: "v12", rulesStamp: "2044-10-01" });
    expect(() => getDb().prepare("UPDATE jahrespakete SET is_active = 1 WHERE id = ?").run(paket.id)).toThrow(/freigegeben/);
    expect(listJahrespakete().find((item) => item.id === paket.id)).toMatchObject({ status: "entwurf", is_active: 0 });
  });

  it("lässt bestehende Falldaten beim Anlegen von Paketversionen unverändert", () => {
    const fall = createCase({ title: "Bestehender Testfall", audience: "verein" });
    legeJahrespaketEntwurfAn({ jahr: 2046, methodologyVersion: "v12", rulesStamp: "2045-10-01" });
    expect(getCase(fall.id)).toEqual(fall);
  });
});
```

## Relevante Abhängigkeiten

Aus `package.json`:

```json
{
  "dependencies": {
    "next": "^16.4.0",
    "react": "^19.3.0",
    "react-dom": "^19.3.0"
  },
  "devDependencies": {
    "@types/node": "^26.6.4",
    "typescript": "^6.0.3",
    "vitest": "^5.0.3"
  }
}
```

SQLite wird über das in Node.js enthaltene Modul `node:sqlite` verwendet; es gibt dafür keine zusätzliche npm-Abhängigkeit.

## Ausführungsbefehle

Node.js wurde in der Prüfungsumgebung unter `C:\Program Files\nodejs\node.exe` gefunden, war aber nicht im `PATH`.

In dieser Umgebung wurden ausgeführt:

```powershell
& 'C:\Program Files\nodejs\node.exe' 'node_modules/typescript/bin/tsc' --noEmit
$env:NODE_ENV='test'
& 'C:\Program Files\nodejs\node.exe' 'node_modules/vitest/vitest.mjs' run tests/jahrespakete.test.ts
& 'C:\Program Files\nodejs\node.exe' 'node_modules/vitest/vitest.mjs' run
```

Ergebnisse:

- TypeScript: Exitcode 0.
- Jahrespaket-Testdatei: 1 Datei, 5 Tests bestanden.
- Gesamter Vitest-Bestand: 11 Dateien, 67 Tests bestanden.
- Vitest meldet zusätzlich eine nicht fehlschlagende Vite-Warnung zur künftig geplanten nativen Konfigurationsladung.

Wenn Node.js im lokalen Cursor-Terminal regulär im `PATH` liegt, lauten die entsprechenden Befehle:

```powershell
npx tsc --noEmit
npx vitest run tests/jahrespakete.test.ts
npm test
```

Für den Browser-Abnahmetest nach Start der Anwendung:

```powershell
npm run dev
```

Danach `/admin` öffnen und prüfen:

1. Ohne Paketversion erscheint der ausdrückliche Leerzustand.
2. Ein Paketentwurf ohne Inhaltshash erscheint mit `unvollständig`.
3. Jahr, Version, Status, Methodik, Regelstand und Aktivstatus werden angezeigt.

Ein automatisierter Playwright-Test für diese neue Tabellenzeile ist in diesem kleinen Schritt noch nicht enthalten und wurde daher nicht als bestanden ausgewiesen.
