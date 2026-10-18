/** Kaufmännisches Runden auf ganze Cent. Eingaben bleiben Ganzzahlen. */
export function levyCents(basisCents: number, rateBps: number): number {
  if (!Number.isSafeInteger(basisCents) || !Number.isSafeInteger(rateBps)) {
    throw new Error("Abgabe nur aus sicheren Ganzzahlen.");
  }
  if (basisCents < 0 || rateBps < 0) {
    throw new Error("Negative Bemessungsgrundlage oder negativer Satz.");
  }
  const product = basisCents * rateBps;
  if (!Number.isSafeInteger(product)) {
    throw new Error("Der Betrag ist zu groß für eine genaue Cent-Rechnung.");
  }
  return Math.floor((product + 5000) / 10000);
}

export function formatEuro(cents: number | null | undefined): string {
  if (cents === null || cents === undefined) return "Ungeklärt";
  const sign = cents < 0 ? "−" : "";
  const abs = Math.abs(cents);
  const euros = Math.floor(abs / 100);
  const rest = abs % 100;
  const grouped = euros.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped},${rest.toString().padStart(2, "0")} €`;
}

export function formatPercentFromBps(rateBps: number): string {
  const whole = Math.floor(rateBps / 100);
  const frac = rateBps % 100;
  if (frac === 0) return `${whole},0 %`;
  return `${whole},${frac.toString().padStart(2, "0").replace(/0$/, "")} %`;
}

export function isFilingSeason(date: Date): boolean {
  const month = date.getMonth() + 1;
  return month >= 1 && month <= 3;
}
