"""
Open DART corpCode 조회 (step1)
대상 종목의 corp_code를 찾아 corp_codes.json으로 저장한다.
"""
import io
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DART_API_KEY")

TARGETS = ["삼성전자", "SK하이닉스", "NAVER", "카카오", "현대자동차"]

CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
OUTPUT_PATH = Path(__file__).parent / "corp_codes.json"


def fetch_corp_code_zip(api_key: str) -> bytes:
    response = requests.get(CORP_CODE_URL, params={"crtfc_key": api_key})
    response.raise_for_status()
    return response.content


def extract_xml(zip_bytes: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xml_name = zf.namelist()[0]
        return zf.read(xml_name)


def find_targets(xml_bytes: bytes, targets: list[str]) -> dict:
    root = ET.fromstring(xml_bytes)
    found = {}
    for item in root.iter("list"):
        corp_name = item.findtext("corp_name", "").strip()
        if corp_name in targets:
            found[corp_name] = {
                "corp_code": item.findtext("corp_code", "").strip(),
                "stock_code": item.findtext("stock_code", "").strip(),
                "corp_name": corp_name,
            }
    return found


def main():
    if not API_KEY:
        print("DART_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    zip_bytes = fetch_corp_code_zip(API_KEY)

    try:
        xml_bytes = extract_xml(zip_bytes)
    except zipfile.BadZipFile:
        print("응답이 zip 형식이 아닙니다. API 키를 확인하세요. 서버 응답:")
        print(zip_bytes.decode("utf-8", errors="replace"))
        sys.exit(1)

    found = find_targets(xml_bytes, TARGETS)

    missing = [name for name in TARGETS if name not in found]
    if missing:
        print(f"찾지 못한 종목: {missing}")

    for name, info in found.items():
        print(f"{name}: corp_code={info['corp_code']}, stock_code={info['stock_code']}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        import json
        json.dump(found, f, ensure_ascii=False, indent=2)

    print(f"\n{OUTPUT_PATH.name} 저장 완료 ({len(found)}/{len(TARGETS)}개 종목)")


if __name__ == "__main__":
    main()
