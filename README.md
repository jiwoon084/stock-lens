# Stock Lens

Stock Lens는 사용자가 주가 차트에서 특정 날짜를 클릭하면, 그 시점 전후의 실제 공시·뉴스를
검색해 주가 변동 요인을 근거와 함께 설명해주는 초보 투자자용 AI 투자 어시스턴트입니다.
"추천"이 아니라 "설명·요약"으로 역할을 한정합니다(투자자문 리스크 회피).

**실제 배포**: http://34.64.152.73 (GCE VM, main 브랜치 push마다 자동 배포)

시세(KRX 공식 API + 한국투자증권 KIS 실시간)·공시(Open DART)·뉴스(네이버 뉴스 API)·LLM
(Upstage SOLAR·Google Gemini)까지 전부 실제 API로 연동되어 있고, 데이터베이스 없이 로컬 JSON
스냅샷 + 요청 시점 실시간 호출 조합으로 동작합니다(아래 [데이터 저장 방식](#데이터-저장-방식)
참고).

## 핵심 기능

- 샘플 종목(삼성전자, SK하이닉스, NAVER, 카카오, 현대차) 중 선택
- 종목 헤더(현재가·전일 대비, KIS 실시간 배지) + Lightweight Charts 캔들/라인 차트, 기간 필터
  (오늘/1주/2주/1개월/전체) — "오늘" 탭은 KIS 분봉 기반 실시간 뷰
- 차트에서 날짜(또는 "오늘" 탭에서 분봉)를 클릭하면 3곳에 결과가 나뉘어 표시됨:
  1. 클릭 지점 옆에 뜨는 팝오버 — "이날 왜 올랐/내렸나요?" (공시·뉴스 근거 + 실제 등락 방향과의
     일치 여부 명시, `POST /api/analysis/date`)
  2. 차트 카드 하단 요약 카드 — 선택 날짜/등락률/AI 한줄 요약/핵심 수치/근거 배지
  3. 우측 "오늘의 체크리스트" 패널 — 앞으로 지켜볼 신호(체크박스) + 근거 원문 자료(DART/뉴스
     원문 링크) + 주의 문구
- 별도로 "주목할 만한 가격변동"(등락률 상위 카드) 아래 "관련 자료" 목록 + SOLAR/Gemini 사용자
  선택 버튼(`LlmProviderToggle`) — 더 예전에 만든 `POST /api/v1/explanations` 기반 기능으로,
  위 3곳과는 완전히 분리된 별도 백엔드 호출(같은 클릭 한 번으로 함께 트리거됨)
- 어려운 공시·재무 용어는 클릭 한 번으로 쉬운 설명 팝업(정적 사전, 20개 용어)
- 차트 클릭 가능성을 알려주는 첫 방문 온보딩 힌트 + 마우스 추적 호버 툴팁
- 요인·출처는 **실제 DART 공시 + 네이버 뉴스** 기반(날짜 근접도 + SOLAR 임베딩 의미 유사도
  하이브리드 랭킹), 요약·해석은 **실제 SOLAR/Gemini LLM 호출** 결과(키가 없거나 실패하면 규칙
  기반으로 폴백)
- 로딩·성공·오류·빈 자료 상태를 모두 갖춘 팝오버/요약 카드/체크리스트, 레이트 리밋(IP당 분당
  10회) 초과 시 안내

## 기술 스택

| 영역 | 스택 |
|---|---|
| Frontend | React, TypeScript, Vite, Lightweight Charts, Pretendard(디자인 토큰 시스템), Nginx(배포), Docker |
| Backend | Python 3.12, FastAPI, Pydantic, LangGraph, Uvicorn, pytest, Docker |
| LLM / 검색 | Upstage SOLAR(solar-pro2, solar-embedding-1-large), Google Gemini(gemini-flash-latest) |
| 데이터 | Open DART(공시), data.go.kr KRX(일봉), 한국투자증권 KIS(실시간·분봉·일봉 gap-fill), 네이버 뉴스 API |
| Infra | Docker Compose(로컬), GitHub Actions(CI/CD + 매일 데이터 자동 갱신), GHCR, GCE(VM 재사용, Cloud Run 아님) |
| MCP | `backend/mcp_server.py` — Stock Lens 분석 기능을 외부 MCP 클라이언트에 도구로 노출(stdio) |

## 아키텍처 개요

```
사용자 UI (React SPA)
  → nginx (GCE VM, 포트 80만 외부 공개)
    → /api/ 프록시 (compose 내부망) → FastAPI (backend, 외부 비공개 127.0.0.1:8001)
      → routes: stocks / explanations / analysis
        → Orchestrator (app/agent/orchestrator.py)
          → Agent (LangGraph 4-노드: fetch_market_data → retrieve_evidence →
                    build_llm_input → generate_analysis)
            → Gateway (app/gateway/data_gateway.py) → KRX · KIS · DART · 네이버뉴스 · SOLAR 임베딩
            → LLM Gateway (app/services/llm/base.py + factory.py)
              → 난이도 기반 라우팅: SOLAR Pro(다중 근거 종합) / Gemini Flash(단순 사실 나열)

GitHub Actions → GHCR(이미지) → GCE VM SSH pull & 재기동 (main push마다 자동)
GitHub Actions (매일 06:00 KST) → 공시/뉴스 재수집 → GCE VM으로 전송 → 백엔드 재시작
```

- **Agent / Gateway / Orchestrator**: `app/agent/`(LangGraph 파이프라인)가 Agent, 외부 데이터
  호출을 감싸는 `app/gateway/data_gateway.py`(+ LLM 쪽은 `app/services/llm/`)가 Gateway,
  Agent 실행을 감싸는 `app/agent/orchestrator.py`가 Orchestrator입니다.
- **가드레일**: LLM 출력은 백엔드가 미리 만든 후보(quick facts·watch items) 중에서만 고르도록
  강제 — 벗어나면 재검증 단계(`_sanitize_result`)에서 제거. 호출 실패 시 재시도 후 결정론적
  규칙 기반 응답으로 폴백 — 하드 실패 없음.
- **`POST /api/v1/explanations`**는 위 파이프라인과 별개입니다 — 사용자가 SOLAR/Gemini를
  직접 고르는 토글 방식(`llm_service.py`)이며, "관련 자료" 목록에 쓰입니다. 두 기능은 스키마·
  프롬프트·엔드포인트가 전부 분리되어 있고 서로 섞이지 않습니다.

## 데이터 저장 방식

**데이터베이스를 쓰지 않습니다.** 이 프로젝트 규모(종목 5개, 공시 1,300여 건)에서는 벡터 DB
같은 인프라를 새로 들이는 게 얻는 것보다 운영 부담이 커서 채택하지 않았습니다.

- 공시·뉴스·종목 코드는 1회성/일일 수집 스크립트(`data/step1~3.py`, `step5_news.py`)가 만든
  `data/*.json` 스냅샷을 백엔드가 읽기 전용으로 서빙합니다. `.github/workflows/refresh-data.yml`
  이 매일 06:00 KST에 이 스크립트들을 다시 실행해 최신화하고, 배포된 GCE VM으로 결과를 전송한
  뒤 백엔드를 재시작합니다(파일이 `@lru_cache`로 캐시되어 재시작 전까지는 새 파일을 안 읽어서
  재시작까지 자동으로 포함됨).
- 시세(KRX/KIS)는 저장 없이 **매 요청 실시간 API 호출**(당일/초단위 짧은 인메모리 캐시만 존재).
- SOLAR 임베딩 결과만 `cache/embeddings.json`에 디스크 캐싱합니다 — 벡터 검색 자체가 아니라
  "같은 텍스트를 재배포/재시작마다 다시 임베딩하는 비용"만 없애기 위한 것으로, 브루트포스
  코사인 유사도 계산은 이 데이터 규모에서 LLM 호출(4~15초)에 비해 무시할 수준입니다.

## 폴더 구조

```
stock-lens/
├── README.md, CLAUDE.md, .gitignore, .env.example, compose.yaml
├── .github/workflows/        ci.yml, deploy.yml, refresh-data.yml
├── docs/                     project-plan, requirements, screen-design, api-spec, architecture, deployment
├── frontend/                 Vite + React + TS, src/features|shared|components|styles
├── backend/
│   ├── app/
│   │   ├── agent/            LangGraph 파이프라인(Agent) — state.py/nodes.py/graph.py/orchestrator.py
│   │   ├── gateway/           외부 데이터 호출 창구(Gateway) — data_gateway.py
│   │   ├── api/routes/        stocks·explanations·analysis·health
│   │   ├── services/          market_data_service·retrieval_service·llm_service·llm/(SOLAR·Gemini)
│   │   ├── rules/              watch_item_templates.py
│   │   └── core/                config.py, rate_limit.py
│   ├── mcp_server.py          MCP 서버(별도 진입점·별도 venv)
│   ├── requirements.txt, requirements-mcp.txt
│   └── tests/
├── infra/gce/                 GCE 배포용 docker-compose.yml, .env.example
├── data/                      step1~3(DART)·step5(네이버뉴스) 수집 스크립트, samples/
└── cache/                     임베딩 캐시(gitignore, 자동 생성)
```

## 로컬 실행 방법 (Docker 없이)

**Backend**

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

로컬 기본값은 `ENABLE_API_DOCS=true`라 http://localhost:8000/docs 에서 API 확인 가능(배포
환경은 보안상 비활성화되어 있음 — [환경변수 설정](#환경변수-설정) 참고).

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
실행합니다(프로덕션에서는 `frontend/Dockerfile`의 Nginx 멀티스테이지 빌드 + `/api/` 프록시를
사용 — [GCE 배포](#gce-배포) 참고).

## 테스트 방법

```bash
cd backend
source .venv/bin/activate
pytest -q
```

105개 통과 + 1개 스킵(`test_mcp_server.py` — `mcp` 패키지가 메인 venv엔 없어서 정상적으로
스킵됨, 아래 [MCP 서버](#mcp-서버-선택) 참고).

프론트엔드 정적 검증:

```bash
cd frontend
npm run lint
npm run build
```

## MCP 서버 (선택)

`backend/mcp_server.py`는 Stock Lens의 분석 기능(`analyze_stock_movement`,
`search_disclosures_and_news`, `get_price_series`)을 MCP(Model Context Protocol) 도구로 노출해,
Claude Desktop 등 외부 MCP 클라이언트가 직접 호출할 수 있게 합니다. 웹 앱과 완전히 분리된
별도 진입점이며, main 앱(`app.main:app`)에는 영향을 주지 않습니다.

`mcp` SDK의 의존성(starlette 등 최신 버전 요구)이 FastAPI 0.115.0의 고정 버전과 충돌해서,
반드시 별도 가상환경(`backend/.venv-mcp`)에 설치해야 합니다 — `backend/.venv`에는 설치하지
마세요.

```bash
cd backend
python -m venv .venv-mcp
.venv-mcp/Scripts/python.exe -m pip install -r requirements-mcp.txt   # Windows
# source .venv-mcp/bin/activate && pip install -r requirements-mcp.txt   # macOS/Linux

.venv-mcp/Scripts/python.exe mcp_server.py
```

Claude Desktop에 연결하려면 `claude_desktop_config.json`의 `mcpServers`에 위 명령(`command`/
`args`/`cwd`)을 등록하면 됩니다.

## 환경변수 설정

`.env.example`을 복사해 `.env`로 사용하세요 (`.env`는 git에 커밋되지 않습니다).

```bash
cp .env.example .env
```

주요 변수:

- `VITE_API_BASE_URL` — 프론트엔드가 호출할 백엔드 주소(로컬 기본값 `http://localhost:8000`).
  배포 빌드에서는 빈 값(상대 경로)으로 둬서 nginx가 같은 origin의 `/api/`를 백엔드로 프록시함.
- `ALLOWED_ORIGINS` — 백엔드 CORS 허용 origin(로컬 기본값 `http://localhost:5173`)
- `ENABLE_API_DOCS` — Swagger/ReDoc/OpenAPI 노출 여부(로컬 기본 `true`, 배포는 `false` — 무인증
  API라 스키마를 공개 노출하지 않음)
- `SOLAR_API_KEY`, `GEMINI_API_KEY` — 둘 다 실제로 사용됨, 두 군데에서 **서로 다른 정책**으로:
  - `POST /api/v1/explanations`: 사용자가 `LlmProviderToggle`로 직접 선택(기본 SOLAR), 자동
    라우팅 없음. 고른 provider의 키가 없거나 실패하면 규칙 기반으로만 폴백(CLAUDE.md 9번).
  - `POST /api/analysis/date`: **난이도 기반 자동 라우팅** — intraday거나 근거 1건 이하는
    Gemini Flash, 근거 2건 이상 비-intraday는 SOLAR Pro(CLAUDE.md 17번).
  - Gemini는 `GEMINI_MODEL`(기본 `gemini-flash-latest` — Google이 관리하는 "항상 최신 무료
    Flash 모델" 별칭)로 모델을 바꿀 수 있음.
- `DART_API_KEY` — [Open DART](https://opendart.fss.or.kr)에서 발급. 공시 목록/본문 실시간 조회에 사용.
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` — [Naver Developers](https://developers.naver.com)에서 발급.
  `data/step5_news.py`가 뉴스를 수집하는 데 사용(매일 자동 갱신).
- `KRX_API_KEY` — [data.go.kr](https://www.data.go.kr) "금융위원회_주식시세정보"의 "일반
  인증키(Decoding)". 일봉 시세 조회에 사용, 최근 1~2일 결제 지연(T+2)은 KIS로 보완.
- `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` — [KIS Developers](https://apiportal.koreainvestment.com)
  모의투자 계좌 키. 실시간 현재가/분봉/일봉 gap-fill에 사용.
- `GCE_HOST`, `GCE_USERNAME`, `GCE_SSH_KEY` — GitHub Actions 배포용(GitHub 리포지토리 Secrets로
  등록, `.env`에는 참고용 placeholder만) — [infra/gcp-setup.md](infra/gcp-setup.md) 참고.

모든 외부 API 키는 없거나 호출이 실패해도 앱이 죽지 않고 mock/규칙 기반으로 정직하게
폴백합니다.

## 데이터 갱신

공시·뉴스는 `.github/workflows/refresh-data.yml`이 **매일 06:00 KST에 자동으로** 재수집해
배포된 GCE VM에 반영합니다(`workflow_dispatch`로 수동 실행도 가능). 로컬에서 직접 갱신하려면:

```bash
source backend/.venv/bin/activate   # requests, python-dotenv 필요
python3 data/step1_corpcode.py      # 5개 샘플 종목의 corp_code 조회 → data/corp_codes.json
python3 data/step2_disclosures.py   # 최근 1년 공시 목록 → data/disclosures.json
python3 data/step5_news.py          # 종목별 실제 뉴스 → data/news.json
```

`data/*.json`은 git에 커밋되지 않습니다(재생성 가능한 산출물). 이 파일들이 없어도 백엔드는
죽지 않고 mock 데이터로 폴백합니다.

## GCE 배포

`.github/workflows/deploy.yml`이 main 브랜치 push마다 자동으로: Docker 이미지 빌드 → GHCR
push → GCE VM에 SSH로 `docker compose pull && up -d` → 헬스체크까지 실행합니다. Cloud Run이
아니라 **GCE VM**(다른 과목 프로젝트와 공유, 재사용) 위에서 Docker Compose로 두 컨테이너를
띄우는 방식입니다. GCP 프로젝트/Workload Identity Federation 설정이 필요 없습니다 — 필요한
건 GitHub Secrets 3개(`GCE_HOST`/`GCE_USERNAME`/`GCE_SSH_KEY`)뿐입니다.

방화벽은 포트 80만 외부에 열려 있어서, 백엔드는 외부에 직접 노출되지 않고 nginx가
`/api/`를 컨테이너 내부망으로 프록시합니다. 최초 VM 설정 절차는
[infra/gcp-setup.md](infra/gcp-setup.md), 전체 설계 이유는 [docs/deployment.md](docs/deployment.md)를
참고하세요.

## 현재 구현 범위

- **대시보드 UI**: 상단바(로고) → 종목 선택 + StockHeader(현재가·등락률, KIS 실시간 배지) →
  캔들/라인 토글 차트(오늘/1주/2주/1개월/전체, "오늘"은 분봉) + 클릭 시 팝오버/요약 카드 →
  "주목할 만한 가격변동" + 관련 자료 → 우측 "오늘의 체크리스트". 용어 하이라이트, 온보딩 힌트/
  호버 툴팁, Pretendard 기반 디자인 토큰 시스템 포함.
- **실시간 시세**: KRX 공식 API(일봉, 결제 지연 T+2) + KIS(실시간 현재가/분봉/일봉 gap-fill)
  병합. 키 없거나 실패 시 mock 폴백.
- **실검색**: Open DART 공시(1년치, 본문 실시간 발췌) + 네이버 뉴스 — 날짜 근접도 + SOLAR
  임베딩 의미 유사도 하이브리드 랭킹, 루틴성 공시 후순위. 매일 자동 갱신.
- **LangGraph Agent + Gateway + Orchestrator**: `app/agent/`(4-노드 파이프라인) + 
  `app/gateway/data_gateway.py`(외부 데이터 호출 단일 창구) + `app/agent/orchestrator.py`
  (실행 진입점 하나) 구조로 재구성 완료.
- **LLMOps — 난이도 기반 SOLAR/Gemini 라우팅**: `POST /api/analysis/date`는 근거 복잡도에 따라
  자동으로 SOLAR Pro/Gemini Flash를 선택(둘 다 실제 연동), 호출마다 provider·레이턴시 로깅.
  `POST /api/v1/explanations`는 별개로 사용자가 직접 SOLAR/Gemini를 고르는 토글 방식 유지.
- **임베딩 캐시 디스크 영속화**: SOLAR 임베딩 결과를 `cache/`에 저장해 재배포·재시작에도
  재계산하지 않음.
- **MCP 서버**: `backend/mcp_server.py`, 도구 3개, 별도 venv/진입점으로 웹 앱과 분리.
- **보안 하드닝**: IP당 분당 10회 레이트 리밋, 배포 환경 API 문서 비공개, CORS credentials off.
- **CI/CD**: GitHub Actions로 lint/build/test(CI)와 GHCR 빌드→GCE 배포(CD)가 push마다 자동
  실행, 공시/뉴스 매일 자동 갱신(Refresh Data 워크플로).
- 백엔드 테스트 105개 통과(+ MCP 테스트 1개는 별도 venv에서만 실행).

## 향후 구현 예정 항목

- Gemini provider를 `/api/v1/explanations`뿐 아니라 `/api/analysis/date`에서도 이미 실 연동
  완료 — 남은 건 이 엔드포인트에 사용자 선택 토글 추가 여부 결정
- `market_comparison_text`용 KOSPI 지수 데이터 소스 확보(시장 대비 비교)
- WebSocket 기반 진짜 실시간 체결가(Phase 2 — 현재는 10초 폴링)
- 이벤트 마커, 분석 결과 캐싱(임베딩 캐싱은 완료, 최종 분석 결과 자체 캐싱은 미착수), 모바일
  반응형 고도화(`docs/requirements.md`의 Should)
- 종목 비교, 후속 질문, 분석 기록 저장(`docs/requirements.md`의 Could)
- 나머지 DART 이벤트 유형 구조화(자기주식취득결정 등 — 지금 5개 종목 데이터엔 해당 사례가 없어 미검증)
