"""
Open DART 공시검색 (step2)
corp_codes.json의 종목별로 최근 공시 목록(제목·날짜·접수번호)을 조회해 disclosures.json으로 저장한다.
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

DISCLOSURE_LIST_URL = "https://opendart.fss.or.kr/api/list.json"

DAYS_BACK = 90  # 조회 기간(일)
PAGE_COUNT = 100  # 페이지당 최대 100건

CORP_CODES_PATH = Path(__file__).parent / "corp_codes.json"
OUTPUT_PATH = Path(__file__).parent / "disclosures.json"


def load_corp_codes(path: Path = CORP_CODES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_disclosures(api_key: str, corp_code: str, bgn_de: str, end_de: str) -> list[dict]:
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bgn_de": bgn_de,
        "end_de": end_de,
        "page_no": 1,
        "page_count": PAGE_COUNT,
    }
    response = requests.get(DISCLOSURE_LIST_URL, params=params)
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

    all_disclosures = {}
    for corp_name, info in corp_codes.items():
        disclosures = fetch_disclosures(API_KEY, info["corp_code"], bgn_de, end_de)
        all_disclosures[corp_name] = disclosures
        print(f"{corp_name}: {len(disclosures)}건 ({bgn_de}~{end_de})")
        time.sleep(0.2)  # 요청 간 최소 대기 (API 과다호출 방지)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_disclosures, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in all_disclosures.values())
    print(f"\n{OUTPUT_PATH.name} 저장 완료 (총 {total}건)")


if __name__ == "__main__":
    main()
