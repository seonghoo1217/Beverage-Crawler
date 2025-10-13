from app.starbucks_crawler import get_crawled_data
from app.megacoffee_crawler import get_megacoffee_data
from app.ocr import get_ocr_data
from app.utils import normalize_name

VALID_SIZES = {"SHORT", "TALL", "GRANDE", "VENTI", "TRENTA"}

def _get_starbucks_beverages():
    """Fetches Starbucks beverages and merges them with OCR data."""
    crawled_data = get_crawled_data()
    ocr_data = get_ocr_data()

    crawled_data_map = {normalize_name(item["name"]): item for item in crawled_data}

    for ocr_item in ocr_data:
        ocr_name = normalize_name(ocr_item.get("name"))
        if ocr_name in crawled_data_map:
            beverage_item = crawled_data_map[ocr_name]
            size = ocr_item.get("size", "").strip().upper()
            nutrition = ocr_item.get("beverageNutrition")

            if size in VALID_SIZES and nutrition and size != "TALL":
                if "beverageNutritions" not in beverage_item:
                    beverage_item["beverageNutritions"] = {}
                beverage_item["beverageNutritions"][size] = nutrition
    
    return list(crawled_data_map.values())

def get_all_beverages(brand: str = None):
    """
    Fetches beverage data for the specified brand or all brands.

    Args:
        brand (str, optional): The brand to fetch data for ('starbucks' or 'megacoffee'). 
                               If None, fetches data for all brands.

    Returns:
        A list of beverage data.
    """
    brand = brand.lower() if brand else None
    all_data = []

    if brand == 'starbucks' or brand is None:
        all_data.extend(_get_starbucks_beverages())
    
    if brand == 'megacoffee' or brand is None:
        all_data.extend(get_megacoffee_data())

    return all_data

if __name__ == "__main__":
    import json
    # Test fetching all brands
    all_brands_data = get_all_beverages()
    print(f"Total beverages (all brands): {len(all_brands_data)}")

    # Test fetching only Starbucks
    starbucks_data = get_all_beverages(brand='starbucks')
    print(f"Total beverages (Starbucks): {len(starbucks_data)}")

    # Test fetching only Mega Coffee
    megacoffee_data = get_all_beverages(brand='megacoffee')
    print(f"Total beverages (Mega Coffee): {len(megacoffee_data)}")
    # print(json.dumps(megacoffee_data, indent=4, ensure_ascii=False))