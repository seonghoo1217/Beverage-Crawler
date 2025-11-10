import pytesseract
from PIL import Image
import os
import re
import cv2
import numpy as np

def preprocess_image(image_path):
    """이미지 전처리 함수"""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 가우시안 블러로 노이즈 제거
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu's Binarization을 사용한 이진화
    _, binary_image = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # PIL 이미지로 변환
    return Image.fromarray(binary_image)

def extract_nutrition_data(text):
    """OCR 텍스트에서 영양 정보 추출"""
    nutrition = {}
    patterns = {
        "servingKcal": r"(?:칼로리|열량)\s*\(Kcal\)\s*([0-9,]+)",
        "saturatedFatG": r"포화지방\s*\(g\)\s*([0-9,.]+)",
        "proteinG": r"단백질\s*\(g\)\s*([0-9,.]+)",
        "sodiumMg": r"나트륨\s*\(mg\)\s*([0-9,]+)",
        "sugarG": r"당류\s*\(g\)\s*([0-9,.]+)",
        "caffeineMg": r"카페인\s*\(mg\)\s*([0-9,]+)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                nutrition[key] = float(value_str)
            except ValueError:
                nutrition[key] = 0
        else:
            nutrition[key] = 0
            
    return nutrition

def get_ocr_data():
    """이미지에서 OCR 데이터를 추출하는 메인 함수"""
    image_dir = './image'
    ocr_results = []

    if not os.path.exists(image_dir):
        return []

    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filename_no_ext = os.path.splitext(filename)[0]
            name_parts = filename_no_ext.rsplit(' ', 1)

            if len(name_parts) != 2:
                continue

            beverage_name, size = name_parts
            image_path = os.path.join(image_dir, filename)

            # 이미지 전처리
            preprocessed_image = preprocess_image(image_path)

            # OCR 실행 (psm 모드 원복)
            config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(preprocessed_image, lang='kor+eng', config=config)
            
            # 영양 정보 추출
            nutrition = extract_nutrition_data(text)

            ocr_results.append({
                "name": beverage_name.strip(),
                "size": size.strip(),
                "beverageNutrition": nutrition
            })
    
    return ocr_results

if __name__ == '__main__':
    # 테스트용
    results = get_ocr_data()
    import json
    print(json.dumps(results, indent=4, ensure_ascii=False))
