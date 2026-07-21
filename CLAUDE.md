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
- ~~프론트 화면 디자인: 목업 이미지 기준으로 Claude Code와 함께 새로 짠 구조 (2026-07-20 확정)~~
  → **2026-07-21 재확정: 정영준님의 Koyfin/Perplexity 스타일 대시보드 UI로 전면 전환.**
  이유: 팀원이 헤더(종목 요약) + 캔들/라인 토글 차트 + "주목할 만한 가격변동"(급등락일 카드
  스트립) + AI 분석 리포트(요인 체크리스트 포함) + 관련 자료 카드까지 이미 만들어뒀고, 사용자가
  이 구조로 가기로 결정함. 목업 기준 2단 그리드+플로팅 툴팁 구조는 폐기됨 — 아래 4번이 현재
  구조. 유일하게 유지한 것: "오늘의 체크리스트"(실제 네이버 뉴스 기반) 카드 — 팀원 대시보드에는
  없던 기능이라 AI 분석 리포트 아래에 새로 얹음.

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

이 저장소는 원래 **정영준님이 만든 모노레포 boilerplate**로 시작했고, 2026-07-20에 한 번 목업
이미지 기준 구조로 재설계했었으나 **2026-07-21에 정영준님의 Koyfin/Perplexity 스타일 대시보드
UI로 다시 전환했습니다** (위 2번 참고). 아래는 현재(대시보드 전환 후) 구조:

```
backend/    FastAPI (routes → schemas/services → core/config 3계층)
  app/api/routes/     health.py, stocks.py, explanations.py, checklist.py
  app/services/       market_data_service.py(공식 KRX API, 없으면 mock), krx_price_client.py
                      (data.go.kr 금융위원회_주식시세정보, 요청마다 실시간 호출 + 당일 in-process
                      캐시), retrieval_service.py(disclosures.json 실제 DART 공시 + news.json 실제
                      뉴스를 날짜 근접도로 섞어서 근거로 사용, 실제 본문 발췌 + 루틴성 공시 필터링,
                      둘 다 없으면 mock), llm_service.py(근거 자료 개수로 SOLAR/Gemini Flash 라우팅,
                      실제 LLM), checklist_service.py(news.json 실제 뉴스, 없으면 mock),
                      explanation_service.py(위 서비스 조합)
  app/agent/          LangGraph 스켈레톤 (state.py/nodes.py/graph.py, 현재 TODO 스텁, 손 안 댐)
  app/prompts/        explain_movement.txt (LLM 프롬프트 — [id] 인용 강제로 할루시네이션 방지)
  requirements.txt    fastapi, uvicorn, pydantic, pydantic-settings, pytest, httpx, openai, requests
frontend/   Vite + React + TypeScript (라이트 테마, Koyfin/Perplexity 스타일 대시보드 — 정영준님 작업)
  src/App.tsx                         상단바 + 종목선택/StockHeader + workspace(좌: 차트+주목할만한
                                       가격변동, 우: AI분석리포트+오늘의체크리스트) 레이아웃
  src/features/price-chart/           PriceChart(캔들/라인 토글, ChartTypeToggle), StockHeader,
                                       SelectedPointInfo, ChartToolbar, usePriceChart
  src/features/movement-explanation/  AIAnalysisPanel(요인 체크리스트 IssueChecklist 포함),
                                       useMovementExplanation
  src/features/market-events/         MarketEventsPanel(급등락일 카드 스트립) + EventCard, SourceCard
                                       (관련 자료 카드), marketEvents.ts(급등락 상위 N일 선정)
  src/features/article-checklist/     ArticleChecklist, ChecklistItemRow, useArticleChecklist
                                       ("오늘의 체크리스트" — 대시보드에 없던 기능이라 새로 얹음)
  src/features/stock-selector/        StockSelector, useStocks
  src/mocks/                          stockData.ts, explanationData.ts, checklistData.ts
  src/shared/                         api client(stocks/explanations/checklist), types, Card(title+actions)
data/       step1_corpcode.py, step2_disclosures.py(DART, 1년치 청크 수집), step3_major_events.py
            (신규 — 자기주식취득/처분·유상증자 등 구조화 공시, 팀원 작성), step5_news.py(네이버 뉴스)
            corp_codes.json, disclosures.json, major_events.json, news.json
            (수집 결과, gitignore 처리됨 — 로컬에만 존재. pykrx/step4_prices.py/market_data.sqlite3는
            공식 KRX API로 교체되며 완전히 삭제됨 — 아래 8번 참고)
docs/       project-plan.md, requirements.md, screen-design.md, api-spec.md, architecture.md,
            deployment.md (팀원이 2026-07-21에 실제 구현 상태에 맞춰 갱신 — 병합 시 그대로 채택)
infra/      GCP Cloud Run 배포 관련 문서 (아직 실제 배포 안 함, GCE로 다시 손봐야 함)
.github/workflows/  ci.yml (pytest), deploy.yml (GCP 배포, DART/KRX 시크릿 추가됨 — 아직 미검증)
compose.yaml         docker compose up --build 으로 로컬 실행 가능
```

**폐기된 컴포넌트 (2026-07-21 대시보드 전환으로 삭제됨):** 목업 기준 구조 때 만들었던
`ReasonTooltip.tsx`(차트 위 플로팅 카드), `SelectedPoint.tsx`, `ExplanationPanel.tsx`,
`FactorCard.tsx`, `SourceList.tsx` — 전부 정영준님의 대시보드 컴포넌트(`AIAnalysisPanel`,
`MarketEventsPanel`, `SelectedPointInfo`, `StockHeader` 등)로 대체됨. **주의**: 8번(2026-07-21
1차 병합) 당시엔 반대로 "프론트는 내 것 유지, 팀원 대시보드 컴포넌트 제외"로 결정했었으나,
바로 다음에 사용자가 "UI도 팀원 것 전체로 전환"으로 재확정하면서 뒤집힘 — 팀원 컴포넌트들을
git 히스토리(커밋 `7760d32`~`0a71d36`)에서 다시 꺼내와 적용함.

**현재 구현 범위 (대시보드 UI 전환 + M1/M2/M3 실제 데이터·LLM 연동 완료, 2026-07-21):**
- 상단바 → 종목 선택 + StockHeader(현재가/등락률) → 캔들/라인 토글 가능한 주가 차트(클릭 시
  선택 정보 표시) → "주목할 만한 가격변동"(등락률 상위 카드, 클릭 시 분석) → 우측 "AI 분석
  리포트"(요인 체크리스트 + 관련 자료 카드, 근거는 실제 링크로 클릭 가능) + "오늘의 체크리스트"
  (체크박스 + [호재/실적/유의/중립] 태그 + 출처 건수 + 원문 링크 + 확인 진행률) 전부 **실제로
  동작 확인함** (Playwright로 스크린샷 검증, 콘솔 에러 없음). 백엔드 계약(`/api/v1/stocks`,
  `/api/v1/stocks/{ticker}/prices`, `/api/v1/explanations`, `/api/v1/stocks/{ticker}/checklist`)이
  두 프론트 구조 사이에서 동일해서, UI를 통째로 갈아끼워도 백엔드는 전혀 안 바꿔도 됐음.
- **M1 완료 — 공식 KRX API로 전환 (2026-07-21, 8번 병합 시 팀원 것 채택)**: 처음엔 pykrx(스크래핑)
  +SQLite 오프라인 캐시로 구현했었으나, 팀원이 **금융위원회_주식시세정보(data.go.kr 공식 서비스키
  API)** 로 이미 전환·검증해둔 것을 발견해 그쪽으로 교체함. pykrx는 개인 계정 기반 스크래핑이라
  ToS/계정 안전성 리스크가 있는데, 공식 API는 이 문제가 없음 — `market_data_service.py`가
  `KRX_API_KEY` 설정 시 `krx_price_client.py`로 요청마다 실시간 호출(당일 in-process 캐시로 같은
  날 재호출 방지), 키 없거나 실패 시 결정론적 mock으로 폴백. 차트 1년 표시 요구사항에 맞춰
  `TRADING_DAYS`(30→250)·`LOOKBACK_CALENDAR_DAYS`(60→375)·`numOfRows`(100→300)를 조정함(팀원
  원본은 30거래일 기준이었음). 발표 문구: "금융위원회_주식시세정보(data.go.kr) 공식 API로 실제
  시세를 조회하며, 서비스 안정성을 위해 당일 캐시를 사용합니다." — 이제 정말 공식 API라고 말해도 됨.
- **M2 완료 — retrieval_service.py 병합**: 날짜 근접도 매칭(내 것, 1년치 공시 커버)에 팀원의 실제
  DART document.xml 본문 발췌(`_fetch_document_excerpt`, XML/HTML 파싱 폴백 포함) + 루틴성 공시
  (임원 소유변동 등) 후순위 배치(`_is_routine`) + `major_events.json` 구조화 필드 우선 사용을
  결합함. 랭킹 키는 `(is_routine, 과거우선여부, 날짜거리)` 3단 조합. 근거의 excerpt가 이제 "OO
  공시 원문은 DART에서 확인하세요" 같은 placeholder가 아니라 **실제 공시 본문 일부**임.
  `checklist_service.py`는 그대로(팀원이 손대지 않음) — `data/news.json` 있으면 실제 뉴스, 없으면
  mock. 원인 후보 근거·체크리스트 항목 모두 실제 원문 링크 클릭 가능. 데이터 파일 없으면 자동
  mock 폴백이라 팀원/CI 환경에서도 안전.
- 공시 수집 기간 1년 확장 + 페이지네이션(2026-07-21): `data/step2_disclosures.py`가
  `DAYS_BACK=365`(차트와 일치, 내 결정) + 90일 청크 분할(Open DART 기간 제한 대응) + 청크별
  페이지네이션(팀원 기여 — 청크당 100건 넘는 공시도 전부 수집)을 모두 반영. `disclosures.json`
  2025-07-23~2026-07-21 전체 커버(1331건).
- 차트 확대/축소 버그 수정: `PriceChart.tsx`에 `handleScroll: false, handleScale: false` — 마우스
  휠/드래그로 실수로 확대·이동되는 것을 막아 기간 탭으로만 범위가 바뀌게 함.
- **M3 완료(SOLAR+Gemini 둘 다 실동작 검증됨) — 2026-07-22에 아키텍처를 "3단 폴백"에서 "난이도 기반
  2단 라우팅"으로 변경**: `llm_service.py`가 이제 **폴백 체인이 아니라 근거 자료 개수로 SOLAR-pro2 /
  Gemini Flash 중 하나를 고름** — 근거가 `_SIMPLE_SOURCE_THRESHOLD`(2)개 초과면 "어려운 요청"으로
  보고 SOLAR-pro2, 그 이하면 "쉬운 요청"으로 보고 Gemini Flash. 라우팅된 쪽이 키가 없거나 실패하면
  나머지 하나를 그 요청에 한해 안전망으로 시도(순수 폴백 아님, 라우팅 실패 시 보정용). **Groq는
  완전히 제거함**(3단 → 2단). 전부 OpenAI 호환 엔드포인트라 `openai` 패키지 하나로 처리. 프롬프트가
  검색된 문서를 `[id]`로 주고 그 id만 인용하게 강제해 할루시네이션 방지. **SOLAR·Gemini 둘 다 실제
  키로 동작 확인함**(2026-07-22, Gemini는 aistudio.google.com/apikey에서 발급받은 키로 근거 1건짜리
  요청을 직접 호출해 정상 응답 확인). `LLM_PROVIDER=mock`이면 mock만 사용(테스트에서 강제 —
  `backend/tests/conftest.py`). 라우팅 로직 자체는 `backend/tests/test_llm_service.py`로 고정해둠
  (`_providers_for()`가 임계값 안팎에서 정확히 [gemini, solar] / [solar, gemini] 순서를 반환하는지).
  retrieval은 여전히 결정론적 로직 그대로 두고 LLM은 생성 단계에만 사용 — 표준 RAG, "출처 기반
  신뢰성" 원칙과 일치.
  ⚠️ `Settings.env_file`이 상대경로 `.env`였던 버그도 고침(둘 다 독립적으로 이 버그를 발견·수정함 —
  절대경로로 고정).
- **retrieval_service.py에 뉴스도 섞임 (2026-07-22)**: 원래 DART 공시만 근거로 썼는데,
  `data/news.json`(네이버 뉴스)도 같이 불러와서 공시 최대 3건 + 뉴스 최대 2건(한쪽이 모자라면
  상대가 채움)을 합친 뒤 선택 날짜와 가까운 순으로 재정렬. **주의**: 네이버 뉴스 API는 과거 특정
  날짜 검색을 지원 안 해서 항상 "오늘" 기사만 가져옴 — 오래된 날짜를 클릭하면 뉴스가 "관련 자료"엔
  뜨지만 실제로 무관한 경우가 많아 LLM이 "주요 요인"에는 인용을 안 할 수 있음(이건 버그 아니라
  "출처 기반 신뢰성" 원칙대로 정직하게 동작하는 것 — 사용자에게 이미 설명하고 확인받음).

**향후 마일스톤 (docs/project-plan.md):**
- M1: ~~실제 시세 연동~~ → **완료** (공식 KRX API)
- M2: ~~실제 검색(공시·뉴스) 연동~~ → **완료** (실제 본문 발췌 + 뉴스 통합까지 포함)
- M3: SOLAR+Gemini **완료** — 사용자가 직접 고르는 방식으로 최종 확정(2026-07-21, 위 9번 참고).
  둘 다 실제 키로 동작 확인됨. 자동 라우팅/폴백·Groq는 없음(의도적으로 제외).
- M4: GCP 배포 — `infra/gcp-setup.md`의 1회성 설정 완료 후 `deploy.yml` 실행 (Cloud Run 기준으로
  작성돼 있어 GCE 확정에 맞춰 다시 손봐야 함)

## 8. 팀원 브랜치 병합 (2026-07-21)

팀원(권지운/정영준)이 origin/main에 독자적으로 4개 커밋을 푸시해둔 상태였음(대시보드형 프론트
리디자인, 공식 KRX API 연동, retrieval_service 본문 발췌 고도화, docs 갱신). 사용자 지시에 따라
다음 기준으로 병합함:
- **프론트엔드: 내 것(목업 기준 재설계) 유지.** 팀원의 "Koyfin/Perplexity 스타일 대시보드"
  리디자인 컴포넌트는 전부 제외함(위 4번 "폐기된 컴포넌트" 참고).
- **시세 데이터: 팀원 것(공식 KRX API) 채택** — pykrx의 ToS 리스크를 팀원이 먼저 지적했고, 이미
  실제 키로 검증까지 끝내둔 상태였음. `data/step4_prices.py`·`market_data.sqlite3`는 완전히 삭제.
- **공시 검색: 병합** — 내 1년 창 + 팀원의 실제 본문 발췌/루틴 필터링 로직.
- **LLM: 내 것(당시 SOLAR/Gemini/Groq 3단 실제 폴백) 유지** — 팀원 건 아직 heuristic mock 수준이라
  명백히 내 것이 더 발전됨. (2026-07-22에 3단 폴백 → 2단 난이도 라우팅으로 변경, 위 참고)
- **부가 기능/문서: 팀원 것 그대로 채택** — `step3_major_events.py`, docs/*.md, README.md,
  deploy.yml 시크릿 추가, compose.yaml, infra/* 전부 병합함(우리 작업과 충돌 없음).
- 병합 후 백엔드 테스트 14개(8+팀원 6개) 전부 통과, 프론트 빌드 정상, 실제 KRX API로 시세 조회
  end-to-end 검증 완료.

## 9. LLM 아키텍처 재결정 — 사용자 직접 선택으로 확정 (2026-07-21, 정영준 세션)

8번 병합 이후 권지운님 쪽에서 `llm_service.py`를 "3단 폴백 → 난이도 기반 2단 라우팅"(위 4번,
`_providers_for()`, `_SIMPLE_SOURCE_THRESHOLD`)으로 계속 발전시켰는데, 같은 시기 정영준님
세션에서 사용자가 명시적으로 다른 방향을 요청함: **"사용자가 SOLAR/Gemini 중 하나를 직접
고르게 해줘, 기본은 SOLAR로"** — 자동 라우팅/폴백이 아니라 사람이 명시적으로 선택하는 구조.
두 요구사항이 정면으로 충돌해서 병합 중에 사용자에게 다시 확인했고, **"이번 세션에서 만든 것
(사용자 직접 선택) 유지"로 확정**함. 아래는 그 결과로 origin/main에 실제 반영된 최종 구조.

**최종 채택된 구조**:
- `MovementExplanationRequest.llm_provider`(`"solar"` | `"gemini"`, 기본 `solar`) 필드로
  프론트엔드가 직접 지정. `frontend/src/features/movement-explanation/LlmProviderToggle.tsx`
  버튼으로 사용자가 고름 — 자동 폴백/라우팅 없음(그 provider 키가 없거나 호출이 실패하면
  규칙 기반으로만 내려감, 다른 provider로 자동 전환하지 않음).
- `app/services/solar_client.py` / `gemini_client.py` — 각자 자기 REST API를 `requests`로
  직접 호출(`openai` SDK 안 씀), 응답을 JSON 스키마로 강제. `llm_service.py`의 `_PROVIDERS`
  딕셔너리(provider명 → 클라이언트/에러타입/키 존재 확인 함수)로 배선.
- Groq는 아예 없음 — 이번 요청 범위 밖.
- `settings.llm_provider`/`LLM_TIMEOUT`/`LLM_NUM_RETRIES`/`UPSTAGE_API_KEY`/`SOLAR_MODEL`/
  `SOLAR_BASE_URL`/`GROQ_API_KEY`/`GROQ_MODEL`, `backend/tests/conftest.py`(mock 강제 픽스처)
  **전부 삭제**. "전역 mock 강제 스위치"라는 개념 자체를 안 씀 — 각 provider 키(`SOLAR_API_KEY`/
  `GEMINI_API_KEY`) 존재 여부로만 실제 호출 여부를 판단(KRX 연동 때와 같은 패턴).
- 프롬프트의 `[id]` 인용 강제(위 4번 132번째 줄 근처 설명, `_sanitize_factors`로 이중 방어)는
  두 브랜치 다 독립적으로 좋다고 판단했던 부분이라 그대로 유지.

**둘 다 실제 키로 검증**(2026-07-21): SOLAR `solar-pro2`
(`https://api.upstage.ai/v1/chat/completions`). Gemini는 `gemini-flash-latest`로 최종
확정(날짜 박힌 모델명 `gemini-2.5-flash`는 새로 만든 키에서 404 "no longer available to new
users", `gemini-3.5-flash`는 유료 Prepay 플랜 필요라 429 — 이 별칭이 둘 다 해결). 백엔드
테스트 35개(기존 24 + 이번에 추가한 11) 전부 통과, 프론트 빌드/lint 통과, 실제 화면에서
SOLAR/Gemini 버튼 전환까지 확인.

⚠️ **다음에 이 파일을 읽는 사람(권지운님 세션 포함)에게**: `llm_service.py`를 다시 "자동
폴백/난이도 라우팅" 방향으로 되돌리지 마세요 — 실수로 지워진 게 아니라 이 세션에서 사용자에게
직접 확인받고 되돌린 결정입니다. 라우팅/자동폴백 아이디어 자체가 나쁜 건 아니고(실제로 한 번
병합해서 반영했다가 다시 되돌린 것뿐), 나중에 다시 필요해지면 git 히스토리(`e258fd0`,
`2de919d`, `6a290b4` 커밋)에 그 구현이 그대로 남아있으니 거기서 가져오면 됩니다. 이 결정을
바꾸려면 먼저 사용자(정영준)와 다시 상의해주세요.

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
  # Backend
  cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
  # Frontend (다른 터미널)
  cd frontend && npm run dev -- --port 5173
  ```
  또는 `docker compose up --build`. `KRX_API_KEY`/`DART_API_KEY`/`NAVER_CLIENT_ID`+`SECRET` 등이
  없어도 앱은 전부 mock으로 정상 동작함(안전한 폴백) — 실제 데이터를 보려면 `.env`에 해당 키를
  채우면 됨(시세는 키만 있으면 요청 시 바로 살아남, 공시/뉴스는 `data/step2_disclosures.py`·
  `data/step5_news.py`를 한 번 실행해야 함). 이전 세션에서 백엔드(:8000)·프론트(:5173) 둘 다
  로컬에서 띄워서 확인했었는데, 새 세션/재부팅 후에는 다시 켜야 할 수 있음.

## 7. 다음에 결정/진행할 것

1. ~~"오늘의 기사 체크리스트" 카드 추가 여부~~ → **완료 (2026-07-20)**.
2. ~~M1(실제 시세)~~ → **완료** (공식 KRX API, 8번 병합 참고). ~~M2(공시·뉴스 실제 연동)~~ →
   **완료**(NAVER_CLIENT_ID/SECRET 발급 완료 + 실행 검증까지 끝남, retrieval_service는 병합으로
   본문 발췌까지 고도화됨).
3. ~~M3(SOLAR/Gemini 실제 LLM)~~ → **완료** — 사용자가 SOLAR/Gemini를 직접 고르는 구조로 최종
   확정(자동 라우팅/폴백·Groq 없음, 2026-07-21, 위 9번 참고), 둘 다 실제 키로 동작 확인됨.
4. GCP/GCE 배포(M4)는 아직 전혀 준비 안 됨 — `infra/gcp-setup.md`/`deploy.yml`이 Cloud Run 기준으로
   작성돼 있어 GCE로 다시 손봐야 함.
5. Supabase/Upstage 키는 이미 `.env`에 채워짐(2026-07-21) — 실제 Supabase 연동 코드는 아직 안 짬.
6. 정영준님이 프론트를 별도로 더 작업한다면, **2번(2026-07-21 대시보드 UI 전환 재확정)에서
   확정한 대시보드 구조**로 맞춰야 함 — 병합 시 충돌 나면 이 구조가 우선. (8번 병합 당시엔
   "내 프론트 유지"였다가 2번에서 다시 뒤집혔으니, 8번보다 2번/4번이 최신 상태.)
