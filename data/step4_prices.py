"""
pykrx 일봉 시세 수집 (step4)

샘플 종목의 최근 1년치 일봉(OHLCV)을 SQLite(market_data.sqlite3)에 저장한다. FastAPI는
이 파일만 읽고 pykrx/KRX/네이버 금융을 직접 호출하지 않는다 — pykrx는 비공식 스크래핑이라
요청마다 호출하면 서비스 안정성에 영향을 줄 수 있어, 수집은 이 스크립트로 분리하고
백엔드는 사전에 구축된 데이터만 조회한다.

실행: backend/.venv/Scripts/python.exe data/step4_prices.py  (pykrx가 backend venv에 설치돼 있음)
매일 또는 필요할 때 수동으로 재실행해서 최신 데이터로 갱신한다 (INSERT OR REPLACE라 재실행해도 안전).
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from pykrx import stock as pykrx_stock

LOOKBACK_DAYS = 365  # backend의 _LOOKBACK_DAYS와 동일하게 유지
FETCH_BUFFER_DAYS = 10

# market_data_service.SAMPLE_STOCKS와 동일한 5종목
TARGETS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "005380": "현대차",
}

DB_PATH = Path(__file__).parent / "market_data.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    PRIMARY KEY (ticker, date)
);
"""


def fetch_ohlcv_rows(ticker: str, as_of: date) -> list[tuple]:
    start = as_of - timedelta(days=LOOKBACK_DAYS + FETCH_BUFFER_DAYS)
    df = pykrx_stock.get_market_ohlcv(start.strftime("%Y%m%d"), as_of.strftime("%Y%m%d"), ticker)
    df.columns = ["open", "high", "low", "close", "volume", "change_percent"]

    return [
        (
            ticker,
            index.strftime("%Y-%m-%d"),
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            int(row.volume),
        )
        for index, row in df.iterrows()
    ]


def main():
    as_of = date.today()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)

    total = 0
    for ticker, name in TARGETS.items():
        rows = fetch_ohlcv_rows(ticker, as_of)
        conn.executemany(
            """
            INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        total += len(rows)
        print(f"{name}({ticker}): {len(rows)}건 저장")

    conn.close()
    print(f"\n{DB_PATH.name} 저장 완료 (총 {total}건)")


if __name__ == "__main__":
    main()
