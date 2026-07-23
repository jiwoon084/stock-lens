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
  구조. ~~유일하게 유지한 것: "오늘의 체크리스트"(실제 네이버 뉴스 기반) 카드~~ → **2026-07-22
  제거함**: AI 분석 리포트의 "주요 요인" 체크리스트와 내용이 겹쳐서 사용자가 직접 빼기로 결정 —
  아래 4번 참고. 관련 백엔드(`checklist.py` 라우트/스키마/서비스)와 프론트(`article-checklist/*`,
  `checklistData.ts` 등)도 전부 삭제함. `data/step5_news.py`·`data/news.json`은 여전히 유지 —
  `retrieval_service.py`가 원인 후보 근거에 뉴스를 섞는 데 그대로 씀(독립적인 별도 로더).

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
  app/api/routes/     health.py, stocks.py, explanations.py, analysis.py(신규 — 아래 10번)
  app/services/       market_data_service.py(공식 KRX API, 없으면 mock), krx_price_client.py
                      (data.go.kr 금융위원회_주식시세정보, 요청마다 실시간 호출 + 당일 in-process
                      캐시), retrieval_service.py(disclosures.json 실제 DART 공시 + news.json 실제
                      뉴스를 날짜 근접도 **+ SOLAR 임베딩 의미 유사도 하이브리드 랭킹**으로 섞어서
                      근거로 사용 — 아래 11번, 실제 본문 발췌 + 루틴성 공시 필터링, 데이터 둘 다
                      없으면 mock), embedding_client.py(신규 — 아래 11번, solar-embedding-1-large
                      query/passage), llm_service.py(사용자가 고른 SOLAR/Gemini 중 하나 호출,
                      키 없거나 실패 시 규칙 기반 폴백 — 아래 9번), solar_client.py/gemini_client.py
                      (각자 REST API 직접 호출), explanation_service.py(위 서비스 조합),
                      stock_analysis_service.py(아래 10번 — analyze_date()는 이제 절차형 함수가
                      아니라 app/agent/의 LangGraph를 빌드·실행함, 아래 11번), llm/(base.py/
                      factory.py/solar_provider.py/gemini_provider.py, stock_analysis_service 전용
                      provider 계층. llm_service.py의 라우팅과는 완전히 별개)
  app/rules/          watch_item_templates.py(아래 10번)
  app/agent/          **더 이상 스켈레톤 아님 — 아래 11번 참고.** state.py/nodes.py/graph.py로
                      stock-analysis LangGraph(fetch_market_data→retrieve_evidence→
                      build_llm_input→generate_analysis) 실제 구현함(2026-07-23)
  app/prompts/        explain_movement.txt (기존 LLM 프롬프트 — [id] 인용 강제), 
                      stock_analysis_system.txt(아래 10번)
  requirements.txt    fastapi, uvicorn, pydantic, pydantic-settings, pytest, httpx, requests,
                      numpy, langgraph(아래 11번)
                      (openai SDK 없음 — SOLAR/Gemini 둘 다 requests로 직접 REST 호출)
frontend/   Vite + React + TypeScript (라이트 테마, Koyfin/Perplexity 스타일 대시보드 — 정영준님 작업)
  src/App.tsx                         상단바 + 종목선택/StockHeader + workspace(좌: 차트+주목할만한
                                       가격변동, 우: 오늘의 체크리스트) 레이아웃 — 아래 10번 참고
  src/features/price-chart/           PriceChart(캔들/라인 토글, ChartTypeToggle, 선택 지점의 픽셀
                                       좌표를 콜백으로 노출 — 차트 팝오버용), StockHeader,
                                       SelectedPointInfo, ChartToolbar, usePriceChart
  src/features/movement-explanation/  AIAnalysisPanel/IssueChecklist(현재 App.tsx에서 직접 렌더링
                                       안 함 — 아래 10번), useMovementExplanation(llmProvider 인자),
                                       LlmProviderToggle(SOLAR/Gemini 사용자 선택 — 현재
                                       MarketEventsPanel 안에서 렌더링됨, 아래 9번/10번)
  src/features/market-events/         MarketEventsPanel(급등락일 카드 스트립 + LlmProviderToggle +
                                       관련 자료) + EventCard, SourceCard, marketEvents.ts
  src/components/analysis/            신규 — 아래 10번 (ChartSummaryCard, ChartMovementPopover,
                                       AnalysisDetailPanel, MovementSection, WatchChecklist,
                                       RecommendedMaterials, AnalysisCaution, useStockAnalysis)
  src/features/stock-selector/        StockSelector, useStocks
  src/mocks/                          stockData.ts, explanationData.ts
  src/shared/                         api client(stocks/explanations/stockAnalysis), types,
                                       Card(title+actions)
  src/types/stockAnalysis.ts          신규 — 아래 10번
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

⚠️ 이 트리는 **2026-07-22(eddie 세션, 아래 10번) 기준**입니다. 같은 날 다른 세션(권지운?)이
`llm_service.py`를 자동 라우팅으로, LLM 관련 파일들을 다시 되돌렸다가(위 checklist 제거와
함께 커밋됨), 이 세션에서 다시 사용자 선택 방식으로 되돌린 상태입니다 — 아래 9번 참고.
다음 세션은 병합 전에 반드시 9번/10번을 먼저 읽으세요.

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
  리포트"(요인 체크리스트 + 관련 자료 카드, 근거는 실제 링크로 클릭 가능) 전부 **실제로 동작
  확인함** (Playwright로 스크린샷 검증, 콘솔 에러 없음). 백엔드 계약(`/api/v1/stocks`,
  `/api/v1/stocks/{ticker}/prices`, `/api/v1/explanations`)이 두 프론트 구조 사이에서 동일해서,
  UI를 통째로 갈아끼워도 백엔드는 전혀 안 바꿔도 됐음.
  ~~별도 "오늘의 체크리스트"(네이버 뉴스 기반) 카드도 있었으나~~ **2026-07-22 제거** — AI 분석
  리포트의 "주요 요인" 체크리스트와 내용이 겹쳐서 사용자가 직접 빼기로 함. 관련 백엔드
  (`api/routes/checklist.py`, `schemas/checklist.py`, `services/checklist_service.py`)와 프론트
  (`features/article-checklist/*`, `mocks/checklistData.ts`, `shared/api/checklist.ts`,
  `shared/types/checklist.ts`)를 전부 삭제함. `/api/v1/stocks/{ticker}/checklist` 라우트도 없어짐.
  `data/step5_news.py`·`data/news.json`은 계속 유지 — `retrieval_service.py`가 원인 후보 근거에
  뉴스를 섞는 데 독립적으로 그대로 사용 중(아래 M2 참고).
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
  원인 후보 근거는 실제 원문 링크 클릭 가능. 데이터 파일 없으면 자동 mock 폴백이라 팀원/CI
  환경에서도 안전.
- 공시 수집 기간 1년 확장 + 페이지네이션(2026-07-21): `data/step2_disclosures.py`가
  `DAYS_BACK=365`(차트와 일치, 내 결정) + 90일 청크 분할(Open DART 기간 제한 대응) + 청크별
  페이지네이션(팀원 기여 — 청크당 100건 넘는 공시도 전부 수집)을 모두 반영. `disclosures.json`
  2025-07-23~2026-07-21 전체 커버(1331건).
- 차트 확대/축소 버그 수정: `PriceChart.tsx`에 `handleScroll: false, handleScale: false` — 마우스
  휠/드래그로 실수로 확대·이동되는 것을 막아 기간 탭으로만 범위가 바뀌게 함.
- **M3 완료 — SOLAR/Gemini 사용자 직접 선택 방식 (위 9번 참고)**: `llm_service.py`는 자동
  라우팅/폴백이 아니라 `MovementExplanationRequest.llm_provider`(`"solar"` | `"gemini"`, 기본
  `solar`) 필드로 프론트엔드가 직접 지정한 provider를 호출함. `solar_client.py`/`gemini_client.py`가
  각자 REST API를 `requests`로 직접 호출(openai SDK 안 씀), 응답을 JSON 스키마로 강제. 지정한
  provider의 키가 없거나 호출이 실패하면 규칙 기반(rule-based) 응답으로만 내려감 — 다른
  provider로 자동 전환하지 않음. Groq는 아예 없음. 프롬프트가 검색된 문서를 `[id]`로 주고 그
  id만 인용하게 강제해 할루시네이션 방지(`_sanitize_factors`로 이중 방어). **SOLAR·Gemini 둘 다
  실제 키로 동작 확인함**(Gemini는 aistudio.google.com/apikey에서 발급받은 키로 확인).
  "전역 mock 강제 스위치" 같은 개념은 안 씀 — 각 provider 키(`SOLAR_API_KEY`/`GEMINI_API_KEY`)
  존재 여부로만 실제 호출 여부를 판단(KRX 연동 때와 같은 패턴). retrieval은 여전히 결정론적
  로직 그대로 두고 LLM은 생성 단계에만 사용 — 표준 RAG, "출처 기반 신뢰성" 원칙과 일치.
  ⚠️ `Settings.env_file`이 상대경로 `.env`였던 버그도 고침(절대경로로 고정).
- **retrieval_service.py에 뉴스도 섞임 (2026-07-22)**: 원래 DART 공시만 근거로 썼는데,
  `data/news.json`(네이버 뉴스)도 같이 불러와서 공시 최대 3건 + 뉴스 최대 2건(한쪽이 모자라면
  상대가 채움)을 합친 뒤 선택 날짜와 가까운 순으로 재정렬. **주의**: 네이버 뉴스 API는 과거 특정
  날짜 검색을 지원 안 해서 항상 "오늘" 기사만 가져옴 — 오래된 날짜를 클릭하면 뉴스가 "관련 자료"엔
  뜨지만 실제로 무관한 경우가 많아 LLM이 "주요 요인"에는 인용을 안 할 수 있음(이건 버그 아니라
  "출처 기반 신뢰성" 원칙대로 정직하게 동작하는 것 — 사용자에게 이미 설명하고 확인받음).
- **AI 분석 리포트를 "차트 팝오버 + 오늘의 체크리스트"로 분리 (2026-07-22)** — 새 `POST
  /api/analysis/date` 엔드포인트와 프론트 `components/analysis/*`. 상세 내용은 아래 10번.

**향후 마일스톤 (docs/project-plan.md):**
- M1: ~~실제 시세 연동~~ → **완료** (공식 KRX API)
- M2: ~~실제 검색(공시·뉴스) 연동~~ → **완료** (실제 본문 발췌 + 뉴스 통합까지 포함)
- M3: SOLAR+Gemini **완료** — 사용자가 직접 고르는 방식으로 최종 확정(2026-07-21, 위 9번 참고,
  2026-07-22에 두 번째로 도전받았으나 재확정됨). 둘 다 실제 키로 동작 확인됨. 자동 라우팅/폴백·
  Groq는 없음(의도적으로 제외). `/api/analysis/date`(아래 10번)는 이것과 별개로 자기 provider
  계층(`services/llm/`)을 가지며, 현재는 env var `LLM_PROVIDER`(기본 solar)로만 고정 — 이 엔드포인트
  에는 아직 사용자 선택 토글이 없음(TODO).
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

## 9. LLM 아키텍처 — 사용자 직접 선택 vs 자동 라우팅, 벌써 세 번째 되돌림 (읽고 시작할 것)

이 저장소에서 가장 자주 반복되는 팀 내 충돌입니다. 시간순 정리:

1. **(2026-07-21, 정영준 세션) 1차 확정**: 권지운님 쪽 `llm_service.py`가 "3단 폴백 → 난이도
   기반 2단 라우팅"(`_providers_for()`, `_SIMPLE_SOURCE_THRESHOLD`)으로 발전하는 동안, 정영준님
   세션에서 사용자가 명시적으로 다른 방향을 요청: **"SOLAR/Gemini 중 하나를 사용자가 직접
   고르게 해줘, 기본은 SOLAR로"**. 병합 중 사용자에게 재확인 → **사용자 직접 선택으로 확정**
   (`LlmProviderToggle.tsx`, `solar_client.py`/`gemini_client.py`, per-request `llm_provider`
   필드, `openai` SDK 없이 `requests`로 각자 REST 호출).
2. **(2026-07-22, 권지운 추정 세션) 2차 되돌림**: 같은 날 다른 세션이 이 구조를 다시 "근거
   자료 개수 기반 자동 난이도 라우팅"으로 되돌리고(`llm_service.py`/`config.py`/`requirements.txt`
   등 되돌림, `solar_client.py`/`gemini_client.py`/`LlmProviderToggle.tsx`/관련 테스트 삭제,
   `backend/tests/conftest.py` mock 강제 픽스처 추가), origin에 병합·푸시함. 동시에 "오늘의
   체크리스트" 기능 전체(백엔드 라우트/스키마/서비스 + 프론트 `article-checklist/*`)를 삭제하는
   결정도 이 세션에서 커밋됨. 이 세션은 CLAUDE.md에 "다음 세션은 팀원과 먼저 상의하라"는 경고를
   남겼음.
3. **(2026-07-22, eddie 세션) 3차 재확정 — 지금 이 상태**: eddie 세션에서 이 새 AI 분석 리포트
   분리 기능(아래 10번)을 만드는 중 `git fetch`로 2번의 되돌림을 발견. 사용자(eddie)에게 직접
   확인 → **"사용자 직접 선택 방식으로 다시 되돌린다"로 명시적 재확정**. 2번에서 삭제됐던
   `solar_client.py`/`gemini_client.py`/`LlmProviderToggle.tsx`/`test_solar_client.py`/
   `test_gemini_client.py`/`llm_service.py`(사용자 선택 디스패처)/`config.py`/
   `explanation.py`(schema)/`explanation_service.py`/`requirements.txt`/관련 테스트를 전부
   1번 상태로 복원하고, 2번이 추가한 `backend/tests/conftest.py`(mock 강제 픽스처)는 다시 제거함.
   "오늘의 체크리스트" 삭제는 **2번과 이견 없음** — eddie 세션에서도 별도로 같은 결정을 내려서
   그대로 유지(코드도 이미 삭제된 상태 그대로 둠).

**현재(2026-07-22, eddie 세션 이후) 최종 상태**: `MovementExplanationRequest.llm_provider`
(`"solar"` | `"gemini"`, 기본 `solar`) 필드로 프론트가 직접 지정, `LlmProviderToggle.tsx`는
현재 `MarketEventsPanel` 안에 렌더링됨(위 10번에서 사이드바 레이아웃이 바뀌면서 옮겨짐).
자동 라우팅/폴백·Groq·전역 mock 강제 스위치 없음. "오늘의 체크리스트" 없음.

⚠️ **다음에 이 파일을 읽는 사람에게 — 제발 여기서 멈추고 팀원과 먼저 얘기하세요**: 같은
자리를 두고 벌써 3번 반대 방향으로 되돌려졌습니다. 다음 병합 전에 반드시 사람 대 사람으로
합의하지 않으면 4번째 되돌림이 됩니다(7번 참고). 자동 라우팅 아이디어 자체가 나쁜 건 아니고,
그 구현은 git 히스토리(`e258fd0`, `2de919d`, `6a290b4` 커밋과 2026-07-22의 되돌림 커밋)에
그대로 남아있으니 팀이 합의하면 언제든 다시 가져올 수 있습니다. 이 결정을 다시 바꾸기 전에
먼저 팀 전체(권지운, 정영준)와 상의해주세요 — 어느 한쪽 세션의 "사용자"만 확인받고 진행하지
말 것.

## 10. AI 분석 리포트를 "차트 팝오버 + 오늘의 체크리스트"로 분리 (2026-07-22, eddie 세션)

**배경**: 기존엔 차트에서 날짜를 클릭하면 사이드바의 "AI 분석 리포트" 하나에 headline/summary/
"주요 요인" 체크리스트/출처가 전부 몰려 있었음. 사용자가 이를 "이날 왜 움직였나요?"는 차트
옆 팝오버로, "앞으로 확인할 내용 + 더 읽어볼 자료"는 사이드바에 남기고 제목을 "오늘의
체크리스트"로 바꾸는 방향으로 재요청함(mockup 이미지 참고 — 목업 기준 구조 때 폐기됐던
`ReasonTooltip.tsx`류 플로팅 카드 컨셉이 부분적으로 부활한 셈).

**신규 백엔드 — `POST /api/analysis/date`** (기존 `/api/v1/explanations`는 완전히 그대로 둠,
`MarketEventsPanel`의 "관련 자료" 목록이 계속 그걸 씀):
- `app/schemas/stock_analysis.py` — LLM 입력 컨텍스트(`LLMInputContext`: market_data/
  quick_fact_candidates/disclosures/news/allowed_watch_items) + 출력(`StockAnalysisResponse`:
  `chart_card` + `detail_panel`) Pydantic 모델. 배열 최대 길이 전부 `Field(max_length=N)`으로
  강제(quick_facts 2, why_it_moved 2, what_to_watch 3, recommended_materials 2,
  information_to_verify 3).
- `app/rules/watch_item_templates.py` — `what_to_watch` 후보를 LLM이 자유생성하지 않고 여기서
  규칙 기반으로만 생성(공급계약 공시 키워드 → 정해진 2개 문구, 뉴스에 "HBM" 언급 → 정해진 1개
  문구). LLM은 이 후보 중 최대 3개를 고르기만 함.
- `app/prompts/stock_analysis_system.txt` — 별도 시스템 프롬프트 파일(하드코딩 안 함).
- `app/services/llm/`(`base.py`/`factory.py`/`solar_provider.py`/`gemini_provider.py`) — 이
  기능 전용 provider 계층. **9번의 `llm_service.py`(사용자 선택 디스패처)와는 완전히 무관** —
  절대 섞어서 되돌리지 말 것. `solar_provider.py`는 `solar_client.py`의 API_URL/MODEL 상수만
  재사용(같은 엔드포인트, 다른 응답 스키마라 새 함수). `gemini_provider.py`는 **인터페이스만**
  (`generate()` 호출 시 `LLMProviderError` — "Gemini 실제 API 연결"은 이번 요청 범위 밖으로
  명시적으로 제외됨). 기본 provider는 `settings.llm_provider`(env `LLM_PROVIDER`, 기본 `solar`).
- `app/services/stock_analysis_service.py` — 조회(market_data_service/retrieval_service 재사용)
  → quick_fact_candidates/allowed_watch_items 생성 → LLM 호출(실패 시 최대 1회 재시도) → 검증
  (`_sanitize_result`: source_id가 입력에 있는지, quick_facts/what_to_watch가 후보와 정확히
  일치하는지, recommended_materials의 information_to_verify가 available_topics에 포함되는지,
  중복 제거) → 검증 실패 시 LLM 호출 자체를 스킵하고 백엔드 데이터만으로 만든 결정론적
  `_fallback_result` 반환(모델 출력을 신뢰하지 않는 안전망, `llm_service.py`의 규칙 기반
  폴백과 같은 철학).
- `app/api/routes/analysis.py` — 라우터. `app/main.py`에 등록.
- 테스트: `backend/tests/test_stock_analysis_{schema,service}.py`.

**신규 프론트엔드**:
- `src/types/stockAnalysis.ts`, `src/shared/api/stockAnalysis.ts`.
- `src/components/analysis/`:
  - `useStockAnalysis.ts` — `/api/analysis/date` 호출 훅. 날짜가 바뀌면 이전 데이터를 즉시
    `null`로 비움(예전 날짜 결과가 새 날짜 결과처럼 남아있지 않도록).
  - `ChartSummaryCard.tsx` — 차트 카드 안, 차트 바로 아래에 작은 요약(날짜/등락률/한줄요약/
    quick facts 최대 2개/근거 배지).
  - `ChartMovementPopover.tsx` + `MovementSection.tsx` — **차트에서 클릭한 지점 옆에 뜨는
    팝오버**. `PriceChart.tsx`가 `onSelectedPointCoordinate` 콜백으로 클릭 지점의 픽셀 좌표를
    노출(`timeToCoordinate`/`priceToCoordinate` + `ResizeObserver`), `App.tsx`가 그 좌표로
    팝오버 위치를 계산해서 차트 좌/우 어느 쪽에 있든 컨테이너 밖으로 안 나가게 좌우 반전.
    ⚠️ 여기서 실제 버그 하나 고쳤음: `chartWrapperRef`가 `useRef`+마운트 전용 `useEffect([])`
    였는데, 가격 로딩 중엔 그 div가 아직 없어서 `ResizeObserver`가 끝내 안 붙어 `chartWidth`가
    영원히 0으로 고정되는 문제 — 콜백 ref로 바꿔서 해결(콜백 ref는 노드가 실제로 붙거나
    떨어질 때마다 호출되므로 조건부 렌더링에도 안전).
  - `AnalysisDetailPanel.tsx`(+ `WatchChecklist.tsx`/`RecommendedMaterials.tsx`/
    `AnalysisCaution.tsx`) — 사이드바에 남는 부분. 제목 "AI 분석 리포트" → **"오늘의
    체크리스트"**로 변경, "이날 왜 움직였나요?"(`MovementSection`, 이제 팝오버 전용)는 여기서
    제거하고 "앞으로 확인할 내용" + "더 읽어볼 자료" + 주의 문구만 남음.
- **이름 충돌**: 기존에 뉴스 기반 "오늘의 체크리스트"(`ArticleChecklist`) 카드가 따로 있었는데
  (9번의 2차 되돌림 세션이 이미 통째로 삭제함 — eddie 세션에서도 독립적으로 같은 요청을 받아
  App.tsx에서 빼뒀다가, 병합하면서 파일까지 완전히 삭제된 상태로 정리됨), 새 패널 제목과
  겹칠 뻔했으나 결과적으로 문제 없음(그 카드가 이제 존재하지 않음).
- `App.tsx`: `MarketEventsPanel`은 그대로 두되(9번 참고, `LlmProviderToggle` 여기로 옮김),
  날짜 클릭 시 기존 `explain()`(구 `/api/v1/explanations`, `MarketEventsPanel`용)과 신규
  `analyze()`(`/api/analysis/date`, 팝오버+사이드바용)를 **둘 다** 호출함 — 백엔드 LLM 호출이
  중복되는 비효율은 있지만, 두 기능을 완전히 분리해서 서로 건드리지 않는 게 안전하다고 판단.
  나중에 여유 있으면 하나로 합치는 걸 고려해볼 것(TODO).

**아직 안 한 것**:
- `/api/analysis/date`용 Gemini provider 실제 연결(`gemini_provider.py`는 인터페이스만).
- `/api/analysis/date`에 사용자 선택 토글 없음 — env var(`LLM_PROVIDER`)로만 고정.
- market_data_context의 `benchmark_name`/`market_comparison_text`(시장 대비 비교) — KOSPI
  지수 시리즈 데이터가 이 저장소에 없어서 항상 `None`. 인터페이스는 준비돼 있음.

## 11. 시맨틱 검색(SOLAR 임베딩) + LangGraph 에이전트 실제 구현 (2026-07-23, eddie 세션)

**배경**: 중간발표 준비 중 "MCP 같은 최신 기술을 접목하고 싶다"는 요청에서 출발했는데, 검토
결과 MCP는 최종 사용자(초보 투자자)에게 아무 가치가 없고 순수 기술력 어필용이라 우선순위를
낮추고, 대신 **실제 사용자에게도 이득이 되면서 이미 있던 미완성 조각(위 4번 `app/agent/`
TODO 스텁)을 채우는 두 가지**를 우선 진행하기로 함:
1. "RAG"라고 부르면서 실제로는 **날짜 근접도로만** 근거를 고르던 것을 **의미 기반 검색**으로
   보강.
2. 방치돼 있던 `app/agent/`(LangGraph) 스켈레톤을 실제로 채워서, `stock_analysis_service`를
   명시적 그래프로 재구성.

**1) `app/services/embedding_client.py` (신규)** — Upstage SOLAR 임베딩 API
(`https://api.upstage.ai/v1/solar/embeddings`)를 `solar_client.py`와 같은 스타일로 `requests`
직접 호출. `solar-embedding-1-large-query`(질의문용)/`solar-embedding-1-large-passage`(문서용)
두 모델을 구분해서 씀 — 같은 벡터 공간이라 서로 비교 가능. 키 없거나 호출 실패 시
`EmbeddingApiError`. 테스트: `backend/tests/test_embedding_client.py`.

**2) `retrieval_service.py` 하이브리드 랭킹** — `get_related_documents()`는 이제 선택 날짜의
등락 방향으로 짧은 질의문(`_build_movement_query`)을 만들어 임베딩하고, 공시 제목/뉴스
제목+요약을 임베딩해 코사인 유사도를 구한 뒤 `0.5×날짜근접도 + 0.5×의미유사도`로 재랭킹함
(본문 전체가 아니라 **제목만** 임베딩 — 후보 전체에 대해 DART 본문 실시간 조회를 다 하면
비용이 너무 커서, 실제 본문 발췌는 여전히 최종 선택된 상위 몇 건에 대해서만 지연 조회함).
루틴성 공시 후순위 배치(`_is_routine`)는 그대로 최우선 유지. `SOLAR_API_KEY`가 없거나
임베딩 호출이 실패하면 **기존 날짜순 정렬 함수(`disclosure_rank_key`/`news_rank_key`)를
그대로 호출** — 즉 키 없는 환경(팀원/CI)에서는 이전과 100% 동일하게 동작함. 검증:
`backend/tests/test_retrieval_service.py`가 "날짜는 가깝지만 무관한 공시 3건 + 날짜는
멀지만 의미상 관련 있는 공시 1건" 픽스처로, 임베딩 있을 때 후자가 실제로 상위 3슬롯 안에
들어오고, 임베딩 없을 때는 기존과 동일하게 날짜순 상위 3건이 나오는 것을 둘 다 확인함.

**3) `app/agent/` LangGraph 실제 구현** — `state.py`(`AnalysisGraphState` TypedDict,
기존에 있던 "종목 Q&A 챗봇"용 스켈레톤 상태는 이 기능과 안 맞아서 새로 정의), `nodes.py`
(`fetch_market_data`→`retrieve_evidence`→`build_llm_input`→`generate_analysis` 4개 노드,
전부 `stock_analysis_service.py`에 원래 있던 private 헬퍼(`_build_market_data_context`,
`_to_disclosure_context`, `_sanitize_result`, `_fallback_result` 등)를 그대로 감싸는
wrapper — 새 비즈니스 로직 없음, 그래서 그 헬퍼들을 직접 테스트하는 기존
`test_stock_analysis_service.py`가 전혀 안 바뀌어도 됨), `graph.py`(`StateGraph` 조립,
모듈 전역에 컴파일된 그래프 캐시). `stock_analysis_service.analyze_date()`는 이제 이 그래프를
`graph.invoke()`로 실행하고 결과를 꺼내는 얇은 함수로 축소됨 — `nodes.py`가
`stock_analysis_service`를 import하고 `stock_analysis_service.analyze_date()`는 함수 본문
안에서만(모듈 최상단 아님) `app.agent.graph`를 import하는 방식으로 순환 임포트를 피함
(자세한 이유는 `nodes.py`/`graph.py` 파일 안 docstring 참고).

**검증**: 기존 백엔드 테스트 62개(53개+임베딩/리트리벌/등 신규 9개) 전부 통과, 회귀 없음.
`test_analyze_date_endpoint_returns_valid_shape`가 실제로 LangGraph를 통해 엔드투엔드로
실행되는 것을 확인함(langgraph 체크포인트 관련 경고 로그로 그래프가 실제 실행됐음을 재확인).

**의도적으로 안 한 것**:
- `explain()`(`/api/v1/explanations`)의 `retrieval_service` 호출도 같은 하이브리드 랭킹의
  덕을 자동으로 봄(같은 함수를 공유하므로) — 이 엔드포인트 자체의 로직은 안 건드림.
- LangGraph 도입 자체가 답변 품질을 올리진 않음 — 품질 개선은 순전히 임베딩 하이브리드
  랭킹에서 나옴. LangGraph는 오케스트레이션을 명시적 구조로 만든 것뿐(관측성/확장성 목적).
- 그래프에 조건 분기/재시도 정책은 아직 안 넣음 — `generate_analysis` 노드 내부의 재시도
  (`MAX_RETRIES=1`)는 기존 `_generate_result` 로직 그대로 재사용.

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

1. ~~"오늘의 기사 체크리스트"(뉴스 기반, `article-checklist/*`) 카드 추가 여부~~ → 2026-07-20
   추가했다가, AI 분석 리포트 체크리스트와 내용이 겹쳐서 **제거함(팀 내 이견 없음, 9번의 2차·
   3차 세션 둘 다 독립적으로 같은 결정)**. `POST /api/analysis/date`용 "오늘의 체크리스트"(10번,
   `AnalysisDetailPanel`)는 이름은 같지만 **다른 기능**이니 혼동하지 말 것 — 지워진 건
   `article-checklist` 기능이고, 지금 있는 "오늘의 체크리스트"는 예전 AI 분석 리포트 패널의
   이름만 바뀐 것.
2. ~~M1(실제 시세)~~ → **완료** (공식 KRX API, 8번 병합 참고). ~~M2(공시·뉴스 실제 연동)~~ →
   **완료**(NAVER_CLIENT_ID/SECRET 발급 완료 + 실행 검증까지 끝남, retrieval_service는 병합으로
   본문 발췌까지 고도화됨).
3. ~~M3(SOLAR/Gemini 실제 LLM)~~ → **완료** — 사용자 직접 선택 방식으로 최종 확정(9번 참고,
   **벌써 3번째 확정** — 자동 라우팅으로 되돌리기 전에 반드시 9번 전체를 읽을 것).
4. GCP/GCE 배포(M4)는 아직 전혀 준비 안 됨 — `infra/gcp-setup.md`/`deploy.yml`이 Cloud Run 기준으로
   작성돼 있어 GCE로 다시 손봐야 함.
5. Supabase/Upstage 키는 이미 `.env`에 채워짐(2026-07-21) — 실제 Supabase 연동 코드는 아직 안 짬.
6. 정영준님이 프론트를 별도로 더 작업한다면, **2번(2026-07-21 대시보드 UI 전환 재확정)에서
   확정한 대시보드 구조**로 맞춰야 함 — 병합 시 충돌 나면 이 구조가 우선. (8번 병합 당시엔
   "내 프론트 유지"였다가 2번에서 다시 뒤집혔으니, 8번보다 2번/4번이 최신 상태.)
7. **팀 커뮤니케이션 매우 시급함**: LLM 구조(자동 라우팅 vs 사용자 선택 토글)를 두고 팀원들이
   벌써 **세 번** 반대 방향으로 각자 작업 후 병합에서 되돌리는 일이 반복됨(9번 참고). 각 세션이
   "사용자에게 확인받았다"고 기록해도, 그게 팀 전체의 합의는 아니었던 게 문제 — 다음에 또
   이 주제를 건드리기 전에 권지운·정영준·(이 세션의) 사용자 셋이 실제로 한 자리에서 결론을
   내고, 그 결론을 이 문서에 "최종"이라고 못 박은 뒤에는 코드로만 반영하고 CLAUDE.md 재서술은
   하지 않는 쪽을 추천.
8. `/api/analysis/date`(10번)의 남은 TODO: Gemini provider 실제 연결, 사용자 선택 토글 여부
   결정, market_comparison_text용 KOSPI 지수 데이터 소스 확보, 그리고 `explain()`/`analyze()`
   중복 호출 통합 검토. ~~`app/agent/` LangGraph 스켈레톤 채우기~~ → **완료**(11번 참고,
   2026-07-23) — 단, `explain()`/`analyze()` 중복 호출 통합은 여전히 안 함(11번도 같은 한계
   명시).
