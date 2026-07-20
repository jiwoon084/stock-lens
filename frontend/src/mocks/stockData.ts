import type { PricePoint, Stock } from "../shared/types/stock";

export const MOCK_STOCKS: Stock[] = [
  { ticker: "005930", name: "삼성전자", market: "KOSPI" },
  { ticker: "000660", name: "SK하이닉스", market: "KOSPI" },
  { ticker: "035420", name: "NAVER", market: "KOSPI" },
  { ticker: "035720", name: "카카오", market: "KOSPI" },
  { ticker: "005380", name: "현대차", market: "KOSPI" },
];

const TRADING_DAYS = 25;
const LATEST_TRADING_DAY = new Date("2026-07-17T00:00:00+09:00");

function businessDaysEnding(end: Date, count: number): Date[] {
  const days: Date[] = [];
  const cursor = new Date(end);
  while (days.length < count) {
    if (cursor.getDay() !== 0 && cursor.getDay() !== 6) {
      days.push(new Date(cursor));
    }
    cursor.setDate(cursor.getDate() - 1);
  }
  return days.reverse();
}

function seededRandom(seed: string) {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return () => {
    hash = (hash * 1103515245 + 12345) & 0x7fffffff;
    return hash / 0x7fffffff;
  };
}

/** Generates a Samsung-Electronics-style mock price series for local UI development before the API responds. */
export function generateMockPrices(ticker: string, basePrice = 78000): PricePoint[] {
  const rng = seededRandom(`stock-lens-${ticker}`);
  const days = businessDaysEnding(LATEST_TRADING_DAY, TRADING_DAYS);

  let prevClose = basePrice;
  let prevVolume = 5_000_000;
  const points: PricePoint[] = [];

  for (const day of days) {
    const dailyChange = (rng() - 0.5) * 0.06;
    const open = prevClose;
    const close = Math.round((open * (1 + dailyChange)) / 100) * 100;
    const high = Math.round((Math.max(open, close) * (1 + rng() * 0.015)) / 100) * 100;
    const low = Math.round((Math.min(open, close) * (1 - rng() * 0.015)) / 100) * 100;
    const volume = Math.round(3_000_000 + rng() * 9_000_000);

    const changePercent = Number((((close - prevClose) / prevClose) * 100).toFixed(2));
    const volumeChangePercent = Number((((volume - prevVolume) / prevVolume) * 100).toFixed(2));

    points.push({
      time: day.toISOString().slice(0, 10),
      open,
      high,
      low,
      close,
      volume,
      change_percent: changePercent,
      volume_change_percent: volumeChangePercent,
    });

    prevClose = close;
    prevVolume = volume;
  }

  return points;
}

export const MOCK_PRICES: PricePoint[] = generateMockPrices("005930");
