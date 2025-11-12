# Implementation Plan: Starbucks · MegaCoffee 데이터 정합성 파이프라인

**Branch**: `001-ocr-data-pipeline` | **Date**: 2025-11-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ocr-data-pipeline/spec.md`

**Note**: This plan reflects the medallion (Bronze → Silver → Gold) data pipeline architecture required to stabilize crawling + OCR accuracy before delivering JSON to the Spring 운영 서버.

## Summary

우선 Starbucks·MegaCoffee 라인에서 수집되는 모든 크롤링·OCR 원천 데이터를 Bronze 티어에 원본 그대로 적재한다. Bronze 데이터를 표준화·정제하여 Spring 서버에 전달 가능한 스키마(JSON)를 Silver에 저장한 뒤, Gold 티어에서는 productId/isLiked를 제외한 음료 정보를 브랜드별로 집계하여 외부 클라이언트가 직접 소비할 수 있도록 제공한다. 각 티어는 불변 스냅샷, 검증된 중간 산출물, 최종 제공용 데이터로 명확히 분리하며, 파이프라인의 핵심 목표는 1) 데이터 정합성(무결성, 중복 제거, 사이즈 규칙), 2) OCR 정확도, 3) 빠른 오류 탐지를 통한 릴리즈 안전성이다.

## Technical Context

**Language/Version**: Python 3.10 (FastAPI service + 배치 스크립트)  
**Primary Dependencies**: FastAPI, httpx/requests, BeautifulSoup/Playwright(크롤링), pytesseract + OpenCV(OCR), pydantic/SQLModel(스키마), boto3/local filesystem 스토리지  
**Storage**: Bronze/Silver/Gold는 로컬 파일 시스템(S3 호환 버킷으로 이관 가능)과 PostgreSQL/SQLite 메타데이터 테이블을 조합 (Batch 메타 + JSON 아카이브)  
**Testing**: pytest + golden-data fixtures, jsonschema validation, 베이스라인 OCR 벤치마크 스크립트  
**Target Platform**: Linux 컨테이너 (Dockerfile 존재), FastAPI 배치 엔드포인트  
**Project Type**: Backend / 데이터 파이프라인 (단일 리포 내부에 app/, crawlers/ 폴더 존재)  
**Performance Goals**: 하루 1회 이상 전체 배치, 브랜드당 5분 내 처리, OCR 정확도 98%+, MegaCoffee 크롤링 성공률 99%  
**Constraints**: Inline 주석 최소화, 의존성 증가는 OCR 정확도 향상이나 파이프라인 안정성 증거가 있을 때만 허용, 브랜드별 사이즈 규칙 강제  
**Scale/Scope**: 브랜드 2곳, 음료 수백 건, 하루 1~2회 동기화, 향후 브랜드 확장 대비 구조화 필요

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Self-Describing Code (C- Floor)** — Batch/ETL 모듈은 기능별(ingest, transform, validate, publish)로 분리하고, pydantic 모델 + 타입힌트로 가독성을 확보한다. `ruff` + `radon`을 CI에 추가해 유지보수 점수 C- 미만 시 실패하도록 구성한다.
2. **Zero-Fault Data Pipeline** — Bronze→Silver→Gold 전 단계에서 jsonschema, duplicate detector, checksum 검증을 실행한다. 실패 시 배치를 중단하고 이전 성공 데이터를 유지한다.
3. **High-Fidelity OCR Backbone** — 브랜딩별 캡처 세트를 bronze에 저장, silver에서 표준화 전 OCR 품질 리포트를 생성한다. 주간 벤치마크 스크립트와 rollback 스위치를 준비한다.
4. **Instrumented Integrity** — 각 티어 저장 시 structured logging (batch_id, source_hash, ocr_model_version)을 남기고 Prometheus/OTLP friendly 메트릭을 출력한다. 경보 기준: OCR 정확도 <98%, 크롤러 HTTP 실패율 >1%, 스키마 위반.
5. **Lean Dependency Discipline** — 신규 라이브러리 도입 시 "OCR uplift" 또는 "pipeline stability" 증빙을 decision log에 남긴다. 기존 FastAPI/requests/pytesseract 조합 우선 사용.

## Project Structure

### Documentation (this feature)

```
specs/001-ocr-data-pipeline/
├── plan.md              # This file
├── spec.md              # 요구사항 및 성공기준
├── checklists/
│   └── requirements.md  # 스펙 품질 체크
├── research/            # (Phase 0 산출물 예정)
├── data-model.md        # (Phase 1 데이터 모델 상세 예정)
├── quickstart.md        # (Phase 1 운영 가이드 예정)
├── contracts/           # Spring JSON 스키마/예제 예정
└── tasks.md             # (Phase 2 작업 세분화 예정)
```

### Source Code (repository root)

```
app/
├── main.py              # FastAPI 진입점
├── ocr.py               # OCR 유틸
├── megacoffee_crawler.py
├── starbucks_crawler.py (예정)
├── pipelines/
│   ├── bronze_ingest.py
│   ├── silver_transform.py
│   └── gold_publish.py
└── storage/
    ├── bronze/
    ├── silver/
    └── gold/

crawlers/
├── utils/
└── brand_specific/

scripts/
└── batch_runner.py
```

**Structure Decision**: 단일 FastAPI/배치 프로젝트 구조를 유지하되 `pipelines/` 디렉터리에 티어별 모듈을 분리하고, `storage/bronze|silver|gold` 경로를 명시적으로 관리한다. 메타데이터/로그는 DB 또는 `/app/data/meta` 경로에 기록한다.

## Phase Plan

### Phase 0 – Research & Alignment
- 정합성 요구사항 확인: Spring JSON 스키마, Gold tier 예제, productId/isLiked 제거 요건 재확인.
- 기존 크롤러/ocr 모듈 성능 측정, 현재 오류 유형 수집.
- 저장소/배치 스케줄링(크론, Celery 등) 옵션 평가.
- 산출물: research.md, 데이터 샘플, baseline metric 리포트.

### Phase 1 – Bronze Tier (Raw Ingest)
- UPDATED Starbucks 크롤러: DOM 변화 감지, size 규칙(TALL/GRANDE/VENTI) 메타 포함.
- MegaCoffee 크롤러: 카테고리 1·1 한정 수집, MEGA 사이즈 강제.
- OCR 러너: PNG → 텍스트 → JSON raw 필드, confidence score + source metadata.
- 저장 전략: `storage/bronze/{brand}/{batch_id}/` 폴더 + batch manifest.
- 검증: 스키마 기초 검증, checksum 기록, 실패 시 브랜드별 배치 중단.

### Phase 2 – Silver Tier (Validated Transform)
- 표준화 로직: Bronze JSON을 정규화하여 NutritionProfile, BeverageRecord 구조로 매핑.
- Dedup & conflict resolution: product name + size 키 기준 중복 제거, needs_review 플래그 유지.
- Quality gates: schema validator + rule engine (사이즈/타입 규칙, 음료명 충돌) 구성.
- Spring 서버용 JSON builder: brand → beverages → nutrition, productId·isLiked 포함 버전.
- 산출물: silver datasets, validation 리포트, alert hook.

### Phase 3 – Gold Tier (Client-Facing, ProductId/isLiked 제외)
- Silver 데이터를 기반으로 브랜드별 공개용 JSON 생성. productId/isLiked 제거, 나머지 필드는 스펙 예제에 맞춤.
- Caching/serving 전략: FastAPI endpoint 또는 정적 파일로 제공, 브랜드 파라미터 지원.
- Contract tests: gold JSON이 클라이언트 계약(필드/자료형)과 일치하는지 검증.

### Phase 4 – Observability & Release Readiness
- Structured logging + metrics (batch_duration, crawl_success_rate, ocr_accuracy) 노출.
- Alerting: HTTP 실패율, OCR 정확도 저하, 스키마 위반 시 Slack/Webhook.
- Dry-run 파이프라인과 rollback 스크립트 문서화.
- Handover: quickstart.md, runbooks, release checklist 업데이트.

## Risk & Mitigation
- **DOM 변화/차단**: Playwright + fallback selectors, 실패 시 브랜드 배치 차단 정책 적용.
- **OCR 정확도 저하**: Benchmarks, model/version pinning, silver 단계에서 manual review queue 유지.
- **데이터 중복/누락**: Dedup rules + hash-based identity, 누락률 리포트 자동화.
- **의존성 증가**: 새 라이브러리는 decision log + 벤치마크 첨부, 필요 시 제거 플랜 명시.

## Open Questions / Assumptions to Monitor
- Spring 서버 JSON Schema 변경 주기 (assumed: 최소 1주 사전 공지).
- Gold tier 배포 방식 (정적 파일 vs FastAPI endpoint) — 기본은 FastAPI endpoint + CDN 캐시.
- Storage backend (로컬/S3) — 현재는 로컬, 운영 전환 시 S3 연계 계획 필요.

## Resource / Schedule Snapshot
- Phase 0: 1일
- Phase 1: 3일 (크롤러 + OCR 개선)
- Phase 2: 3일 (정제/검증 로직)
- Phase 3: 2일 (Gold API + 계약 테스트)
- Phase 4: 1일 (관측/문서)
- 총 10일 (버퍼 제외)

## Constitution-Mandated Follow-ups
- Readability tooling (`ruff`, `radon`, type hints) 구성 후 CI에 추가.
- Schema + duplication 검증 스크립트 문서화하고 bronze→silver 전환 시 자동 실행.
- OCR benchmark 스크립트(weekly) + dataset 관리 정책 수립.
- Dependency justification log 템플릿을 repo/docs에 추가.
