"""OCR helpers with retry + confidence scoring."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Tuple

import cv2
import pytesseract
from PIL import Image

FieldMap = {
    "servingKcal": r"(?:칼로리|열량)\s*\(Kcal\)\s*([0-9,]+)",
    "saturatedFatG": r"포화지방\s*\(g\)\s*([0-9,.]+)",
    "proteinG": r"단백질\s*\(g\)\s*([0-9,.]+)",
    "sodiumMg": r"나트륨\s*\(mg\)\s*([0-9,]+)",
    "sugarG": r"당류\s*\(g\)\s*([0-9,.]+)",
    "caffeineMg": r"카페인\s*\(mg\)\s*([0-9,]+)",
}


def preprocess_image(image_path: str | os.PathLike[str]) -> Image.Image:
    image = cv2.imread(str(image_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary_image = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return Image.fromarray(binary_image)


def extract_nutrition_data(text: str) -> dict:
    nutrition = {}
    for key, pattern in FieldMap.items():
        match = re.search(pattern, text)
        if match:
            value_str = match.group(1).replace(",", "")
            try:
                nutrition[key] = float(value_str)
            except ValueError:
                nutrition[key] = 0
        else:
            nutrition[key] = 0
    return nutrition


def _confidence_from_nutrition(nutrition: dict) -> float:
    total = len(nutrition)
    filled = sum(1 for val in nutrition.values() if val and val > 0)
    return round(filled / total, 2) if total else 0.0


def ocr_drink(image_path: str | os.PathLike[str]) -> str:
    preprocessed_image = preprocess_image(image_path)
    config = r"--oem 3 --psm 6"
    return pytesseract.image_to_string(
        preprocessed_image, lang="kor+eng", config=config
    )


def run_ocr_with_retries(
    image_path: str | os.PathLike[str], retries: int = 3
) -> Tuple[dict, float]:
    best_payload: dict | None = None
    best_confidence = -1.0
    for _ in range(max(1, retries)):
        text = ocr_drink(image_path)
        nutrition = extract_nutrition_data(text)
        confidence = _confidence_from_nutrition(nutrition)
        if confidence > best_confidence:
            best_payload = nutrition
            best_confidence = confidence
    return best_payload or {}, max(best_confidence, 0.0)


def collect_ocr_dataset(
    image_dir: str | os.PathLike[str] = "./image", retries: int = 3
) -> Dict[tuple[str, str], dict]:
    directory = Path(image_dir)
    if not directory.exists():
        return {}
    dataset: Dict[tuple[str, str], dict] = {}
    for path in directory.iterdir():
        if not path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            continue
        filename_no_ext = path.stem
        name_parts = filename_no_ext.rsplit(" ", 1)
        if len(name_parts) != 2:
            continue
        beverage_name, size = name_parts
        nutrition, confidence = run_ocr_with_retries(path, retries=retries)
        dataset[(beverage_name.strip().upper(), size.strip().upper())] = {
            "nutrition": nutrition,
            "confidence": confidence,
            "source": str(path),
        }
    return dataset


def get_ocr_data() -> list[dict]:
    dataset = collect_ocr_dataset()
    return [
        {
            "name": name,
            "size": size,
            "beverageNutrition": payload["nutrition"],
            "confidence": payload["confidence"],
        }
        for (name, size), payload in dataset.items()
    ]
