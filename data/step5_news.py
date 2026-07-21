"""
네이버 뉴스 검색 API (step5)
종목별로 최근 뉴스(제목·요약·링크·날짜)를 조회해 news.json으로 저장한다.
"""
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NEWS_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"
DISPLAY_COUNT = 20  # 종목당 조회 건수

# stock.py의 SAMPLE_STOCKS와 동일한 5종목 (뉴스 검색에는 통용되는 약칭을 씀: 현대차 등)
TARGETS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "005380": "현대차",
}

OUTPUT_PATH = Path(__file__).parent / "news.json"

_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return html.unescape(_TAG_STRIP_RE.sub("", text)).strip()


def fetch_news(client_id: str, client_secret: str, query: str) -> list[dict]:
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    params = {"query": query, "display": DISPLAY_COUNT, "sort": "date"}
    response = requests.get(NEWS_SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])

    return [
        {
            "title": _clean(item["title"]),
            "description": _clean(item["description"]),
            "link": item.get("originallink") or item["link"],
            "pub_date": item["pubDate"],
        }
        for item in items
    ]


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    all_news: dict[str, list[dict]] = {}
    for ticker, name in TARGETS.items():
        articles = fetch_news(CLIENT_ID, CLIENT_SECRET, name)
        all_news[ticker] = articles
        print(f"{name}({ticker}): {len(articles)}건")
        time.sleep(0.2)  # 요청 간 최소 대기

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in all_news.values())
    print(f"\n{OUTPUT_PATH.name} 저장 완료 (총 {total}건)")


if __name__ == "__main__":
    main()
