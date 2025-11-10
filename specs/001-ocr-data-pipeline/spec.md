# Feature Specification: Starbucks · MegaCoffee 데이터 정합성 파이프라인

**Feature Branch**: `001-ocr-data-pipeline`  
**Created**: 2025-11-10  
**Status**: Draft  
**Input**: User description: "해당 서버는 현재 음료 목록을 바탕으로 혈당을 관리할 수 있는 서비스인 ‘아맞당!’을 위한 데이터 파이프라인을 제공하는 서버인 FAST API 서버입니다. 가장 핵심은 각 음료의 영양성분표를 저장할 수 있는 형태로 가공하여 아맞당의 운영서버인 Spring 서버에 JSON형식으로 제공하는 것입니다. 현재 구조에서 가장문제가 되는 부분은 데이터 정합성입니다. 그렇기에 OCR 로직은 성능이 좋아야하며, Crawling또한 문제가 없어야합니다. 현재 가장 크게 제공하는 음료 브랜드는 두 가지로 Starbucks와 MegaCoffee로 데이터 수집방식은 브랜드별로 차이가 있습니다. - Starbucks는 공식 API가 존재하지 않기 때문에 데이터 파이프라인을 위해서 공식홈페이지(https://www.starbucks.co.kr/menu/drink_list.do) Crawling과 더불어 공식 앱의 영양성분표를 캡처한 PNG 파일을 기반으로 OCR을 제공합니다. - SIze는 TALL,GRANDE,VENTI가 존재합니다. - SIZE 중 Other는 존재하지 않습니다. - BeverageType은 제공되는 데이터를 사용합니다. - MegaCoffee의 경우 공식홈페이지(https://www.mega-mgccoffee.com/menu/?menu_category1=1&menu_category2=1)에서 제공하는 음료에 한하여서만 Crawling을 시도합니다. - MegaCoffee의 Size는 Mega로 통일합니다. - BeverageType은 제공되는게 있다면 사용하고 그렇지않다면 이름에 기반하여 BeverageType Tag를 붙입니다."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Starbucks 영양정보 수집·검증 (Priority: P1)

Starbucks 음료 목록을 정기적으로 수집하고 앱에서 캡처한 PNG를 OCR에 통과시켜 영양성분 JSON을 생성한다.

**Why this priority**: 전체 사용자 중 Starbucks 이용 비중이 가장 높고, 기존 오류 대부분이 이 경로에서 발생했기 때문이다.

**Independent Test**: 샘플 캡처 50건과 웹 크롤링 결과를 이용해 파이프라인을 단독 실행하고, 영양 성분 누락·중복률을 측정한다.

**Acceptance Scenarios**:

1. **Given** 최신 Starbucks 메뉴 페이지 URL과 캡처 PNG가 준비된 상태, **When** 파이프라인이 크롤링과 OCR 단계를 모두 마치면, **Then** TALL/GRANDE/VENTI 사이즈별 Nutrition JSON이 생성되고 필수 영양 필드(칼로리, 당류 등)가 100% 채워진다.
2. **Given** OCR 결과와 공식 앱 표 값이 상이할 때, **When** 검증 단계가 실행되면, **Then** 차이율 2% 초과 항목은 "needs_review" 상태로 마킹되어 운영자에게 전달된다.

---

### User Story 2 - MegaCoffee 단일 사이즈 데이터 파이프라인 (Priority: P2)

MegaCoffee 웹 페이지에서 공식 제공 음료만 수집하고 사이즈를 MEGA로 통일해 표준 JSON으로 만든다.

**Why this priority**: MegaCoffee 고객 비중은 낮지만 신규 음료가 자주 추가되어 누락 위험이 크다.

**Independent Test**: MegaCoffee 카테고리 1·1 페이지를 기반으로 주간 스냅샷을 생성하고, 기존 데이터와 비교하여 추가/삭제/변경 건을 검증한다.

**Acceptance Scenarios**:

1. **Given** MegaCoffee 메뉴 페이지가 정상 응답할 때, **When** 크롤러가 실행되면, **Then** 페이지 내 모든 음료가 MEGA 사이즈로 저장되고 BeverageType은 제공 데이터 또는 이름 기반 태그로 채워진다.
2. **Given** 새 음료가 추가된 경우, **When** 파이프라인이 주간 동기화를 돌면, **Then** Spring 서버로 전송되는 JSON에 신규 음료가 포함되고 변경 로그가 생성된다.

---

### User Story 3 - 정합성 보증 및 Spring 서버 연동 (Priority: P1)

두 브랜드 데이터를 병합하기 전에 무결성 검증, 중복 제거, 사이즈/타입 규칙 확인을 수행한 뒤 Spring 운영 서버에 배포 가능한 JSON을 제공한다.

**Why this priority**: 아맞당 운영서버에 잘못된 JSON이 전달되면 혈당 관리 로직 전체가 흔들리기 때문이다.

**Independent Test**: 브랜드별 샘플 30건으로 병합·검증 단계를 돌려 경고 없이 통과하는지 확인하고, 최종 JSON이 계약된 스키마와 일치하는지 검증한다.

**Acceptance Scenarios**:

1. **Given** 브랜드별 원천 데이터가 수집된 상태, **When** 정합성 검증이 실행되면, **Then** 사이즈 규칙 위반(예: Starbucks Other)이나 음료명 중복은 자동 차단되고 보고서에 기록된다.
2. **Given** 최종 JSON이 생성된 상태, **When** Spring 서버 전달 큐에 배포하면, **Then** API 수신 측에서 100% 성공 응답을 기록하고 전달 시간은 5분 이내다.

---

### Edge Cases

- Starbucks 웹 구조나 DOM 클래스 변경으로 특정 음료가 누락되는 경우
- 앱 캡처 PNG 해상도가 낮아 OCR이 일부 숫자를 잘못 인식하는 경우
- 동일 음료명이 계절 한정판으로 재등장하여 중복 레코드가 생기는 경우
- MegaCoffee 페이지 장애로 응답이 빈 배열이 되는 경우 (빈 동기화 금지)
- BeverageType 정보가 비어 있어 이름 기반 태깅 로직이 다의어를 잘못 분류하는 경우

## Data Integrity & OCR Benchmarks *(constitution-mandated)*

- OCR 벤치마크 데이터셋: Starbucks 앱 캡처 500장, MegaCoffee 캡처 200장(분기별 갱신). 목표 정확도는 문자 기준 98%, 단어 기준 95% 이상이며, 실패 시 즉시 롤백한다.
- 벤치마킹 워크플로우: 매주 정기 테스트를 예약해 샘플 50장을 무작위 선택, baseline 대비 오차율을 기록하고 0.5% 초과 시 경보·배포 중단.
- 데이터 파이프라인 검증: 각 단계마다 스키마 검증, 중복 감지, 체크섬 비교를 실행하고 미일치 건은 재처리 큐로 격리한다.
- 신규 라이브러리는 OCR 정확도 향상이나 파이프라인 안정성 입증 자료(전/후 벤치마크)를 첨부한 경우에만 도입하고, 불필요 의존성은 금지한다.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 시스템은 Starbucks 메뉴 페이지 전체를 하루 1회 이상 수집하고 HTTP 오류 또는 DOM 구조 변화 시 경보를 남겨야 한다.
- **FR-002**: OCR 단계는 PNG당 3회 이상 다중 시도를 통해 98% 문자 정확도를 만족하고, 실패 시 원본/결과 쌍을 재검토 큐에 저장해야 한다.
- **FR-003**: 모든 영양 필드는 TALL/GRANDE/VENTI(Starbucks) 또는 MEGA(MegaCoffee) 사이즈 구조를 강제하며, 규칙 위반 레코드는 최종 JSON에 포함되지 않아야 한다.
- **FR-004**: BeverageType은 원천 데이터가 제공될 경우 그대로 사용하고, 없을 시 음료명 키워드를 규칙 기반으로 매핑하여 빈 값이 남지 않도록 해야 한다.
- **FR-005**: 브랜드별 JSON을 병합하기 전에 중복 식별자, 음료명, 사이즈 조합을 비교해 충돌을 제거하고, 제거 사유를 감사 로그로 남겨야 한다.
- **FR-006**: 최종 JSON 패키지는 Spring 운영 서버가 요구하는 스키마(브랜드, 음료, 사이즈, 영양 리스트, 태그, 갱신일자)를 충족하며, 전송 실패 시 최대 3회까지 재시도 후 운영자에게 통보해야 한다.
- **FR-007**: 전 파이프라인 실행 로그는 배치별로 저장되어야 하며, 각 배치에는 소스 해시, OCR 버전, 의존 라이브러리 목록이 포함되어야 한다.

### Key Entities *(include if feature involves data)*

- **BeverageRecord**: 브랜드, 음료명, 사이즈, BeverageType, 원천 URL/이미지 메타데이터를 보유하는 기본 단위.
- **NutritionProfile**: 칼로리, 당류, 단백질 등 영양 필드와 측정 단위를 담는 구조체. OCR 신뢰도와 검증 상태를 포함한다.
- **SourceArtifact**: 웹 HTML 스냅샷이나 앱 PNG 파일을 나타내며 체크섬, 수집 일시, 비고를 저장한다.
- **DeliveryPayload**: Spring 서버에 전달되는 최종 JSON 패키지로, 브랜드별 음료 배열과 데이터 품질 요약(누락 0건, 경고 건수 등)을 포함한다.

## Assumptions

- Starbucks 앱 스크린샷은 매주 최신 버전으로 확보할 수 있으며, 개인정보가 포함되지 않는다.
- MegaCoffee는 공지 없이 URL 구조를 크게 바꾸지 않고, 페이지는 인증 없이 접근 가능하다.
- Spring 운영 서버는 JSON 스키마 변경 시 최소 1주일 전에 사전 공지를 제공한다.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 월간 배치에서 필수 영양 필드 누락률이 0.5% 이하, 중복 레코드가 0건임을 운영 보고서로 확인한다.
- **SC-002**: OCR 정확도(문자 기준) 98% 이상, MegaCoffee 웹 크롤링 성공률 99% 이상을 유지한다.
- **SC-003**: 신규/변경 음료가 발견된 후 24시간 이내에 Spring 서버 JSON에 반영된다.
- **SC-004**: Spring 서버 전달 후 5분 이내 확인 응답을 100% 수신하며, 실패 재시도는 월 1회 이하로 유지한다.
