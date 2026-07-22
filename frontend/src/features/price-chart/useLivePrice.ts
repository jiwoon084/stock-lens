import { useEffect, useState } from "react";

import { fetchLivePrice } from "../../shared/api/stocks";
import type { LivePrice } from "../../shared/types/stock";

const POLL_INTERVAL_MS = 10_000;

interface UseLivePriceResult {
  live: LivePrice | null;
  asOf: string | null;
}

/** Polls `/live-price` for `ticker` every 10s. Silently stays at `live: null` when the KIS
 * key isn't configured or the market's closed for this ticker — there's nothing meaningful to
 * show, so callers should just fall back to the daily close instead of surfacing an error.
 */
export function useLivePrice(ticker: string): UseLivePriceResult {
  const [live, setLive] = useState<LivePrice | null>(null);
  const [asOf, setAsOf] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLive(null);
    setAsOf(null);

    const poll = () => {
      fetchLivePrice(ticker)
        .then((response) => {
          if (cancelled) return;
          setLive(response.available ? response.live : null);
          setAsOf(response.available ? response.as_of : null);
        })
        .catch(() => {
          if (!cancelled) {
            setLive(null);
            setAsOf(null);
          }
        });
    };

    poll();
    const intervalId = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [ticker]);

  return { live, asOf };
}
