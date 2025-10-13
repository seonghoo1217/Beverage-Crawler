import requests
import json
from app.utils import get_beverage_temperature

def clean_nutrition_value(value):
    """영양성분 값이 .1처럼 1 미만일 경우 0으로 처리합니다."""
    if not value:
        return value
    try:
        # 문자열을 float으로 변환 시도
        float_value = float(value)
        # 1 미만인 경우 "0"으로 반환
        if abs(float_value) < 1:
            return "0"
    except (ValueError, TypeError):
        # 변환 실패 시 원래 값 반환
        return value
    # 그 외의 경우 원래 값 반환
    return value

def get_crawled_data():
    # JS 파일 주소 목록 (카테고리별)
    urls = {
        "W0000003": "ESPRESSO",
        "W0000171": "COLD_BREW",
        "W0000060": "COLD_BREW",
        "W0000004": "FRAPPUCCINO",
        "W0000005": "BLENDED",
        "W0000075": "TEA",
        "W0000422": "REFRESHER",      # ANY -> REFRESHER
        "W0000061": "FIZZIO",          # ANY -> FIZZIO
        "W0000053": "OTHERS",         # ANY -> OTHERS
        "W0000062": "JUICE_YOGURT",   # ANY -> JUICE_YOGURT
    }

    # 전체 결과 저장 리스트
    result = []

    # 크롤링 시작
    for code, beverage_type in urls.items():
        url = f"https://www.starbucks.co.kr/upload/json/menu/{code}.js"
        res = requests.get(url)
        text = res.text.replace("\ufeff", "")  # BOM 제거

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"JSON 파싱 실패: {url}")
            continue

        for item in data.get("list", []):
            name = item.get("product_NM")
            image_path = f"https://www.starbucks.co.kr{item.get('file_PATH', '')}"

            # Tall 사이즈 정보를 기본으로 입력 (값 클리닝 로직 추가)
            tall_nutrition = {
                "servingKcal": clean_nutrition_value(item.get("kcal")),
                "saturatedFatG": clean_nutrition_value(item.get("sat_FAT")),
                "proteinG": clean_nutrition_value(item.get("protein")),
                "sodiumMg": clean_nutrition_value(item.get("sodium")),
                "sugarG": clean_nutrition_value(item.get("sugars")),
                "caffeineMg": clean_nutrition_value(item.get("caffeine"))
            }

            result.append({
                "brand": "STARBUCKS",
                "name": name,
                "image": image_path,
                "beverageType": beverage_type,
                "beverageTemperature": get_beverage_temperature(name, beverage_type),
                "beverageNutritions": {
                    "TALL": tall_nutrition
                }
            })

    return result
