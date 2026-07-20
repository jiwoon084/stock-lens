# Stock Lens

Stock Lens는 사용자가 주가 차트에서 특정 날짜를 선택하면, 해당 시점 전후의 뉴스·공시·리포트와
가격·거래량 정보를 분석하여 주가 상승·하락 관련 요인을 보여주는 웹 서비스입니다.

이번 단계는 **모노레포 boilerplate**로, 실제 AI/RAG 대신 실제 API 응답과 동일한 구조의 Mock
데이터로 핵심 인터랙션(종목 선택 → 차트 확인 → 날짜 클릭 → 분석 결과 확인)이 로컬에서 실제로
동작하도록 만드는 것이 목표입니다.

## 핵심 기능

- 샘플 종목(삼성전자, SK하이닉스, NAVER, 카카오, 현대차) 중 선택
- Lightweight Charts 기반 캔들스틱 차트, 기간 필터(1주/2주/1개월/전체)
- 차트 포인트 클릭 → 선택 날짜의 종가·등락률·거래량 변화율 표시
- 선택 날짜에 대한 AI 분석 요청 → 헤드라인/요약/신뢰도/주요 요인/출처/분석 한계 표시
- 로딩·성공·오류 상태를 모두 갖춘 분석 패널 (현재는 Mock 응답)

## 기술 스택

| 영역 | 스택 |
|---|---|
| Frontend | React, TypeScript, Vite, Lightweight Charts, 순수 CSS, Nginx(배포), Docker |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn, pytest, Docker |
| Infra | Docker Compose(로컬), GitHub Actions(CI/CD), Artifact Registry, Cloud Run, Secret Manager, Workload Identity Federation |

## 아키텍처 개요

```
Browser → Cloud Run(stock-lens-web, Nginx+SPA) → Cloud Run(stock-lens-api, FastAPI) → (Mock) LLM / 문서 데이터
GitHub Actions → Artifact Registry → Cloud Run
```

자세한 다이어그램은 [docs/architecture.md](docs/architecture.md) 참고. 백엔드는
`routes → schemas / services → core/config` 3계층으로 분리되어 있고, `explanation_service.py`가
`market_data_service` / `retrieval_service` / `llm_service`를 조합해 응답을 만듭니다.

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
├── data/                     # step1_corpcode.py, step2_disclosures.py(실제 DART 연동), samples/
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
- `SOLAR_API_KEY`, `GEMINI_API_KEY`, `LLM_PROVIDER=mock` — 현재는 사용되지 않는 자리 표시자 (실제 키를 채우거나 커밋하지 마세요)
- `GCP_*`, `FRONTEND_SERVICE_NAME`, `BACKEND_SERVICE_NAME` — GCP 배포용 (아래 참고)

## GCP 배포 개요

`.github/workflows/deploy.yml`은 Workload Identity Federation으로 GCP에 인증하고, backend/frontend
Docker 이미지를 빌드해 Artifact Registry에 푸시한 뒤 각각 Cloud Run(`stock-lens-api`,
`stock-lens-web`)에 배포합니다.

**⚠️ 이 workflow는 아직 실제 GCP 프로젝트/설정 없이는 실행되지 않습니다.** GCP 프로젝트 준비,
Artifact Registry, Workload Identity Federation, Secret Manager, GitHub Repository Variables
설정이 모두 먼저 필요합니다 — 전체 절차는 [docs/deployment.md](docs/deployment.md)를 참고하세요.

## 현재 구현 범위

- 종목 선택, 차트 표시, 포인트 선택, 선택 날짜 정보, AI 분석 요청/표시(Mock), 출처/한계 표시
- 프론트엔드-백엔드 API 계약 (snake_case로 통일, 변환 로직 없음)
- 로컬 실행 (venv/npm, Docker Compose)
- Docker 빌드 (frontend/backend 모두 로컬에서 build 및 실행 검증 완료)
- GitHub Actions CI(lint/build/test/docker build) — 실행 여부는 GitHub 저장소에 push 후 Actions 탭에서 확인 필요
- GitHub Actions CD 뼈대 — 실제 GCP 배포는 미검증 (설정 전이므로 실행 불가)

## 향후 구현 예정 항목

- 실제 시세 데이터 연동 (`market_data_service.py` 교체 — `pykrx` 사용 예정, 루트 `requirements.txt` 참고)
- 실제 공시 데이터 수집 (`data/step1_corpcode.py` → `data/step2_disclosures.py`는 이미 동작하는 DART 연동 스크립트; `DART_API_KEY` 필요, 아직 백엔드에는 연결 안 됨)
- 실제 뉴스/공시/리포트 검색(RAG) 연동 (`retrieval_service.py` 교체 — `chromadb` 사용 예정)
- SOLAR/Gemini 실제 LLM 호출 연동 (`llm_service.py` 교체, `app/prompts/explain_movement.txt` + `backend/app/agent/`의 LangGraph 스켈레톤 참고)
- 이벤트 마커, 분석 결과 캐싱, 모바일 반응형 (`docs/requirements.md`의 Should)
- 종목 비교, 후속 질문, 분석 기록 저장 (`docs/requirements.md`의 Could)
- 실제 GCP 프로젝트에서의 배포 검증
