# Stock Lens (증권 AI 투자 어시스턴트) — 세션 인계 문서

> 이 파일은 이전 Claude Code 세션(프로젝트가 OneDrive 경로에 있을 때)에서 나눈 대화 내용을
> 새 세션이 이어받을 수 있도록 정리한 것입니다. 폴더를 이 위치(`C:\Users\jiwoo\Downloads\AI investment assistant`)로
> 옮기면서 대화 히스토리 자체는 승계되지 않기 때문에 작성했습니다.

## 1. 프로젝트 정체성

- **가천 AI 부트캠프 26-여름 현장미러형 프로젝트 11번** — 증권 AI 투자 어시스턴트
- 참여 기업: **카카오** / 멘토: **박재성** / 팀명: **10조** / 팀원: **권지운, 정영준**
- GitHub 저장소: **https://github.com/jiwoon084/stock-lens** (`main` 브랜치, 팀원과 공유)
- 핵심 컨셉: 사용자가 주가 차트에서 특정 날짜를 클릭하면, 그 시점 전후 뉴스·공시·리포트를 분석해
  주가 변동 요인을 근거와 함께 보여주는 서비스. RAG 기반, "추천"이 아니라 "설명·요약"으로 역할 한정.

## 2. 확정된 의사결정

- **타깃 사용자: 초보 투자자** (2026-07-20 확정). 1차 멘토링(2026-07-03)에서 멘토가 "초보는
  거래량이 적어 수익성이 낮다"며 활발한 투자자 쪽도 검토해보라고 했지만, 팀은 초보 투자자로
  유지하기로 결정. → 기능은 "이해를 돕는" 방향(용어 풀이, 체크리스트, 원인 후보 설명)에 집중,
  UI/UX 완성도를 중요하게 봄.
- **프론트엔드: React** (Streamlit 아님). 이유: 토스증권 같은 곳과 알고리즘 정교함으로 경쟁할 수
  없으니, 차별점은 "차트 클릭 → 원인 후보/체크리스트를 직관적으로 보여주는 UI 편의성"에 있다는
  판단. 그래서 개발 속도보다 UI 폴리시가 중요.
- **빌드 순서: 핵심 기능 먼저, 인프라(Docker/CI-CD/GCP 배포)는 나중.** (다만 실제로는 팀원이
  Docker/CI/CD까지 이미 상당 부분 만들어둔 상태 — 아래 4번 참고)
- 투자자문법 관련: "추천 전면 배제"까지 갈 필요는 없고, 순한 설명·정보 제공 수준의 표현이면
  법적으로 괜찮다는 게 1차 멘토링 피드백.
- **프론트 화면 디자인: 정영준님의 초기 mock UI가 아니라, 1차 멘토링 목업 이미지 기준으로
  Claude Code와 함께 새로 짠 구조로 간다** (2026-07-20 확정). 이유: 목업(헤더 + 좌측 차트/원인
  후보 툴팁 + 우측 오늘의 체크리스트, 라이트 테마)에 더 가깝고 더 깔끔함. 정영준님의 원래 구조
  (캔들스틱 차트, 카드 나열형 AI 분석 패널)는 대체됨 — 아래 4번이 현재(대체 후) 구조.

## 3. 1차 멘토링 피드백 요약 (2026-07-03, Zoom 17:00~17:30)

| 주제 | 멘토 피드백 | 팀 반영 방향 |
|---|---|---|
| 화면 구성 | 큰 화면에 모든 기능을 한 번에 보는 대시보드형도 괜찮음 | 대시보드형 구성 유지 |
| 타깃·수익성 | 초보는 수익성 낮음, 활발한 투자자도 고려해볼 것 | 그래도 초보로 확정 (위 참고) |
| 투자자문 법규 | 순하게 추천하는 정도는 법 저촉 안 됨 | 추천 전면 배제 방침 완화 |
| 기능 범위 | 기능 덕지덕지 붙이지 말고 타깃 맞춤 선택·집중 | 초보용 핵심 기능만 |
| 시각화 | 초보 타깃이면 시각화 완성도가 더 중요 | UI/UX 폴리시 강화 |

다음 멘토링까지 목표: 타깃 확정(완료) → 기능 범위 좁히기 → **동작하는 프로토타입 시연**.

## 4. 현재 코드 상태 (중요 — 실제로 확인한 사실)

이 저장소는 원래 **정영준님이 만든 모노레포 boilerplate**로 시작했지만 (제가 처음에 만들었던
`app/` 스켈레톤은 이 구조로 대체·흡수됨), **2026-07-20에 프론트 화면을 1차 멘토링 목업 이미지
기준으로 Claude Code와 함께 다시 짰습니다** (위 2번 참고 — 정영준님의 원래 mock UI 대신 이 구조로
가기로 확정). 아래는 그 이후(현재) 구조:

```
backend/    FastAPI (routes → schemas/services → core/config 3계층)
  app/api/routes/     health.py, stocks.py, explanations.py, checklist.py
  app/services/       market_data_service.py(data/market_data.sqlite3 캐시만 조회, 없으면 mock —
                      pykrx는 절대 직접 호출 안 함), retrieval_service.py(disclosures.json 실제
                      DART 공시, 없으면 mock), llm_service.py(아직 mock), checklist_service.py
                      (news.json 실제 뉴스, 없으면 mock), explanation_service.py(위 3개 조합)
  app/agent/          LangGraph 스켈레톤 (state.py/nodes.py/graph.py, 현재 TODO 스텁)
  app/prompts/        explain_movement.txt (실제 LLM 연동 시 사용할 프롬프트)
  requirements.txt    fastapi, uvicorn, pydantic, pydantic-settings, pytest, httpx
frontend/   Vite + React + TypeScript (라이트 테마, 목업 기준 헤더 + 좌우 2단 그리드 레이아웃)
  src/features/price-chart/          PriceChart(라인/영역 차트, 클릭 시 픽셀 좌표 반환), ChartToolbar, usePriceChart
  src/features/movement-explanation/ ReasonTooltip(차트 위 플로팅 "원인 후보" 카드), useMovementExplanation
  src/features/article-checklist/    ArticleChecklist, ChecklistItemRow, useArticleChecklist (신규 — "오늘의 체크리스트")
  src/features/stock-selector/       StockSelector
  src/mocks/                         stockData.ts, explanationData.ts, checklistData.ts
  src/shared/                        api client(stocks/explanations/checklist), types, Card
data/       step1_corpcode.py, step2_disclosures.py (DART, 동작 확인됨), step4_prices.py(신규 —
            pykrx 일봉 수집 → market_data.sqlite3, backend venv로 수동/주기 실행), step5_news.py
            (네이버 뉴스 검색 API, NAVER_CLIENT_ID/SECRET 발급 완료·실행 완료)
            corp_codes.json, disclosures.json, news.json, market_data.sqlite3
            (수집 결과, gitignore 처리됨 — 로컬에만 존재)
docs/       project-plan.md, requirements.md, screen-design.md, api-spec.md, architecture.md, deployment.md
infra/      GCP Cloud Run 배포 관련 문서 (아직 실제 배포 안 함)
.github/workflows/  ci.yml (pytest), deploy.yml (GCP 배포 — 아직 미검증)
compose.yaml         docker compose up --build 으로 로컬 실행 가능
```

**폐기된 컴포넌트 (목업 재설계로 대체됨, 삭제됨):** `SelectedPoint.tsx`, `ExplanationPanel.tsx`,
`FactorCard.tsx`, `SourceList.tsx` — 별도 카드로 나열하던 방식 대신 `ReasonTooltip`이 차트 위
플로팅 카드로 합쳐서 보여줌.

**현재 구현 범위 (목업 이미지 기준 재설계 완료 + M1/M2 실제 데이터 연동 완료, 2026-07-21):**
- 종목 선택(5종목) → 헤더에 현재가/등락률 표시 → 라인 차트에서 급등락 지점 클릭 → 그 자리에
  플로팅 "이날 왜 올랐을까?/내렸을까? — 원인 후보" 카드(요인 + 근거) 표시 → 우측 "오늘의
  체크리스트"(체크박스 + [호재/실적/유의/중립] 태그 + 출처 건수 + 확인 진행률) 전부 **실제로
  동작 확인함** (Playwright로 스크린샷 검증, 콘솔 에러 없음)
- **M1 완료 (2026-07-21에 아키텍처 재정비)**: pykrx는 KRX/네이버 금융을 스크래핑하는 비공식 방식이라
  **요청마다 직접 호출하지 않기로 결정** — `data/step4_prices.py`가 오프라인으로 1년치 일봉을 수집해
  `data/market_data.sqlite3`에 저장하고, `market_data_service.py`는 이 캐시만 읽음(캐시 없으면
  결정론적 mock으로 폴백). 차트 기간은 **현재 시점 기준 최근 1년**(`_LOOKBACK_DAYS = 365`).
  발표 문구: "한국거래소 및 네이버 금융 데이터를 수집하는 pykrx를 활용해 시세 데이터를 사전
  구축했으며, 서비스 안정성을 위해 사용자 요청 시 외부 사이트를 직접 호출하지 않고 내부 저장
  데이터를 제공합니다." — **pykrx를 "공식 API"라고 표현하지 말 것.**
  금융위원회 공식 API는 신청만 해두고(키 발급 대기), 대표 종목·날짜 몇 개를 나중에 교차 검증할
  계획 — 지금 당장 그 연동에 시간 쓰지 않기로 함(아래 7번 참고).
- **M2 완료**: `retrieval_service.py`가 `data/disclosures.json`(실제 DART 공시)을 선택 날짜에 가장
  가까운 공시 3건으로 매칭해 원인 후보 근거로 사용함 — 실제 dart.fss.or.kr 링크. `checklist_service.py`도
  `data/news.json`(네이버 뉴스 검색 API, `data/step5_news.py`로 수집)이 있으면 근접 제목으로
  클러스터링 + 키워드 기반 태그 분류(호재/실적/유의/중립)를 거쳐 실제 기사로 채움 — **2026-07-21에
  NAVER_CLIENT_ID/SECRET 발급 완료 후 실행해서 검증까지 끝남.** 원인 후보 근거와 체크리스트 항목
  모두 실제 원문 링크("원문 보기"/근거 링크 클릭 시 새 탭으로 이동)까지 연결됨. 세 서비스(시세·
  공시·뉴스) 모두 데이터 파일이 없으면 자동으로 기존 mock으로 폴백하므로 팀원/CI 환경에서는
  안전하게 그대로 동작함.
- **공시 수집 기간을 차트와 동일하게 1년으로 확장 (2026-07-21)**: `data/step2_disclosures.py`의
  `DAYS_BACK`을 90 → 365로 늘리고, Open DART list.json의 조회기간 제한 때문에 90일 단위로 나눠
  요청(`CHUNK_DAYS`)하도록 수정. 재수집 결과 `disclosures.json`이 2025-07-23~2026-07-21 전체를
  커버함(총 1331건). 차트의 어느 지점을 클릭해도 원인 후보가 몇 달씩 동떨어진 공시를 근거로
  들이미는 문제가 해결됨.
- 차트 확대/축소 버그 수정(2026-07-21): `PriceChart.tsx`가 기본으로 마우스 휠/드래그 확대·이동을
  허용해서, 페이지 스크롤 중 실수로 차트가 확대되면 "전체" 탭이 눌린 채로도 일부 기간만 보이는
  문제가 있었음 → `handleScroll: false, handleScale: false`로 막아 기간 탭으로만 범위가 바뀌게 함.
- **M3 절반 완료 (2026-07-21)**: `llm_service.py`가 **SOLAR-pro2 → Gemini Flash → Groq(Llama 3.3
  70B) 3단 폴백**으로 실제 LLM을 호출함(전부 OpenAI 호환 엔드포인트라 provider별 SDK 없이 `openai`
  패키지 하나로 처리). 프롬프트(`app/prompts/explain_movement.txt`)가 검색된 문서를 `[id]`로 주고
  "이 id만 인용 가능"하게 강제해서 할루시네이션된 출처를 막음. **SOLAR는 실제로 동작 확인함**(실제
  공시 내용을 읽고 근거 없는 요인은 `source_ids: []`로 스스로 구분하는 것까지 검증) — **Gemini/Groq는
  아직 키가 없어서 자동으로 건너뛰어짐**(키 없는 provider는 조용히 skip 후 다음으로 넘어가서,
  키가 채워지는 순간 코드 변경 없이 바로 활성화됨). 3개 다 실패/미설정이면 기존 mock으로 폴백.
  `LLM_PROVIDER=mock`이면 아예 mock만 씀(테스트에서 강제 — `backend/tests/conftest.py`가 매 테스트
  전에 mock으로 고정해서 pytest가 실제 토큰을 쓰지 않음). **주의**: retrieval(근거 찾기)은 여전히
  결정론적 로직(날짜 근접도/키워드) 그대로 두고, LLM은 "찾아온 근거를 읽고 설명을 쓰는" 생성
  단계에만 씀 — 표준 RAG 패턴이자 "출처 기반 신뢰성" 원칙과 일치. 전부 LLM화하는 게 아님.
  ⚠️ `backend/app/core/config.py`의 `Settings.env_file`이 상대경로 `.env`였던 버그도 같이 고침
  (backend/ 안에서 uvicorn을 실행하면 backend/.env를 찾아서 루트 `.env`를 못 읽고 있었음 —
  절대경로로 고정).

**향후 마일스톤 (docs/project-plan.md):**
- M1: ~~실제 시세 연동~~ → **완료**
- M2: ~~실제 검색(공시·뉴스) 연동~~ → **완료**. 여유 있으면 `retrieval_service.py`/`checklist_service.py`를
  chromadb 기반 임베딩 검색·클러스터링으로 고도화(현재는 날짜 근접도/제목 중복·키워드 기반의 단순 로직).
- M3: SOLAR 실제 연동 **완료**. Gemini/Groq 키 발급 대기 중 — 발급되면 `.env`에 `GEMINI_API_KEY`,
  `GROQ_API_KEY`만 채워 넣으면 코드 변경 없이 3단 폴백이 자동으로 완성됨.
- M3: 실제 LLM 연동 — `llm_service.py`를 SOLAR(langchain-upstage) 또는 Gemini로 교체,
  `app/prompts/explain_movement.txt` + `backend/app/agent/`의 LangGraph 스켈레톤 활용,
  `LLM_PROVIDER` 환경변수로 전환
- M4: GCP 배포 — `infra/gcp-setup.md`의 1회성 설정 완료 후 `deploy.yml` 실행

## 5. 기술 스택 확정 사항 (2026-07-20) — 이전 프로젝트(MathMate) 자산 재사용

이전 수업 프로젝트 **MathMate**(`...생성형 AI 에이전트\MathMate`, LangGraph+FastAPI+Supabase+
Docker+GCE)의 인프라 패턴을 그대로 재사용하기로 확정함:
- **데이터 저장: Supabase** (RLS 전체 활성화 + 정책 없음 — service_role 키만 서버에서 접근 가능,
  anon 키는 잠금)
- **챗봇 LLM: SOLAR가 메인, Gemini Flash가 폴백 모델** (`LLM_PROVIDER` 환경변수로 전환 — M3에서 구현)
- **배포: GCE** (Cloud Run 아님 — MathMate와 같은 GCE VM 재사용). ⚠️ `infra/gcp-setup.md`와
  `.github/workflows/deploy.yml`은 기존에 Cloud Run 기준으로 작성돼 있어서, GCE 확정에 맞춰
  나중에 다시 손봐야 함(MathMate의 `cd.yml` 패턴 참고: GHCR 빌드/푸시 → GCE VM SSH 배포 →
  `/api/health` 체크).
- **CI/CD**: 지금 있는 `ci.yml`(pytest)은 유지, GCE 배포용 CD 워크플로는 추후 GitHub Actions로 추가 예정.
- **재사용 예정 자격증명**: `UPSTAGE_API_KEY`, `SUPABASE_URL`/`SUPABASE_KEY`(+ Supabase DB 비밀번호),
  GCE VM(호스트/유저/SSH 키). 실제 값은 사용자의 로컬 "에이전트 - 각종 키들.txt" 파일에 있음 —
  **이 저장소의 `.env`/`.env.example`에는 아직 반영 안 됨(플레이스홀더만 존재)** — 절대 이 값들을
  git에 커밋하거나 `.env.example`/문서에 그대로 옮기지 말 것. M3/Supabase 연동을 실제로 시작하는
  시점에 로컬 `.env`(gitignore됨)에만 채워 넣을 것.

## 6. 로컬 환경 관련 중요 이슈 (반드시 알아야 함)

- **이 폴더가 왜 `Downloads`에 있는가**: 원래 OneDrive의 한글 경로
  (`문서\대학교 4학년 여름학기 수업과목\현장 미러형 프로젝트\...`)에 있었는데, **경로에 한글이
  들어가면 `npm install`(esbuild 네이티브 바이너리 설치)이 STATUS_ACCESS_VIOLATION으로 무조건
  크래시**하는 것을 직접 재현해서 확인함 (OneDrive 동기화/백신 문제 아님 — 영문 경로면 OneDrive
  안이든 밖이든 문제없이 설치됨). 그래서 2026-07-20에 이 폴더로 통째로 이동함(git 히스토리·
  `.env`·수집 데이터 전부 보존). **앞으로도 이 프로젝트를 한글 경로로 옮기지 말 것.**
- **Python 버전**: 이 시스템 기본 Python은 3.9였는데, `backend/app/services/market_data_service.py`
  등에서 `Stock | None` 같은 PEP 604 문법을 써서 **Python 3.10+ 필수**. `winget install
  Python.Python.3.12`로 3.12 설치함 (`py -3.12`로 접근 가능). `backend/.venv`는 3.12로 생성됨.
- **Docker Desktop**: 설치는 되어 있으나 데몬이 꺼져있던 적이 있음 (`docker compose up` 실패 시
  Docker Desktop 앱이 실제로 켜져 있는지 먼저 확인).
- **로컬 실행 방법** (README.md 참고):
  ```
  # (최초 1회, 또는 시세 갱신하고 싶을 때) 주가 캐시 수집
  backend\.venv\Scripts\python.exe data\step4_prices.py
  # Backend
  cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
  # Frontend (다른 터미널)
  cd frontend && npm run dev -- --port 5173
  ```
  또는 `docker compose up --build`. `data/step4_prices.py`를 안 돌려도 앱은 mock 시세로 정상
  동작하지만(2026-07-21 기준 안전한 폴백), 실제 시세를 보려면 한 번 실행해야 함. 이전 세션에서
  백엔드(:8000)·프론트(:5173) 둘 다 로컬에서 띄워서 확인했었는데, 새 세션/재부팅 후에는 다시
  켜야 할 수 있음.

## 7. 다음에 결정/진행할 것

1. ~~"오늘의 기사 체크리스트" 카드 추가 여부~~ → **완료 (2026-07-20)**.
2. ~~M1(pykrx 실제 시세)~~ → **완료**(2026-07-21에 sqlite 캐시 구조로 재정비 — 4번 참고).
   ~~M2(공시·뉴스 실제 연동)~~ → **완료 (2026-07-21, NAVER_CLIENT_ID/SECRET 발급 완료 +
   `data/step5_news.py` 실행 검증까지 끝남)**.
3. M3(SOLAR/Gemini 실제 LLM) — 아직 시작 전. **우선순위상 다음 차례** (사용자가 명시적으로
   "금융위원회 API 연동보다 OpenDART·뉴스·Agent 연결에 집중" 하라고 확정함, 2026-07-21).
   `.env`에 SOLAR/Gemini/Supabase/GCE 자격증명은 이미 채워둠(6번 참고) — 실제 연동 코드 작성만 남음.
4. **시세 데이터 아키텍처 (2026-07-21 확정)**: pykrx는 비공식 스크래핑이라 요청마다 호출하지 않고,
   `data/step4_prices.py`로 오프라인 수집 → `data/market_data.sqlite3` 캐시 → 백엔드는 캐시만 조회.
   **금융위원회 공식 API는 신청만 해두고(키 아직 없음), 나중에 대표 종목·날짜 몇 개만 교차 검증**
   할 계획 — 지금 이 연동 작업에 시간 쓰지 않기로 함. 발표 때 pykrx를 "공식 API"라고 표현하지
   말 것(정확한 문구는 4번 코드 블록 위 M1 항목 참고).
5. GCP/GCE 배포(M4)는 아직 전혀 준비 안 됨 — `infra/gcp-setup.md`/`deploy.yml`이 Cloud Run 기준으로
   작성돼 있어 GCE로 다시 손봐야 함.
6. Supabase/Upstage 키는 이미 `.env`에 채워짐(2026-07-21) — M3 진행 시 바로 사용 가능.
7. 정영준님이 별도로 프론트를 계속 작업 중이라면, 이번에 확정한 목업 기준 구조(2번/4번 참고)로
   맞춰야 함 — 병합 시 충돌 나면 이 구조가 우선.
