import { LibraryPanel } from "./library-panel";
import { WertePanel } from "./werte-panel";
import { JahrespaketePanel } from "./jahrespakete-panel";
import { JahrespaketVorbereitungPanel } from "./jahrespaket-vorbereitung-panel";

export const dynamic = "force-dynamic";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <p className="rounded-md bg-amber-50 px-4 py-3 text-sm font-semibold text-unclear">Testmodus — nicht produktiv</p>
      <JahrespaketVorbereitungPanel />
      <JahrespaketePanel />
      <LibraryPanel />
      <WertePanel />
    </div>
  );
}
