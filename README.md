# Starbucks · MegaCoffee Data Pipeline

- Medallion 구조: Bronze(원본 크롤링/OCR) → Silver(정제 JSON) → Gold(클라이언트 노출)
- 품질 게이트/의존성 변경 사항은 `docs/DEPENDENCY_DECISIONS.md`에서 추적합니다.
