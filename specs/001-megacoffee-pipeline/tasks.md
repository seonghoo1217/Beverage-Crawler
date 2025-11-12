# Tasks: Starbucks · MegaCoffee 데이터 정합성 파이프라인

**Input**: Design documents from `/specs/001-ocr-data-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 명시적 테스트 요구는 없지만, 각 단계에서 데이터 검증 스크립트와 벤치마크 실행을 포함합니다.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 프로젝트 디렉터리·환경 초기화 및 필수 도구 세팅

- [x] T001 생성된 파이프라인 폴더 구조 확인 및 `storage/bronze|silver|gold` 디렉터리/`.keep` 파일 생성 (`app/storage/`)
- [x] T002 `.env` 혹은 설정 파일에 브랜드별 크롤링 URL·스케줄 파라미터를 정의하고 샘플 값을 추가 (`app/config/settings.py`)
- [x] T003 [P] FastAPI 배치 진입점에서 medallion 파이프라인을 트리거할 CLI/엔드포인트 골격 작성 (`app/main.py`)
- [x] T004 [P] requirements에 lint/정적분석 도구(`ruff`, `radon`)와 jsonschema, pydantic 버전 명시 후 잠금 (`app/requirements.txt`)
- [x] T005 CI 혹은 로컬 pre-commit 스크립트에 lint + maintainability 체크 파이프라인 추가 (`.github/workflows/ci.yml` 또는 `scripts/precommit.sh`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 전 스토리 공통으로 필요한 검증/관측/데이터 계약 준비

**Constitution Gate**: Include explicit tasks for
`Self-Describing Code (C- Floor)` (lint/static-analysis configuration),
`Zero-Fault Data Pipeline` (schema validation harness + reconciliation jobs),
`High-Fidelity OCR Backbone` (benchmark suite + labeled dataset prep),
and `Lean Dependency Discipline` (dependency review checklist).

- [x] T006 Bronze→Silver→Gold 공통 스키마(pydantic models + jsonschema)를 정의하고 버전 태그 추가 (`app/pipelines/models.py`)
- [x] T007 [P] Duplicate/Checksum 검증 유틸 작성: 배치마다 원천 해시·중복 탐지 로직 구현 (`app/pipelines/validators/dedup_validator.py`)
- [x] T008 [P] Structured logging 헬퍼 및 Prometheus 메트릭 수집 지표 정의 (`app/observability/logging.py`, `app/observability/metrics.py`)
- [x] T009 OCR 벤치마크 스크립트 초안과 벤치마크용 캡처 목록 manifest 작성 (`scripts/ocr_benchmark.py`, `data/benchmarks/manifest.json`)
- [x] T010 의존성 결정 로그 템플릿 작성 및 README 링크 추가 (설명서에 새 라이브러리 도입 근거 기록) (`docs/DEPENDENCY_DECISIONS.md`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Starbucks 영양정보 수집·검증 (Priority: P1) 🎯 MVP

**Goal**: Starbucks 웹/앱에서 원천 데이터를 안정적으로 수집해 Bronze→Silver 티어로 올리고 필수 영양 필드를 100% 채운다.

**Independent Test**: 샘플 50건 기반 end-to-end 배치를 실행하여 누락·중복률 보고서를 브랜치별로 확인하면 스토리 완성.

### Implementation for User Story 1

- [x] T011 [US1] Starbucks 크롤러가 DOM 변경을 감지하도록 셀렉터/에러 처리 강화 (`app/starbucks_crawler.py`)
- [x] T012 [P] [US1] 크롤링 결과와 PNG 소스 메타를 Bronze tier manifest에 기록 (`app/pipelines/bronze_ingest.py`)
- [x] T013 [US1] OCR 실행 파이프라인에서 PNG당 3회 시도 및 confidence 캡처 (`app/ocr.py`)
- [x] T014 [P] [US1] OCR 결과·원본을 bronze 저장소에 배치 ID별로 저장 (`app/storage/bronze/manifest_writer.py`)
- [x] T015 [US1] Silver 변환 모듈에서 TALL/GRANDE/VENTI 별 NutritionProfile 매핑 (`app/pipelines/silver_transform.py`)
- [x] T016 [US1] 차이율 2% 초과 값에 `needs_review` 상태를 부여하는 검증 로직 (`app/pipelines/validators/starbucks_validator.py`)
- [x] T017 [US1] Spring 전달 전 Starbucks 브랜드 품질 리포트 생성 (누락률, 경고 수) (`reports/starbucks_quality_report.md`)

**Checkpoint**: User Story 1 완성 시 Starbucks 데이터만으로도 JSON 전달 및 검증 리포트를 생성 가능

**Parallel Example**:
`T012`(bronze manifest)와 `T013`(OCR 재시도 로직)은 서로 다른 파일로 병렬 진행 가능.

---

## Phase 4: User Story 2 - MegaCoffee 단일 사이즈 파이프라인 (Priority: P2)

**Goal**: MegaCoffee 웹 메뉴에서 MEGA 사이즈로 통일된 파이프라인을 구축하고, 이름 기반 BeverageType 태깅을 완성한다.

**Independent Test**: MegaCoffee 스냅샷을 기반으로 새/삭제 음료를 감지 후 Silver JSON에서 모두 반영되면 완료.

### Implementation for User Story 2

- [x] T018 [US2] MegaCoffee 크롤러가 카테고리 1·1 페이지만 순회하도록 로직 정제 (`app/megacoffee_crawler.py`)
- [x] T019 [P] [US2] MEGA 고정 사이즈·BeverageType 매퍼 구현 (원천 데이터 없을 시 이름 기반 태그) (`app/pipelines/mappers/megacoffee_mapper.py`)
- [x] T020 [US2] Bronze 단계에 MegaCoffee 메타데이터 기록 및 실패 시 배치 중단 정책 적용 (`app/pipelines/bronze_ingest.py`)
- [x] T021 [US2] Silver 변환 시 신규/삭제 음료 diff 로그 생성 (`app/pipelines/silver_transform.py`)
- [x] T022 [P] [US2] 변경 로그를 Spring 전달 큐 전 단계에서 감사 리포트로 남김 (`reports/megacoffee_change_log.md`)
- [x] T023 [US2] MegaCoffee 품질 지표(크롤링 성공률 99%)를 metrics로 노출 (`app/observability/metrics.py`)

**Parallel Example**:
`T019` BeverageType 매퍼와 `T021` Silver diff 로직은 서로 다른 모듈에서 독립 개발 가능.

---

## Phase 5: User Story 3 - 정합성 보증 및 Spring 연동 (Priority: P1)

**Goal**: 두 브랜드 데이터를 병합/검증하여 Spring 서버로 전송 가능한 JSON을 생성하고, Gold tier에 클라이언트용 데이터를 제공한다.

**Independent Test**: 브랜드별 샘플 30건을 병합해 오류 없이 Spring JSON 계약 검증 + Gold 공개 JSON 검증을 통과하면 완료.

### Implementation for User Story 3

- [x] T024 [US3] 브랜드 병합 및 중복 제거 로직 (음료명+사이즈 키) 구현 (`app/pipelines/merger.py`)
- [x] T025 [P] [US3] 사이즈·타입 규칙 위반 자동 차단 및 보고서 생성 (`app/pipelines/validators/integrity_validator.py`)
- [x] T026 [US3] Spring 서버 전송 JSON 빌더에서 스키마 필드(productId, isLiked 포함) 구성 (`app/pipelines/publishers/spring_payload_builder.py`)
- [x] T027 [P] [US3] 전송 실패 재시도(최대 3회) + 경보 트리거 추가 (`app/pipelines/publishers/spring_dispatcher.py`)
- [x] T028 [US3] Gold tier JSON 생성 시 productId/isLiked 제거, 브랜드별 공개 구조로 저장 (`app/pipelines/gold_publish.py`)
- [x] T029 [US3] Gold JSON 제공 FastAPI 엔드포인트/정적 파일 핸들러 추가 (`app/routes/gold_data.py`)
- [x] T030 [US3] 최종 전달 후 5분 이내 응답 모니터링 및 보고 (`app/observability/alerts.py`)

**Parallel Example**:
`T024` 병합 로직과 `T026` Spring JSON 빌더는 인터페이스만 맞추면 동시에 진행 가능.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: 문서화, 최적화, 릴리즈 준비

- [ ] T031 [P] docs/에 bronze→silver→gold 파이프라인 다이어그램과 runbook 작성 (`docs/pipeline_runbook.md`)
- [ ] T032 로그/메트릭 대시보드 샘플 및 경보 정책을 README에 요약 (`README.md`)
- [ ] T033 [P] 성능 튜닝: batch duration 5분 이내 달성 여부 점검 및 병목 리팩터링 (`app/pipelines/perf_tuning.md`)
- [ ] T034 Quickstart 가이드에 배치 실행, 롤백, 벤치마크 절차 기록 (`specs/001-ocr-data-pipeline/quickstart.md`)
- [ ] T035 최종 QA: bronze→silver→gold dry-run 후 결과물을 Spring 스테이징에 제출 (`scripts/batch_runner.py`)

---

## Constitution-Mandated Tasks (Do Not Skip)

- [ ] T036 Readability/maintainability 리포트를 CI에서 강제하고 결과를 위키에 게시 (`.github/workflows/ci.yml`, `docs/QUALITY_GATE.md`)
- [ ] T037 Bronze→Silver→Gold 전환 시 스키마/중복 검증 스크립트 자동 실행 여부를 통합 테스트로 검증 (`tests/pipeline/test_schema_guards.py`)
- [ ] T038 OCR 라벨 데이터셋 갱신 + 벤치마크 스크립트 결과 캡처 (`data/benchmarks/manifest.json`, `scripts/ocr_benchmark.py`)
- [ ] T039 새 라이브러리 도입 시 decision log에 사유/롤백 플랜 기록 (`docs/DEPENDENCY_DECISIONS.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 모든 후속 단계의 기본 환경. 완료 후 Foundational 시작 가능.
- **Foundational (Phase 2)**: 스키마/검증/관측 준비가 끝나야 US1~3 진행 가능.
- **User Story 1 (P1)**: Starbucks 라인 완료가 기본 MVP.
- **User Story 2 (P2)**: Foundational 완료 후 병렬 가능 (US1과 독립)이나, 병합 시 규칙 공유.
- **User Story 3 (P1)**: US1/US2 중 최소 한 브랜드 데이터가 준비되어야 병합 테스트가 의미 있음.
- **Polish**: 모든 스토리 완료 후 실행.

### User Story Dependencies

- **US1**: Foundational 의존, 다른 스토리에 의존 없음.
- **US2**: Foundational 의존, 결과는 US3에 입력.
- **US3**: US1·US2 산출물을 소비하므로 두 스토리 완료 후 본격 진행.

### Within Each User Story

- 모델/매핑 작성 → 검증 로직 → 리포트/전송 순서.
- 브론즈 저장/매니페스트 작성 후에만 Silver 변환 실행.
- 검증 실패 시 배치 중단 정책을 우선 적용.

### Parallel Opportunities

- US1의 manifest 작업(T012)과 OCR 로직(T013) 동시 진행.
- US2의 타입 매퍼(T019)와 diff 로그(T021) 동시 진행.
- US3의 병합(T024)과 스키마 빌더(T026) 동시 진행.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup + Foundational 완료.
2. US1을 완성해 Starbucks 데이터만으로 Spring JSON·품질 리포트를 생성.
3. 문제가 없으면 이 상태로도 제한적 배포 가능.

### Incremental Delivery

1. US1 배포(Starbucks만) → 운영 검증.
2. US2를 병렬 추가하여 MegaCoffee 포함.
3. US3에서 병합/Gold 제공 → 전체 브랜드 지원.

### Parallel Team Strategy

- 개발자 A: US1 크롤러/OCR 개선.
- 개발자 B: US2 매퍼 및 diff 로직.
- 개발자 C: US3 병합 + 배포.
- 공통: 관측/문서/QA를 폴리시 단계에서 합류.

---
