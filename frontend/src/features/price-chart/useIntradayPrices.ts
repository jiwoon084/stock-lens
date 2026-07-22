import { useEffect, useState } from "react";

import { fetchIntradayPrices } from "../../shared/api/stocks";
import type { IntradayPoint } from "../../shared/types/stock";

const POLL_INTERVAL_MS = 20_000;

/** Polls today's minute-bar prices for `ticker` every 20s. Empty array (not mock data) when
 * KIS isn't configured or the call fails — PriceChart just renders the daily series alone then.
 */
export function useIntradayPrices(ticker: string): IntradayPoint[] {
  const [points, setPoints] = useState<IntradayPoint[]>([]);

  useEffect(() => {
    let cancelled = false;
    setPoints([]);

    const poll = () => {
      fetchIntradayPrices(ticker)
        .then((data) => {
          if (!cancelled) setPoints(data);
        })
        .catch(() => {
          if (!cancelled) setPoints([]);
        });
    };

    poll();
    const intervalId = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [ticker]);

  return points;
}
