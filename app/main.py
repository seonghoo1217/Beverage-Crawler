from fastapi import FastAPI, Query
from app.merge import get_all_beverages
from app.pipelines import run_medallion_batch
from app.routes import gold_router
from app.routes.gold_data import read_latest_gold_payload
from app.routes.legacy_formatter import gold_to_legacy
from typing import Optional

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Multi-Brand Beverage API",
    description="스타벅스, 메가커피 등 여러 브랜드의 음료 정보를 제공하는 API입니다.",
    version="2.0.0",
)

app.include_router(gold_router)

@app.get("/", tags=["Root"], summary="API 헬스 체크")
def health_check():
    """
    API 서버가 정상적으로 실행 중인지 확인합니다.
    """
    return {"status": "ok", "message": "API is running normally."}


@app.get("/api/v1/beverages", tags=["Beverages"], summary="모든 음료 정보 조회")
def get_beverages_endpoint(brand: Optional[str] = Query(None, description="조회할 브랜드를 지정합니다 (starbucks, megacoffee). 지정하지 않으면 모든 브랜드의 데이터를 반환합니다.")):
    """
    웹사이트 크롤링 데이터와 이미지 OCR 데이터를 병합하여
    지정된 브랜드 또는 모든 브랜드의 음료 상세 정보를 반환합니다.
    """
    payload = read_latest_gold_payload()
    if payload:
        all_data = gold_to_legacy(payload, brand_filter=brand)
    else:
        all_data = get_all_beverages(brand=brand)
    return {"count": len(all_data), "data": all_data}


@app.post("/api/v1/pipeline/run", tags=["Pipeline"], summary="Medallion 파이프라인 수동 실행")
def trigger_pipeline(manual: bool = True):
    """
    Bronze→Silver→Gold 파이프라인을 수동으로 트리거합니다.
    현재는 배치 식별자를 기록만 하며, 후속 구현에서 실제 파이프라인을 호출합니다.
    """
    result = run_medallion_batch(triggered_by="manual" if manual else "system")
    return {"batchId": result.batch_id, "status": result.status, "details": result.details}
