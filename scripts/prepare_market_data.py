"""Generates a deterministic mock daily OHLCV CSV for a sample ticker.

Standalone by design (no dependency on backend/app) so it can be run before the backend
is installed. This is NOT a real market data pipeline — it exists to produce the sample
CSV under data/samples/market/ used for local development and demos.

Usage:
    python scripts/prepare_market_data.py --ticker 005930 --name samsung --base-price 78000
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "samples" / "market"


def business_days_ending(end: date, count: int) -> list[date]:
    days: list[date] = []
    cursor = end
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


def generate_rows(ticker: str, base_price: float, trading_days: int) -> list[dict]:
    rng = random.Random(f"stock-lens-{ticker}")
    days = business_days_ending(date(2026, 7, 17), trading_days)

    prev_close = base_price
    prev_volume = rng.randint(4_000_000, 8_000_000)
    rows = []

    for day in days:
        daily_change = rng.uniform(-0.03, 0.03)
        open_price = prev_close
        close_price = round(open_price * (1 + daily_change), -2)
        high_price = round(max(open_price, close_price) * (1 + rng.uniform(0, 0.015)), -2)
        low_price = round(min(open_price, close_price) * (1 - rng.uniform(0, 0.015)), -2)
        volume = rng.randint(3_000_000, 12_000_000)

        rows.append(
            {
                "date": day.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            }
        )

        prev_close = close_price
        prev_volume = volume

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="005930")
    parser.add_argument("--name", default="samsung", help="output filename stem")
    parser.add_argument("--base-price", type=float, default=78000.0)
    parser.add_argument("--trading-days", type=int, default=30)
    args = parser.parse_args()

    rows = generate_rows(args.ticker, args.base_price, args.trading_days)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{args.name}.csv"

    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
