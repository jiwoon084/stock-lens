export interface Stock {
  ticker: string;
  name: string;
  market: string;
}

export interface PricePoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change_percent: number;
  volume_change_percent: number;
}

export type PriceDirection = "up" | "down" | "flat";

export interface LivePrice {
  price: number;
  change: number;
  change_percent: number;
  direction: PriceDirection;
  open: number;
  high: number;
  low: number;
  volume: number;
}

export interface LivePriceResponse {
  available: boolean;
  as_of: string | null;
  live: LivePrice | null;
}
