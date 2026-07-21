"""
Open DART 주요사항보고서 구조화 정보 (step3)
자기주식취득/처분결정, 유상증자결정처럼 DART가 본문 대신 구조화된 필드(숫자·목적 등)로
따로 제공하는 이벤트를 corp_codes.json의 종목별로 조회해 major_events.json으로 저장한다.

step2_disclosures.py와 마찬가지로 최근 90일(약 3개월) 스냅샷만 받고, 주기적 재실행은 하지 않는다.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DART_API_KEY")

# event_type 이름 -> DART Open API 엔드포인트 (개발가이드 DS005 그룹에서 확인한 실제 엔드포인트)
EVENT_APIS = {
    "자기주식취득결정": "https://opendart.fss.or.kr/api/tsstkAqDecsn.json",
    "자기주식처분결정": "https://opendart.fss.or.kr/api/tsstkDpDecsn.json",
    "유상증자결정": "https://opendart.fss.or.kr/api/piicDecsn.json",
}

DAYS_BACK = 90  # step2_disclosures.py와 동일한 창(약 3개월), MVP 스냅샷

CORP_CODES_PATH = Path(__file__).parent / "corp_codes.json"
OUTPUT_PATH = Path(__file__).parent / "major_events.json"


def load_corp_codes(path: Path = CORP_CODES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_events(api_key: str, url: str, corp_code: str, bgn_de: str, end_de: str) -> list[dict]:
    response = requests.get(
        url,
        params={"crtfc_key": api_key, "corp_code": corp_code, "bgn_de": bgn_de, "end_de": end_de},
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "013":
        return []  # 조회된 데이터 없음
    if data.get("status") != "000":
        raise RuntimeError(f"DART API 오류: {data.get('status')} {data.get('message')}")

    return data.get("list", [])


def main():
    if not API_KEY:
        print("DART_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    try:
        corp_codes = load_corp_codes()
    except FileNotFoundError:
        print("corp_codes.json이 없습니다. step1_corpcode.py를 먼저 실행하세요.")
        sys.exit(1)

    end_de = datetime.now().strftime("%Y%m%d")
    bgn_de = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y%m%d")

    events_by_rcept_no: dict[str, dict] = {}
    for corp_name, info in corp_codes.items():
        for event_type, url in EVENT_APIS.items():
            items = fetch_events(API_KEY, url, info["corp_code"], bgn_de, end_de)
            for item in items:
                events_by_rcept_no[item["rcept_no"]] = {"event_type": event_type, **item}
            print(f"{corp_name} - {event_type}: {len(items)}건")
            time.sleep(0.2)  # 요청 간 최소 대기 (API 과다호출 방지)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(events_by_rcept_no, f, ensure_ascii=False, indent=2)

    print(f"\n{OUTPUT_PATH.name} 저장 완료 (총 {len(events_by_rcept_no)}건)")


if __name__ == "__main__":
    main()
