import { apiRequest } from "./client";
import type { IntradayPoint, LivePriceResponse, PricePoint, Stock } from "../types/stock";

export function fetchStocks(): Promise<Stock[]> {
  return apiRequest<Stock[]>("/api/v1/stocks");
}

export function fetchStockPrices(ticker: string): Promise<PricePoint[]> {
  return apiRequest<PricePoint[]>(`/api/v1/stocks/${ticker}/prices`);
}

export function fetchLivePrice(ticker: string): Promise<LivePriceResponse> {
  return apiRequest<LivePriceResponse>(`/api/v1/stocks/${ticker}/live-price`);
}

export function fetchIntradayPrices(ticker: string): Promise<IntradayPoint[]> {
  return apiRequest<IntradayPoint[]>(`/api/v1/stocks/${ticker}/intraday-prices`);
}
