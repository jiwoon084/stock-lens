import type { PricePoint } from "../../shared/types/stock";

export function selectNotableMovements(prices: PricePoint[], limit = 6): PricePoint[] {
  return [...prices]
    .sort((a, b) => Math.abs(b.change_percent) - Math.abs(a.change_percent))
    .slice(0, limit)
    .sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
}
