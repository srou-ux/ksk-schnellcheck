import type { KskCategory, PayerRole, PayeeKind, PositionKind, PositionState } from "./types";

export const CATEGORY_LABEL: Record<KskCategory, string> = {
  wort: "Wort",
  bildende_kunst: "Bildende Kunst",
  musik: "Musik",
  darstellende_kunst: "Darstellende Kunst",
};

export const STATE_LABEL: Record<PositionState, string> = {
  ABGABEPFLICHTIG: "Abgabepflichtig",
  NICHT_ABGABEPFLICHTIG: "Nicht abgabepflichtig",
  UNGEKLÄRT: "Ungeklärt",
};

export const ROLE_LABEL: Record<PayerRole | "UNGEKLÄRT", string> = {
  typischer_verwerter: "Typischer Verwerter",
  eigenwerbung: "Eigenwerbung",
  generalklausel: "Generalklausel",
  UNGEKLÄRT: "Ungeklärt",
};

export const PAYEE_LABEL: Record<PayeeKind | "UNGEKLÄRT", string> = {
  natuerliche_person: "Natürliche Person",
  gesellschaft: "Gesellschaft",
  UNGEKLÄRT: "Ungeklärt",
};

export const KIND_LABEL: Record<PositionKind | "UNGEKLÄRT", string> = {
  honorar: "Honorar",
  material: "Material",
  reise: "Reisekosten",
  bewirtung: "Bewirtung",
  gemischt: "Gemischte Position",
  drittleistung: "Drittleistung",
  umsatzsteuer: "Umsatzsteuer",
  UNGEKLÄRT: "Ungeklärt",
};

export const DEPENDENCY_LABEL = {
  unselbstaendig: "Unselbstständig: der Punkt hängt am Auftrag",
  eigenstaendig: "Eigenständig: der Punkt ist ein eigener Vorgang",
  gemischt: "Gemischt: nur ein belegter Anteil kann ausscheiden",
} as const;
