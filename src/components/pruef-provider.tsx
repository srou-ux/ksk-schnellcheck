"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  LEERER_STAND,
  naechsterStatus,
  positionFinden,
  vorschlagPositionen,
  type AssistentVorschlag,
  type ChatNachricht,
  type Dokument,
  type Entscheidung,
  type Position,
  type Pruefstand,
} from "@/lib/pruefstand";

const SPEICHER = "ksk-pruefstand-v1";

interface PruefContext {
  bereit: boolean;
  stand: Pruefstand;
  fokusId: string | null;
  setFokus: (positionId: string | null) => void;
  dokumentAnlegen: (name: string) => Dokument;
  entscheide: (positionId: string, aktion: Entscheidung) => void;
  gespraech: (frage: string, positionId: string | null, vorschlag: AssistentVorschlag & { text: string }) => void;
  position: (positionId: string | null) => Position | null;
}

const Context = createContext<PruefContext | null>(null);

function neueId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

export function PruefProvider({ children }: { children: React.ReactNode }) {
  const [stand, setStand] = useState<Pruefstand>(LEERER_STAND);
  const [fokusId, setFokus] = useState<string | null>(null);
  const [bereit, setBereit] = useState(false);

  useEffect(() => {
    try {
      const roh = window.localStorage.getItem(SPEICHER);
      if (roh) {
        const gelesen = JSON.parse(roh) as { stand?: Pruefstand; fokusId?: string | null };
        if (gelesen.stand?.dokumente && gelesen.stand.audit && gelesen.stand.nachrichten) {
          setStand(gelesen.stand);
        }
        if (gelesen.fokusId) setFokus(gelesen.fokusId);
      }
    } catch {
      window.localStorage.removeItem(SPEICHER);
    }
    setBereit(true);
  }, []);

  useEffect(() => {
    if (!bereit) return;
    window.localStorage.setItem(SPEICHER, JSON.stringify({ stand, fokusId }));
  }, [bereit, stand, fokusId]);

  const wert = useMemo<PruefContext>(() => {
    return {
      bereit,
      stand,
      fokusId,
      setFokus,
      position: (positionId) => positionFinden(stand.dokumente, positionId),
      dokumentAnlegen: (name) => {
        const id = neueId("dok");
        const dokument: Dokument = {
          id,
          name,
          zeit: new Date().toISOString(),
          positionen: vorschlagPositionen(id, name),
        };
        setStand((bisher) => ({ ...bisher, dokumente: [dokument, ...bisher.dokumente] }));
        return dokument;
      },
      entscheide: (positionId, aktion) => {
        const zeit = new Date().toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
        setStand((bisher) => {
          const position = positionFinden(bisher.dokumente, positionId);
          if (!position) return bisher;
          const nach = naechsterStatus(aktion, position.status);
          const text =
            aktion === "uebernehmen"
              ? `${position.text}: übernommen, zählt in die Jahressumme`
              : aktion === "verwerfen"
                ? `${position.text}: verworfen, zählt nicht`
                : `${position.text}: KSK-Auskunft vermerkt, Status bleibt offen`;
          return {
            ...bisher,
            dokumente: bisher.dokumente.map((dokument) => ({
              ...dokument,
              positionen: dokument.positionen.map((eintrag) =>
                eintrag.id === positionId ? { ...eintrag, status: nach } : eintrag,
              ),
            })),
            audit: [
              { id: neueId("audit"), zeit, positionId, aktion, von: position.status, nach, text },
              ...bisher.audit,
            ],
          };
        });
      },
      gespraech: (frage, positionId, vorschlag) => {
        const nutzer: ChatNachricht = {
          id: neueId("msg"),
          rolle: "nutzer",
          text: frage.trim() || "Bitte diese Position einordnen.",
          positionId: positionId ?? undefined,
        };
        const assistent: ChatNachricht = {
          id: neueId("msg"),
          rolle: "assistent",
          text: vorschlag.text,
          positionId: positionId ?? undefined,
          vorschlag,
        };
        setStand((bisher) => ({ ...bisher, nachrichten: [...bisher.nachrichten, nutzer, assistent] }));
      },
    };
  }, [bereit, fokusId, stand]);

  return <Context.Provider value={wert}>{children}</Context.Provider>;
}

export function usePruefstand(): PruefContext {
  const wert = useContext(Context);
  if (!wert) throw new Error("PruefProvider fehlt.");
  return wert;
}
