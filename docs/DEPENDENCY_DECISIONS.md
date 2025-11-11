# Dependency Decision Log

| Date | Dependency | Reason | Expected Benefit | Exit / Review Plan |
|------|------------|--------|------------------|--------------------|
| 2025-11-10 | ruff | 헌법 준수용 정적 분석 (C- 유지보수성) | 린트 + maintainability 자동화 | 파이프라인 안정 시 6개월 주기로 재평가 |
| 2025-11-10 | radon | 유지보수성 점수 산출 | C- 이하 코드 차단 | 동일 |
| 2025-11-10 | jsonschema | bronze→silver 스키마 검증 | 데이터 정합성 보증 | 스키마 검증이 다른 시스템으로 대체되면 제거 |
| 2025-11-10 | pydantic | 계층 데이터 모델링 | 모델/검증 일관성 확보 | FastAPI 업데이트와 함께 주기적 재평가 |
