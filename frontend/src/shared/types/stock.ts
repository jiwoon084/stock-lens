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
