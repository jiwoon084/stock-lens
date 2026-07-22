# Stock Lens

Stock Lens는 사용자가 주가 차트에서 특정 날짜를 선택하면, 해당 시점 전후의 뉴스·공시·리포트와
가격·거래량 정보를 분석하여 주가 상승·하락 관련 요인을 보여주는 웹 서비스입니다.

초기 단계는 **모노레포 boilerplate**로 시작해 실제 API 응답과 동일한 구조의 Mock 데이터로 핵심
인터랙션(종목 선택 → 차트 확인 → 날짜 클릭 → 분석 결과 확인)을 로컬에서 완성하는 것이 목표였습니다.
현재는 여기서 한 단계 더 나가서, **공시(DART) 쪽은 실제 데이터로 전환**됐습니다 — 시세는 여전히
Mock이지만, 관련 요인·출처는 실제 DART 공시(목록·본문·구조화 필드)를 기반으로 만들어집니다. 자세한
현재 범위는 [현재 구현 범위](#현재-구현-범위)를 참고하세요.

## 핵심 기능

- 샘플 종목(삼성전자, SK하이닉스, NAVER, 카카오, 현대차) 중 선택
- 종목 헤더(현재가·전일 대비)와 Lightweight Charts 기반 캔들스틱 차트, 기간 필터(1주/2주/1개월/전체)
- 차트 포인트 클릭 → 클릭 지점에 바로 뜨는 팝오버("이날 왜 올랐을까?")와 우측 체크리스트에 동시 표시
- 체크리스트: 요인별 체크박스·호재/유의/중립 태그·출처 펼치기, "확인 완료 X/Y" 진행률
- 요인·출처는 **실제 DART 공시** 기반 (선택 날짜와 가까운 공시를 우선순위 규칙으로 선정, 본문 발췌
  또는 구조화 필드 사용) — 단, 호재/유의/중립 판단과 요약 문장 자체는 아직 규칙 기반이며 실제 LLM
  해석은 아님
- 로딩·성공·오류 상태를 모두 갖춘 체크리스트/팝오버

## 기술 스택

| 영역 | 스택 |
|---|---|
| Frontend | React, TypeScript, Vite, Lightweight Charts, 순수 CSS, Nginx(배포), Docker |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn, pytest, Docker |
| Infra | Docker Compose(로컬), GitHub Actions(CI/CD), Artifact Registry, Cloud Run, Secret Manager, Workload Identity Federation |

## 아키텍처 개요

```
Browser → Cloud Run(stock-lens-web, Nginx+SPA) → Cloud Run(stock-lens-api, FastAPI) → DART Open API(실제) / LLM(Mock)
GitHub Actions → Artifact Registry → Cloud Run
```

자세한 다이어그램은 [docs/architecture.md](docs/architecture.md) 참고. 백엔드는
`routes → schemas / services → core/config` 3계층으로 분리되어 있고, `explanation_service.py`가
`market_data_service`(Mock 시세) / `retrieval_service`(실제 DART 공시) / `llm_service`(규칙 기반
요약)를 조합해 응답을 만듭니다. `retrieval_service`는 요청마다 DART `document.xml`/구조화 이벤트
API를 실시간으로 호출하므로, 백엔드가 실행되는 환경에 아웃바운드 인터넷 접근이 필요합니다.

## 폴더 구조

```
stock-lens/
├── README.md, .gitignore, .env.example, compose.yaml
├── requirements.txt          # 향후 실제 연동(LangGraph/SOLAR/pykrx/ChromaDB) 대상 의존성 목록 — 지금은 미사용
├── .github/workflows/        # ci.yml, deploy.yml
├── docs/                     # project-plan, requirements, screen-design, api-spec, architecture, deployment
├── frontend/                 # Vite + React + TS, src/features|shared|mocks|styles
├── backend/                  # FastAPI app/api|core|schemas|services|prompts|agent(LangGraph 스켈레톤), tests/
├── infra/                    # GCP 설정 문서, Cloud Run 환경변수 예시
├── data/                     # step1~3 (실제 DART 연동: corp_code/공시목록/구조화 이벤트), samples/
└── scripts/                  # prepare_market_data.py, ingest_documents.py
```

## 로컬 실행 방법 (Docker 없이)

**Backend**

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

→ http://localhost:8000/docs 에서 API 확인 가능.

**Frontend** (다른 터미널에서)

```bash
cd frontend
npm install
npm run dev
```

→ http://localhost:5173 접속.

## Docker Compose 실행 방법

```bash
docker compose up --build
```

- Frontend (Vite dev server): http://localhost:5173
- Backend: http://localhost:8000
- API 문서: http://localhost:8000/docs

`compose.yaml`은 로컬 개발 편의를 위해 frontend를 `node:20-alpine` 위에서 Vite dev server로
실행합니다 (프로덕션에서는 `frontend/Dockerfile`의 Nginx 멀티스테이지 빌드를 사용).

## 테스트 방법

```bash
cd backend
source .venv/bin/activate
pytest -q
```

프론트엔드 정적 검증:

```bash
cd frontend
npm run lint
npm run build
```

## 환경변수 설정

`.env.example`을 복사해 `.env`로 사용하세요 (`.env`는 git에 커밋되지 않습니다).

```bash
cp .env.example .env
```

주요 변수:

- `VITE_API_BASE_URL` — 프론트엔드가 호출할 백엔드 주소 (로컬 기본값: `http://localhost:8000`)
- `ALLOWED_ORIGINS` — 백엔드 CORS 허용 origin (로컬 기본값: `http://localhost:5173`)
- `UPSTAGE_API_KEY`, `GEMINI_API_KEY` — **둘 다 실제로 사용됨**. `llm_service.py`가 근거 자료
  개수로 SOLAR-pro2(어려운 요청)와 Gemini Flash(쉬운 요청) 중 하나로 **자동 라우팅**합니다 —
  사용자가 모델을 직접 고르지 않습니다. 라우팅된 쪽이 키가 없거나 호출에 실패하면 나머지 하나를
  안전망으로 한 번 더 시도합니다. Gemini 모델명은 `GEMINI_MODEL`(기본 `gemini-flash-latest` —
  Google이 관리하는 "항상 최신 무료 Flash 모델" 별칭. `gemini-2.5-flash`처럼 날짜 박힌 이름은
  신규 키에서 404/유료 전환될 수 있어서 별칭을 기본값으로 씀)로 바꿀 수 있습니다. 둘 다 없거나
  호출이 실패해도 앱이 죽지 않고 결정론적 mock 분석으로 폴백합니다.
- `DART_API_KEY` — **실제로 사용됨**. [Open DART](https://opendart.fss.or.kr)에서 무료로 발급받은 키를 넣으면
  `data/step1_corpcode.py` → `step2_disclosures.py` → `step3_major_events.py` 실행과, 백엔드의
  실시간 공시 본문/구조화 이벤트 조회(`retrieval_service.py`)에 쓰입니다. 키가 없으면 앱이 죽지
  않고 그냥 "관련 공시·뉴스 자료를 찾지 못했습니다"로 정직하게 응답합니다.
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` — **실제로 사용됨**. [Naver Developers](https://developers.naver.com)
  에서 발급받은 키를 넣으면 `data/step5_news.py`가 종목별 실제 뉴스를 `data/news.json`에
  수집합니다. `retrieval_service.py`가 AI 분석 출처(공시+뉴스)로 이 데이터를 씁니다. 키가
  없어도 스크립트만 못 돌리는 것이고 서비스는 mock으로 폴백합니다.
- `KRX_API_KEY` — **실제로 사용됨**. [data.go.kr](https://www.data.go.kr)에서 "금융위원회_주식시세정보"
  API를 활용신청하면 받는 "일반 인증키(Decoding)"를 넣으세요. `market_data_service.py`가 요청마다
  실시간으로 KRX 일별 시세를 가져오는 데 씁니다 (같은 날 반복 요청은 캐시). 키가 없거나 호출이
  실패해도 앱이 죽지 않고 기존 mock 시세로 폴백합니다.
- `GCP_*`, `FRONTEND_SERVICE_NAME`, `BACKEND_SERVICE_NAME` — GCP 배포용 (아래 참고)

## DART 실데이터 준비 (선택)

`DART_API_KEY`를 `.env`에 넣은 뒤, 저장소 루트에서 한 번만 실행하면 됩니다 (재실행 스케줄은 없음 —
스냅샷 방식, MVP 결정):

```bash
source backend/.venv/bin/activate   # requests, python-dotenv 필요
python3 data/step1_corpcode.py      # 5개 샘플 종목의 corp_code 조회 → data/corp_codes.json
python3 data/step2_disclosures.py   # 최근 약 3개월 공시 목록 → data/disclosures.json
python3 data/step3_major_events.py  # 자기주식/유상증자 등 구조화 이벤트 → data/major_events.json
```

`data/*.json`은 git에 커밋되지 않습니다(재생성 가능한 산출물). 이 파일들이 없어도 백엔드는 죽지
않고 "관련 공시를 찾지 못했습니다"로 응답합니다 — Docker에서는 `compose.yaml`이 `./data`를
`/app/data`로 읽기 전용 마운트해서 로컬에서 만든 스냅샷을 그대로 사용합니다.

## GCP 배포 개요

`.github/workflows/deploy.yml`은 Workload Identity Federation으로 GCP에 인증하고, backend/frontend
Docker 이미지를 빌드해 Artifact Registry에 푸시한 뒤 각각 Cloud Run(`stock-lens-api`,
`stock-lens-web`)에 배포합니다.

**⚠️ 이 workflow는 아직 실제 GCP 프로젝트/설정 없이는 실행되지 않습니다.** GCP 프로젝트 준비,
Artifact Registry, Workload Identity Federation, Secret Manager, GitHub Repository Variables
설정이 모두 먼저 필요합니다 — 전체 절차는 [docs/deployment.md](docs/deployment.md)를 참고하세요.

**추가로 확인할 점**: 백엔드가 이제 요청마다 DART로 실시간 아웃바운드 호출을 하므로 Cloud Run
서비스에 인터넷 접근이 필요하고(기본 허용이라 보통 문제 없음), `DART_API_KEY`도 SOLAR/GEMINI와
같은 방식으로 Secret Manager에 등록해서 배포해야 합니다.

## 현재 구현 범위

- **Koyfin/Perplexity 스타일 대시보드 UI**: 상단바 → 종목 선택 + StockHeader(현재가/등락률) →
  캔들/라인 토글 가능한 주가 차트(`ChartTypeToggle`, 클릭 시 선택 정보 표시) → "주목할 만한
  가격변동"(등락률 상위 카드) → 우측 "AI 분석 리포트"(요인 체크리스트 + SOLAR/Gemini 선택
  버튼) + "오늘의 체크리스트"(실제 뉴스 기반, 체크박스/태그/출처 건수/원문 링크/확인 진행률)
- **DART 공시 실데이터**: 5개 종목 실제 공시 목록(`data/disclosures.json`, 1년치) + 실시간 본문
  발췌(`document.xml`, XML/HTML 두 형식 모두 처리) + 구조화 이벤트(자기주식처분결정/유상증자결정)
  까지 연동. 행정성 보고서(임원 소유상황 등)는 후순위 우선순위 규칙으로 처리
- **네이버 뉴스 실데이터**: `data/step5_news.py`로 종목별 실제 기사 수집(`data/news.json`).
  AI 분석 출처와 "오늘의 체크리스트" 둘 다 이 데이터를 사용
- **KRX 실 시세 데이터**: data.go.kr "금융위원회_주식시세정보"로 요청마다 실시간 조회
  (`app/services/krx_price_client.py`, 1년치 250거래일). 키가 없거나 호출이 실패하면 mock
  시세로 자동 폴백 — 자세한 내용은 [docs/project-plan.md](docs/project-plan.md) M1 참고
- **SOLAR/Gemini 실 LLM 연동**: 사용자가 버튼으로 직접 고를 수 있음(기본 SOLAR). 실제 검색된
  공시/뉴스만 근거로 쓰도록 프롬프트가 `[id]` 인용을 강제하고, 인용 안 된 id는 응답 단계에서도
  한 번 더 걸러냄(`llm_service._sanitize_factors`). 키가 없거나 호출 실패 시 실제 자료 기반의
  규칙 기반 분석으로 폴백 — 자세한 내용은 [docs/project-plan.md](docs/project-plan.md) M3 참고
- 프론트엔드-백엔드 API 계약 (snake_case로 통일, 변환 로직 없음)
- 로컬 실행 (venv/npm, Docker Compose, `data/` 볼륨 마운트로 실데이터도 로컬 Docker에서 동작)
- Docker 빌드 (frontend/backend 모두 로컬에서 build 및 실행 검증 완료)
- GitHub Actions CI(lint/build/test/docker build) — 실행 여부는 GitHub 저장소에 push 후 Actions 탭에서 확인 필요
- GitHub Actions CD 뼈대 — 실제 GCP 배포는 미검증 (설정 전이므로 실행 불가)

## 향후 구현 예정 항목

- 나머지 DART 이벤트 유형 구조화 (자기주식취득결정 등 — 지금 5개 종목 데이터엔 해당 사례가 없어 미검증)
- 한경 컨센서스 등 증권사 리서치 리포트 연동
- 이벤트 마커, 분석 결과 캐싱, 모바일 반응형 (`docs/requirements.md`의 Should)
- 종목 비교, 후속 질문, 분석 기록 저장 (`docs/requirements.md`의 Could)
- 실제 GCP 프로젝트에서의 배포 검증
